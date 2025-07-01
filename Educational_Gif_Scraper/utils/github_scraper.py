import requests

def fetch_topic_list():
    owner = "Pragament"
    repo = "json_data"
    branch = "main"
    api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"

    try:
        res = requests.get(api_url, timeout=10)
        res.raise_for_status()  
        tree_data = res.json()
        
        print(f"[INFO] GitHub API response: {tree_data}") 

    except requests.exceptions.RequestException as e:
        print(f"[!] Failed to fetch repository tree: {e}")
        return []
    
    topics = []

    for item in tree_data.get("tree", []):
        if item["path"].startswith("textbooks/page_attributes/") and item["path"].endswith(".json"):
            file_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{item['path']}"
            try:
                file_res = requests.get(file_url, timeout=10)
                file_res.raise_for_status()
                data = file_res.json()

                print(f"[INFO] File content from {item['path']}: {data}")  

                if isinstance(data, dict):
                    for group in data.values():
                        if isinstance(group, list):
                          
                            topics.extend([entry['text'] for entry in group if isinstance(entry, dict) and 'text' in entry])
                elif isinstance(data, list):
                    topics.extend([entry['text'] for entry in data if isinstance(entry, dict) and 'text' in entry])
                else:
                    print(f"[~] Unexpected format in {item['path']}")
            except Exception as e:
                print(f"Error parsing {item['path']}: {e}")

    return list(set(topics)) 
