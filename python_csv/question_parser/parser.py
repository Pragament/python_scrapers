import argparse
import os
import shutil
from datetime import datetime, timezone
from typing import List, Dict, Optional
import re

import boto3
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None
from bson import ObjectId
from bs4 import BeautifulSoup
from pymongo import MongoClient
import pandas as pd

MONGO_URI = os.environ.get("MONGO_URI")
MONGO_DB = os.environ.get("MONGO_DB")
MONGO_DATABASE_NAME = os.environ.get("MONGO_DATABASE_NAME", "adminjs")

# S3 configuration
AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")


AWS_BUCKET = os.environ.get("AWS_BUCKET", "textbookpdf")
# Support both custom and standard AWS env var names; do not fall back to hardcoded defaults
AWS_ACCESS_KEY = (
    os.environ.get("AWS_ACCESS_KEY")
    or os.environ.get("AWS_ACCESS_KEY_ID")
)
AWS_SECRET_KEY = (
    os.environ.get("AWS_SECRET_KEY")
    or os.environ.get("AWS_SECRET_ACCESS_KEY")
)
AWS_SESSION_TOKEN = os.environ.get("AWS_SESSION_TOKEN") or ""

# Defaults for required fields in target schema
DEFAULT_AUTHOR_USER_ID = os.environ.get("AUTHOR_USER_ID")
DEFAULT_LANGUAGE = os.environ.get("QUESTION_LANGUAGE", "English")
DEFAULT_SUBJECT = os.environ.get("QUESTION_SUBJECT", "Mathematics")
DEFAULT_TOPIC = os.environ.get("QUESTION_TOPIC", "Generic")
DEFAULT_SUBTOPIC = os.environ.get("QUESTION_SUBTOPIC", "Generic")


def build_s3_client(
    region_name: Optional[str] = None,
    access_key_id: Optional[str] = None,
    secret_access_key: Optional[str] = None,
    session_token: Optional[str] = None,
    profile_name: Optional[str] = None,
    validate_credentials: bool = False,
):
    """Create and validate an S3 client using provided args, env, or default chain."""
    resolved_region = region_name or AWS_REGION

    session = None
    if profile_name:
        # Use an explicit profile if provided
        session = boto3.Session(profile_name=profile_name, region_name=resolved_region)
    elif access_key_id and secret_access_key:
        # Use explicit static credentials if provided
        session = boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            aws_session_token=session_token or None,
            region_name=resolved_region,
        )
    elif AWS_ACCESS_KEY and AWS_SECRET_KEY:
        # Fallback to env-provided explicit creds
        session = boto3.Session(
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            aws_session_token=AWS_SESSION_TOKEN or None,
            region_name=resolved_region,
        )
    else:
        # Default provider chain (env, shared config, metadata/IMDS)
        session = boto3.Session(region_name=resolved_region)

    # Optionally validate credentials early to provide a clear error message
    if validate_credentials:
        try:
            sts = session.client("sts")
            sts.get_caller_identity()
        except Exception as e:
            # Keep previous behavior: do not hard-fail; warn and proceed so uploads will warn per-file
            print(
                f"Warning: AWS credential validation failed: {e}. Continuing without validation; uploads may fail with warnings."
            )

    return session.client("s3")


def upload_to_s3(s3_client, local_path: Optional[str], key_prefix: str, skip_s3: bool = False) -> Optional[str]:
    if skip_s3:
        return None
    if not local_path or not os.path.exists(local_path):
        return None
    file_name = os.path.basename(local_path)
    key = f"{key_prefix}/{file_name}"
    # Do not set ACLs; many buckets enforce bucket-owner-only and block ACLs
    try:
        s3_client.upload_file(local_path, AWS_BUCKET, key)
        url = f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
        print(f"Uploaded to {url}")
        return url
    except Exception as e:
        print(f"Warning: Failed to upload {local_path} -> s3://{AWS_BUCKET}/{key}: {e}")
        return None


