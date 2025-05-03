import requests
import json
import xml.etree.ElementTree as ET
import os
import re
import ollama
from time import sleep
from urllib.parse import quote
from tenacity import retry, stop_after_attempt, wait_exponential

# Configuration
SVG_NAMESPACE = "http://www.w3.org/2000/svg"
DC_NAMESPACE = "http://purl.org/dc/elements/1.1/"
ET.register_namespace('', SVG_NAMESPACE)
ET.register_namespace('dc', DC_NAMESPACE)

# Rate limiting configuration
MAX_RETRIES = 3
BASE_DELAY = 2  # seconds
GITHUB_API_DELAY = 1  # seconds between GitHub API requests

def fetch_topics():
    """Fetch topics list from GitHub repository with enhanced error handling"""
    print("📚 Fetching topics list...")
    
    try:
        # Step 1: Get directory listing with rate limit handling
        api_url = "https://api.github.com/repos/Pragament/json_data/contents/textbooks/page_attributes"
        response = safe_github_request(api_url)
        
        # Step 2: Filter JSON files
        files = [f for f in response.json() if f['name'].endswith('.json')]
        
        # Step 3: Process files with enhanced error handling
        topics = []
        for file in files[:25]:
            try:
                file_response = safe_raw_request(file['download_url'])
                
                if file_response.status_code == 200:
                    # Content validation
                    content = file_response.text.strip()
                    if not content.startswith(('{', '[')):
                        continue
                    
                    data = json.loads(content)
                    
                    # Handle different JSON structures
                    if isinstance(data, dict):
                        topic = data.get('title') or data.get('name')
                        if topic: topics.append(topic)
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                topic = item.get('title') or item.get('name')
                                if topic: topics.append(topic)
            
            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"⚠️ File processing error: {e}")
                continue
            finally:
                sleep(GITHUB_API_DELAY)  # Rate limiting
        
        if not topics:
            return get_fallback_topics()
            
        return list(dict.fromkeys(topics))[:25]  # Remove duplicates while preserving order
    
    except Exception as e:
        print(f"⚠️ GitHub processing error: {e}")
        return get_fallback_topics()

@retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(multiplier=1, min=BASE_DELAY))
def safe_github_request(url):
    """Safe GitHub API request with retries"""
    response = requests.get(url)
    if response.status_code == 403:
        reset_time = int(response.headers.get('X-RateLimit-Reset', 0)) - time.time()
        if reset_time > 0:
            sleep(max(reset_time, 0))
            raise Exception("Rate limit hit - waiting to retry")
    response.raise_for_status()
    return response

@retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(multiplier=1, min=BASE_DELAY))
def safe_raw_request(url):
    """Safe raw file request with retries"""
    response = requests.get(url)
    if response.status_code == 429:
        sleep(BASE_DELAY * 2)  # Double delay for 429 errors
        raise Exception("Too Many Requests - retrying")
    response.raise_for_status()
    return response

def get_fallback_topics():
    """Return curated educational topics"""
    return [
        "human anatomy", "world map", "electric circuit", "photosynthesis",
        "solar system", "periodic table", "human brain", "digestive system",
        "water cycle", "plant cell", "animal cell", "volcano diagram",
        "rock cycle", "food pyramid", "muscular system", "skeletal system",
        "respiratory system", "heart anatomy", "neuron structure",
        "ecosystem diagram", "climate zones", "tectonic plates",
        "electromagnetic spectrum", "atomic structure", "mitochondria structure"
    ]

def search_wikimedia_svg(topic):
    """Search Wikimedia Commons for SVG files using API"""
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": f'"{topic}" filetype:svg',
        "srlimit": 1,
        "srnamespace": 6  # File namespace
    }
    
    try:
        response = requests.get("https://commons.wikimedia.org/w/api.php", params=params)
        results = response.json()["query"]["search"]
        return results[0]["title"] if results else None
    except Exception as e:
        print(f"⚠️ Search error for {topic}: {e}")
        return None

