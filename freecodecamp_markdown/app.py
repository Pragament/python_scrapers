import os
import re
import requests
import yaml
from pathlib import Path


OUTPUT_FILE = "freecodecamp_full_stack_lectures.md"
Path(OUTPUT_FILE).unlink(missing_ok=True)

def fetch_json(url):
    """Fetch JSON data from URL"""
    try:
        print(f"Fetching JSON: {url}")
        res = requests.get(url)
        if res.status_code == 404:
            print(f"404 Not Found: {url}")
            return None
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching JSON from {url}: {e}")
        return None

def fetch_text(url):
    """Fetch text data from URL"""
    try:
        print(f"Fetching text: {url}")
        res = requests.get(url)
        if res.status_code == 404:
            print(f"404 Not Found: {url}")
            return None
        res.raise_for_status()
        return res.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching text from {url}: {e}")
        return None

def extract_content_section(md_text, section_name):
    """Extract a specific section from markdown (transcript, description, etc.)"""
    
    pattern = rf"# --{section_name}--\n(.*?)(?=\n# --|$)"
    match = re.search(pattern, md_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def write_lecture_section(title, content, content_type, f):
    """Write a lecture section to the markdown file"""
    f.write(f"\n## {title}\n\n")
    if content:
        f.write(f"### {content_type.title()}\n\n")
        f.write(f"{content}\n\n")
    else:
        f.write(f"*No {content_type} available*\n\n")

def get_common_lecture_ids():
    """Return common lecture file IDs to try when meta.json is not available"""
    # These are some common patterns we might find
    return [
        "670803abcb3e980233da4768",  
        "6708382cf088b216580a9ff1", 
        "67083868d5fdcb17bf8c14bd",
        "670838b10ee87a18e5faff62",
        "67083952f800051a8a21fcfd",
        "6708396caa00e11b597b3365"
    ]

def try_direct_approach(block_name, f):
    """Try to fetch lecture files directly when meta.json is not available"""
    print(f"    Trying direct approach for block: {block_name}")
    
    # Try some common lecture IDs
    lecture_ids = get_common_lecture_ids()
    lectures_found = 0
    
    for lecture_id in lecture_ids:
        lecture_url = f"https://raw.githubusercontent.com/freeCodeCamp/freeCodeCamp/refs/heads/main/curriculum/challenges/english/25-front-end-development/{block_name}/{lecture_id}.md"
        md_text = fetch_text(lecture_url)
        
        if md_text:
            print(f"      Found lecture file: {lecture_id}")
            
            
            title_match = re.search(r"title:\s*(.+)", md_text)
            title = title_match.group(1).strip() if title_match else f"Lecture {lecture_id}"
            
            
            content = extract_content_section(md_text, "transcript")
            content_type = "transcript"
            
            if not content:
                content = extract_content_section(md_text, "description")
                content_type = "description"
            
            if content:
                write_lecture_section(title, content, content_type, f)
                lectures_found += 1
        else:
            break  # Stop trying if we hit a 404
    
    return lectures_found

def main():
    """Main function to scrape FreeCodeCamp curriculum"""
    print("Starting FreeCodeCamp Full Stack curriculum scraper...")
    
    # Fetch chapters list  API
    chapters_url = "https://raw.githubusercontent.com/freeCodeCamp/freeCodeCamp/refs/heads/main/curriculum/superblock-structure/full-stack.json"
    superblock = fetch_json(chapters_url)
    
    if not superblock:
        print("Failed to fetch chapters list")
        return
    
    print(f"Found {len(superblock.get('chapters', []))} chapters")
    
    total_lectures = 0
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# FreeCodeCamp Full Stack Curriculum\n\n")
        f.write("This document contains lecture content from the FreeCodeCamp Full Stack curriculum.\n\n")

        for chapter in superblock.get("chapters", []):
            chapter_name = chapter.get("dashedName", "unknown")
            print(f"\nProcessing chapter: {chapter_name}")
            f.write(f"\n# Chapter: {chapter_name.replace('-', ' ').title()}\n\n")

            for module in chapter.get("modules", []):
                module_name = module.get("dashedName", "unknown")
                print(f"  Processing module: {module_name}")
                f.write(f"\n## Module: {module_name.replace('-', ' ').title()}\n\n")

                for block in module.get("blocks", []):
                    block_name = block.get("dashedName", "unknown")
                    
                    # Skip non-lecture blocks
                    if not block_name.startswith("lecture-"):
                        print(f"    Skipping non-lecture block: {block_name}")
                        continue
                        
                    print(f"    Processing lecture block: {block_name}")
                    
                    
                    meta_url = f"https://raw.githubusercontent.com/freeCodeCamp/freeCodeCamp/refs/heads/main/curriculum/challenges/_meta/{block_name}/meta.json"
                    meta = fetch_json(meta_url)
                    
                    f.write(f"\n### Lecture Block: {block_name.replace('-', ' ').title()}\n\n")
                    
                    lecture_count = 0
                    
                    if meta and meta.get("challengeOrder"):
                        
                        print(f"    Using meta.json for {block_name}")
                        
                        for challenge in meta["challengeOrder"]:
                            challenge_id = challenge.get("id", "")
                            challenge_title = challenge.get("title", "Untitled")
                            
                            if not challenge_id:
                                continue
                            
                            print(f"      Processing lecture: {challenge_title} ({challenge_id})")
                            
                            lecture_url = f"https://raw.githubusercontent.com/freeCodeCamp/freeCodeCamp/refs/heads/main/curriculum/challenges/english/25-front-end-development/{block_name}/{challenge_id}.md"
                            md_text = fetch_text(lecture_url)
                            
                            if not md_text:
                                print(f"      [!] Skipping {challenge_id} - lecture file not found")
                                continue

                            
                            content = extract_content_section(md_text, "transcript")
                            content_type = "transcript"
                            
                            if not content:
                                content = extract_content_section(md_text, "description")
                                content_type = "description"
                            
                            if content:
                                write_lecture_section(challenge_title, content, content_type, f)
                                lecture_count += 1
                                total_lectures += 1
                            else:
                                print(f"      [!] No content found for {challenge_title}")
                    
                    else:
                       
                        print(f"    Meta.json not available for {block_name}, trying direct approach")
                        direct_lectures = try_direct_approach(block_name, f)
                        lecture_count += direct_lectures
                        total_lectures += direct_lectures
                    
                    if lecture_count > 0:
                        print(f"    Found {lecture_count} lectures in block {block_name}")
                    else:
                        print(f"    [!] No lectures found in block {block_name}")

    print(f"\nScraping completed! Found {total_lectures} total lectures.")
    print(f"Data written to `{OUTPUT_FILE}`")
    
    if total_lectures == 0:
        print("\nNo lectures were found. This might be because:")
        print("1. The meta.json files don't exist for most blocks")
        print("2. The lecture files are in a different location")
        print("3. The URL structure has changed")
        print("\nTry checking the GitHub repository structure manually.")

if __name__ == "__main__":
    main()