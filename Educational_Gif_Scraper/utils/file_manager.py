import json
import os

def save_results(data, filename="data/gif_links.json"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[✔] Saved {len(data)} topics to {filename}")