def download_svg(file_title, topic):
    """Download SVG file from Wikimedia Commons"""
    filename = quote(file_title.replace("File:", "").replace(" ", "_"))
    url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{filename}"
    
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            os.makedirs("svgs", exist_ok=True)
            clean_topic = re.sub(r'\W+', '_', topic.lower())
            filepath = os.path.join("svgs", f"{clean_topic}.svg")
            
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            return filepath
    except Exception as e:
        print(f"⚠️ Download failed for {topic}: {e}")
    return None

def generate_placeholder_svg(topic):
    """Create fallback SVG when no image found"""
    print(f"⚠️ Generating placeholder for {topic}")
    svg_content = f'''<svg xmlns="{SVG_NAMESPACE}" width="400" height="300" viewBox="0 0 400 300">
        <rect width="100%" height="100%" fill="#f0f8ff"/>
        <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" 
              font-family="Arial" font-size="20" fill="#333">{topic}</text>
    </svg>'''
    
    clean_topic = re.sub(r'\W+', '_', topic.lower())
    filepath = os.path.join("svgs", f"{clean_topic}_placeholder.svg")
    with open(filepath, "w") as f:
        f.write(svg_content)
    return filepath

def enhance_svg(filepath, topic):
    """Add educational metadata and accessibility features"""
    try:
        if not filepath or not os.path.exists(filepath):
            raise FileNotFoundError("SVG file missing")
            
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        # Add title element for accessibility
        title = ET.SubElement(root, "title")
        title.text = f"Educational Diagram: {topic}"
        
        # Add frontend-compatible attributes
        root.set("data-map-type", "educational")
        root.set("data-zoom-level", "1")
        root.set("data-topic", topic.lower().replace(" ", "-"))
        
        # Add metadata section with proper namespaces
        metadata = ET.SubElement(root, "metadata")
        
        # Create DC elements with proper namespace handling
        dc_title = ET.SubElement(metadata, f"{{{DC_NAMESPACE}}}title")
        dc_title.text = topic
        
        dc_desc = ET.SubElement(metadata, f"{{{DC_NAMESPACE}}}description")
        dc_desc.text = f"Educational diagram about {topic}"
        
        tree.write(filepath, xml_declaration=True, encoding="utf-8")
        return filepath
    except Exception as e:
        print(f"⚠️ SVG enhancement failed for {topic}: {e}")
        return filepath

def generate_ai_explanation(filepath):
    """Generate educational content using Mistral AI"""
    try:
        if not filepath or not os.path.exists(filepath):
            raise FileNotFoundError("SVG file missing")
            
        with open(filepath, "r") as f:
            svg_content = f.read()
        
        prompt = f"""Analyze this educational SVG diagram and provide:
        1. Key elements explanation
        2. Real-world applications
        3. Common student misconceptions
        4. Interactive learning suggestions
        
        SVG Content:
        {svg_content}"""
        
        response = ollama.chat(
            model="mistral",
            messages=[{"role": "user", "content": prompt}]
        )
        
        explanation_path = filepath.replace(".svg", "_explanation.md")
        with open(explanation_path, "w") as f:
            f.write(f"# Educational Guide\n{response['message']['content']}")
        print(f"📘 Explanation saved: {explanation_path}")
    except Exception as e:
        print(f"⚠️ AI explanation failed: {e}")

def process_topic(topic):
    """Full processing pipeline for a single topic"""
    print(f"\n🔍 Processing: {topic}")
    
    # Phase 1: Content Acquisition
    file_title = search_wikimedia_svg(topic)
    svg_path = download_svg(file_title, topic) if file_title else None
    
    if not svg_path:
        svg_path = generate_placeholder_svg(topic)
    
    # Phase 2: SVG Enhancement
    enhanced_path = enhance_svg(svg_path, topic)
    
    # Phase 3: Educational Content Generation
    generate_ai_explanation(enhanced_path)
    
    return enhanced_path

def main():
    """Main execution flow"""
    print("🚀 Starting Educational SVG Processor")
    
    try:
        topics = fetch_topics()
        print(f"📋 Loaded {len(topics)} topics for processing")
        
        for topic in topics:
            process_topic(topic)
            sleep(1)  # Rate limiting
            
    except Exception as e:
        print(f"🔥 Critical error: {e}")
    
    print("\n✅ Processing complete. Check 'svgs' directory for results.")

if __name__ == "__main__":
    main()