def resolve_image_local_path(src: str, base_dir: str, extra_roots: List[str]) -> Optional[str]:
    # Normalize and try multiple strategies to find the local image
    src = src.strip()
    if not src:
        return None
    # Skip data URIs
    if src.startswith("data:"):
        return None
    
    # 1) If looks like an absolute Windows path
    if os.path.isabs(src) and os.path.exists(src):
        return src
    
    # 2) Relative to HTML file
    candidate = os.path.join(base_dir, src.strip("./\\"))
    if os.path.exists(candidate):
        return candidate
    
    # 3) By basename (with or without extension) under any extra roots
    filename = os.path.basename(src)
    stem, ext = os.path.splitext(filename)
    
    def norm(name: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", name.lower())
    norm_stem = norm(stem)
    # Always try common extensions in addition to whatever the HTML provided
    COMMON_EXTS = [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg"]
    candidate_exts = []
    if ext:
        candidate_exts.append(ext.lower())
    for ce in COMMON_EXTS:
        if ce not in candidate_exts:
            candidate_exts.append(ce)
    
    for root in extra_roots:
        if not root or not os.path.exists(root):
            continue
        
        # direct name
        by_name = os.path.join(root, filename)
        if os.path.exists(by_name):
            return by_name
        
        # try stem with common extensions
        for e in candidate_exts:
            guess = os.path.join(root, stem + e)
            if os.path.exists(guess):
                return guess
        
        # also try normalized stem with common extensions
        for e in candidate_exts:
            guess_norm = os.path.join(root, norm_stem + e)
            if os.path.exists(guess_norm):
                return guess_norm
        
        # quick scan in root for files starting with stem (sometimes names differ by suffixes)
        try:
            for f in os.listdir(root):
                fstem = os.path.splitext(f)[0]
                if fstem.lower().startswith(stem.lower()) or norm(fstem) == norm_stem:
                    candidate = os.path.join(root, f)
                    return candidate
        except Exception:
            pass
    
    return None


def extract_imgs_and_upload(
    s3_client, base_dir: str, cell, key_prefix: str, image_search_roots: List[str], skip_s3: bool
) -> List[Dict]:
    image_details: List[Dict] = []
    imgs = cell.find_all("img")
    for img in imgs:
        if not img.has_attr("src"):
            continue
        src = img["src"].strip()
        local_img = resolve_image_local_path(src, base_dir, image_search_roots)
        url = upload_to_s3(s3_client, local_img, key_prefix, skip_s3=skip_s3)
        if url:
            image_details.append({"path": url, "width": 0, "height": 0})
    return image_details


def process_cell_images(
    s3_client, base_dir: str, cell, key_prefix: str, image_search_roots: List[str], skip_s3: bool
) -> (str, List[Dict]):
    image_details: List[Dict] = []
    imgs = cell.find_all("img")
    for img in imgs:
        if not img.has_attr("src"):
            continue
        src = img["src"].strip()
        local_img = resolve_image_local_path(src, base_dir, image_search_roots)
        url = upload_to_s3(s3_client, local_img, key_prefix, skip_s3=skip_s3)
        if url:
            image_details.append({"path": url, "width": 0, "height": 0})
            img["src"] = url
    return cell.decode_contents().strip(), image_details


def parse_options_and_images(
    s3_client, base_dir: str, options_cell, image_search_roots: List[str], skip_s3: bool
) -> List[Dict]:
    # Options cell may contain multiple <p> or list items and images
    option_blocks: List[str] = []
    # Heuristics: split by <p> tags; fallback to text
    ps = options_cell.find_all("p")
    if ps:
        option_blocks = [p.decode_contents().strip() for p in ps if p.decode_contents().strip()]
    else:
        # If no <p>, just use the whole cell
        option_blocks = [options_cell.decode_contents().strip()]

    results: List[Dict] = []
    for idx, html_block in enumerate(option_blocks):
        # Temporary soup to find images inside each block
        block_soup = BeautifulSoup(html_block, "lxml")
        html_with_urls, images = process_cell_images(
            s3_client,
            base_dir,
            block_soup,
            key_prefix="question_images/option_images",
            image_search_roots=image_search_roots,
            skip_s3=skip_s3,
        )
        option_doc: Dict = {"optionText": html_with_urls}
        if images:
            # Store all image details for the option
            option_doc["imageDetails"] = images
        results.append(option_doc)

    # Keep only 4 options if more
    return results[:4]


def find_main_table(soup: BeautifulSoup):
    candidate_tables = soup.find_all("table")
    wanted_headers = {"sr no", "tag", "type", "priority", "chapter", "question", "options", "answer", "marks", "active", "approved", "added by"}
    for table in candidate_tables:
        header_cells = table.find_all("th")
        headers_text = {h.get_text(" ", strip=True).lower() for h in header_cells}
        if headers_text and len(wanted_headers.intersection(headers_text)) >= 6:
            return table
    return None


def clean_text(value: str) -> str:
    if not value:
        return ""
    # Remove UI shortcut/tool-tip noise like 'Alt+1', 'Back to my Website', etc.
    value = re.sub(r"\bAlt\+[A-Za-z0-9]+\b", "", value)
    value = value.replace("Back to my Website (My Website)", "")
    value = value.replace("Add new column (Depends on the page)", "")
    value = value.replace("Edit Column (Depends on the page)", "")
    value = value.strip()
    return value


def parse_questions(
    html_file,
    output_img_dir="extracted_images",
    images_root: Optional[str] = None,
    excel_check_path: Optional[str] = None,
    aws_region: Optional[str] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_session_token: Optional[str] = None,
    aws_profile: Optional[str] = None,
    aws_validate: bool = False,
    skip_s3: bool = False,
):
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")

    # Make sure output folder exists
    base_dir = os.path.dirname(os.path.abspath(html_file))
    os.makedirs(output_img_dir, exist_ok=True)

    table = find_main_table(soup) or soup.find("table")
    if not table:
        raise RuntimeError("No table found in HTML")
    rows = table.find_all("tr")
    # Find the real header row (some tables have multiple heading rows)
    expected_headers = [
        "sr num", "que id", "que tag", "question type", "question priority",
        "chapter", "question", "options", "answer", "marks", "active",
        "approved", "added by",
    ]
    header_map: Dict[int, str] = {}
    header_row_index = 0
    for i, r in enumerate(rows[:5]):
        cells = r.find_all(["th", "td"])  # headers sometimes are <td>
        texts = [c.get_text(" ", strip=True).lower() for c in cells]
        if len(set(expected_headers).intersection(texts)) >= 6:
            header_row_index = i
            for idx, text in enumerate(texts):
                header_map[idx] = text
            break
    if not header_map and rows:
        # Default fixed positions if header not detected
        header_map = {i: name for i, name in enumerate(expected_headers)}
        header_row_index = 0

    # Initialize external services
    if not MONGO_URI:
        raise RuntimeError("MONGO_URI environment variable is required")
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DATABASE_NAME]
    generic_col = db["genericquestions"]
    papers_col = db["questionpapers"]
    s3_client = build_s3_client(
        region_name=aws_region,
        access_key_id=aws_access_key_id,
        secret_access_key=aws_secret_access_key,
        session_token=aws_session_token,
        profile_name=aws_profile,
        validate_credentials=aws_validate,
    )

    inserted_ids: List[ObjectId] = []

    # Build additional image search roots
    html_basename = os.path.splitext(os.path.basename(html_file))[0]
    default_images_dir = os.path.join(base_dir, f"{html_basename}_files")
    extra_images_root = images_root or os.environ.get("IMAGES_ROOT")
    # If a specific images_root is provided, search ONLY there (per user request to ignore path prefixes)
    if images_root:
        image_search_roots: List[str] = [images_root]
    else:
        image_search_roots: List[str] = [p for p in [default_images_dir, extra_images_root] if p]

    # Also search any sibling directory starting with the HTML base
    if not images_root:
        for name in os.listdir(base_dir):
            if name.lower().startswith(html_basename.lower()) and os.path.isdir(os.path.join(base_dir, name)):
                path = os.path.join(base_dir, name)
                if path not in image_search_roots:
                    image_search_roots.append(path)

    # Load target schema headers from Excel if present to guide mapping
    excel_headers: Dict[str, str] = {}
    try:
        for name in os.listdir(base_dir):
            if name.lower().endswith(".xlsx"):
                df = pd.read_excel(os.path.join(base_dir, name), nrows=0)
                for col in list(df.columns):
                    excel_headers[col.lower()] = col
                break
    except Exception:
        excel_headers = {}

    for row in rows[header_row_index + 1:]:
        cols = row.find_all("td")
        if not cols:
            continue
        # Map by header names when available; fallback to known positions
        def by_name(name: str, default_index: Optional[int] = None) -> str:
            name_l = name.lower()
            idx = next((i for i, h in header_map.items() if h == name_l), default_index)
            if idx is None or idx >= len(cols):
                return ""
            return clean_text(cols[idx].get_text(" ", strip=True))

        # Finder with aliases/Excel help
        def find_idx_alias(aliases: List[str], fallback: Optional[int]) -> Optional[int]:
            names = [a.lower() for a in aliases if a]
            return next((i for i, h in header_map.items() if h in names), fallback)

        # Aliases per column
        sr_idx = find_idx_alias(["sr num", "sr no", excel_headers.get("sr num"), excel_headers.get("sr no")], 1 if len(cols) > 1 else None)
        que_id_idx = find_idx_alias(["que id", "question id", "id", excel_headers.get("que id"), excel_headers.get("question id")], 0 if len(cols) > 0 else None)
        tag_idx = find_idx_alias(["que tag", "tag", excel_headers.get("que tag"), excel_headers.get("tag")], 2 if len(cols) > 2 else None)
        type_idx = find_idx_alias(["question type", "type", excel_headers.get("question type"), excel_headers.get("type")], 3 if len(cols) > 3 else None)
        priority_idx = find_idx_alias(["question priority", "priority", excel_headers.get("question priority"), excel_headers.get("priority")], 4 if len(cols) > 4 else None)
        chapter_idx = find_idx_alias(["chapter", excel_headers.get("chapter")], 5 if len(cols) > 5 else None)

        que_id = clean_text(cols[que_id_idx].get_text(" ", strip=True)) if que_id_idx is not None and que_id_idx < len(cols) else ""
        sr_num = clean_text(cols[sr_idx].get_text(" ", strip=True)) if sr_idx is not None and sr_idx < len(cols) else ""
        que_tag = clean_text(cols[tag_idx].get_text(" ", strip=True)) if tag_idx is not None and tag_idx < len(cols) else ""
        que_type = clean_text(cols[type_idx].get_text(" ", strip=True)) if type_idx is not None and type_idx < len(cols) else ""
        priority = clean_text(cols[priority_idx].get_text(" ", strip=True)) if priority_idx is not None and priority_idx < len(cols) else ""
        chapter = clean_text(cols[chapter_idx].get_text(" ", strip=True)) if chapter_idx is not None and chapter_idx < len(cols) else ""

        # Extract question HTML and upload any images
        q_idx = next((i for i, h in header_map.items() if h == "question"), None)
        if q_idx is None:
            q_idx = 6 if len(cols) > 6 else None
        if q_idx is None or q_idx >= len(cols):
            continue
        question_cell = cols[q_idx]
        question_html, question_images = process_cell_images(
            s3_client,
            base_dir,
            question_cell,
            key_prefix="question_images",
            image_search_roots=image_search_roots,
            skip_s3=skip_s3,
        )

        def idx_for(key: str, fallback: Optional[int]):
            excel_name = excel_headers.get(key)
            names = [key, excel_name.lower()] if excel_name else [key]
            return next((i for i, h in header_map.items() if h in [n.lower() for n in names]), fallback)

        o_idx = idx_for("options", 7 if len(cols) > 7 else None)
        a_idx = idx_for("answer", 8 if len(cols) > 8 else None)
        m_idx = idx_for("marks", 9 if len(cols) > 9 else None)
        act_idx = idx_for("active", 10 if len(cols) > 10 else None)
        app_idx = idx_for("approved", 11 if len(cols) > 11 else None)
        add_idx = idx_for("added by", 12 if len(cols) > 12 else None)

        options = (
            parse_options_and_images(s3_client, base_dir, cols[o_idx], image_search_roots, skip_s3)
            if o_idx is not None and o_idx < len(cols)
            else []
        )
        answer = clean_text(cols[a_idx].get_text(" ", strip=True)) if a_idx is not None and a_idx < len(cols) else None
        marks = clean_text(cols[m_idx].get_text(" ", strip=True)) if m_idx is not None and m_idx < len(cols) else None
        active = clean_text(cols[act_idx].get_text(" ", strip=True)) if act_idx is not None and act_idx < len(cols) else None
        approved = clean_text(cols[app_idx].get_text(" ", strip=True)) if app_idx is not None and app_idx < len(cols) else None
        added_by = clean_text(cols[add_idx].get_text(" ", strip=True)) if add_idx is not None and add_idx < len(cols) else None

        # Build generic question document (compatible with existing structure)
        now_iso = datetime.now(timezone.utc).isoformat()
        # Build option texts array for the Excel-style "Options" column
        option_texts = [opt.get("optionText") for opt in options] if options else []

        q_doc = {
            "author_user_id": ObjectId(DEFAULT_AUTHOR_USER_ID) if DEFAULT_AUTHOR_USER_ID else ObjectId(),
            "questionType": que_type or "MCQ",
            "questionNumber": int(sr_num) if sr_num.isdigit() else sr_num,
            "archived": False,
            "markedForDeletion": False,
            "questionText": question_html,
            "extraText": "NA",
            "options": options,
            "language": DEFAULT_LANGUAGE,
            "age": os.environ.get("QUESTION_AGE", "IX"),
            "subject": DEFAULT_SUBJECT,
            "topic": DEFAULT_TOPIC,
            "subtopic": DEFAULT_SUBTOPIC,
            "timestamp": datetime.now(timezone.utc),
            "__v": 0,
            "Formula_id": "",
            "Timestamp": now_iso,
            "priority": priority,
            "chapter": chapter,
            "tag": que_tag,
            "answer": answer,
            "marks": marks,
            "active": (active or "").lower() in ("true", "1", "yes"),
            "approved": (approved or "").lower() in ("true", "1", "yes"),
            # Excel-style columns mirrored as separate fields, with None when missing
            "Sr Num": sr_num if sr_num else None,
            "Que ID": que_id if que_id else None,
            "Que Tag": que_tag if que_tag else None,
            "Question Type": que_type if que_type else None,
            "Question Priority": priority if priority else None,
            "Chapter": chapter if chapter else None,
            "Question": question_html if question_html else None,
            "Options": option_texts if option_texts else None,
            "Answer": answer if answer else None,
            "Marks": marks if marks else None,
            "Active": active if active is not None else None,
            "Approved": approved if approved is not None else None,
            "Added By": added_by if added_by else None,
        }

        if question_images:
            # Store all image details for the question under 'imageDetails'
            q_doc["imageDetails"] = question_images
            # Also expose a simple list of S3 URLs under a separate column "Images"
            q_doc["Images"] = [img.get("path") for img in question_images if img.get("path")]

        inserted_id = generic_col.insert_one(q_doc).inserted_id
        inserted_ids.append(inserted_id)

    # Optional cross-check with Excel: compare counts and basic fields
    if excel_check_path and os.path.exists(excel_check_path):
        try:
            import pandas as pd  # local import in case optional
            xdf = pd.read_excel(excel_check_path)
            expected_count = len(xdf.index)
            print(f"Excel check: {expected_count} rows in sheet; inserted {len(inserted_ids)}.")
        except Exception as e:
            print(f"Excel check failed: {e}")

    # Create a questionpaper document linking inserted questions
    if inserted_ids:
        title = os.path.splitext(os.path.basename(html_file))[0]
        papers_col.insert_one({
            "title": title,
            "questions": inserted_ids,
        })

    print(f"Inserted {len(inserted_ids)} questions and created a question paper entry.")

def main():
    parser = argparse.ArgumentParser(description="Parse Question Bank HTML")
    parser.add_argument("html_file", help="Path to the HTML file")
    parser.add_argument("--images", default="extracted_images",
                        help="Folder to copy extracted images (default: extracted_images)")
    parser.add_argument("--images-root", default=None,
                        help="Directory containing referenced images (overrides IMAGES_ROOT)")
    parser.add_argument("--excel", default=None,
                        help="Path to Excel file for cross-check (optional)")
    # Env file support
    parser.add_argument("--env-file", dest="env_file", default=None, help="Path to a .env file to load before running")
    # AWS overrides (optional)
    parser.add_argument("--aws-region", dest="aws_region", default=None, help="AWS region override (default from env or ap-south-1)")
    parser.add_argument("--aws-access-key-id", dest="aws_access_key_id", default=None, help="AWS access key id")
    parser.add_argument("--aws-secret-access-key", dest="aws_secret_access_key", default=None, help="AWS secret access key")
    parser.add_argument("--aws-session-token", dest="aws_session_token", default=None, help="AWS session token (if using temporary credentials)")
    parser.add_argument("--aws-profile", dest="aws_profile", default=None, help="AWS shared credentials/config profile name")
    parser.add_argument("--aws-validate", dest="aws_validate", action="store_true", help="Validate AWS credentials at startup via STS (optional)")
    parser.add_argument("--no-aws-validate", dest="aws_validate", action="store_false", help="Disable AWS credentials validation (default)")
    parser.set_defaults(aws_validate=False)
    parser.add_argument("--skip-s3", dest="skip_s3", action="store_true", help="Skip uploading images to S3; leave image srcs unchanged (for offline runs)")
    args = parser.parse_args()

    # Load .env if requested or if a default .env exists and python-dotenv is available
    if load_dotenv is not None:
        if args.env_file and os.path.exists(args.env_file):
            load_dotenv(args.env_file)
        else:
            default_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
            if os.path.exists(default_env):
                load_dotenv(default_env)

    parse_questions(
        args.html_file,
        args.images,
        images_root=args.images_root,
        excel_check_path=args.excel,
        aws_region=args.aws_region,
        aws_access_key_id=args.aws_access_key_id,
        aws_secret_access_key=args.aws_secret_access_key,
        aws_session_token=args.aws_session_token,
        aws_profile=args.aws_profile,
        aws_validate=args.aws_validate,
        skip_s3=args.skip_s3,
    )

if __name__ == "__main__":
    main()

