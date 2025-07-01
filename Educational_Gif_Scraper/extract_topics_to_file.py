# extract_topics_to_file.py

from utils.github_scraper import fetch_topic_list
import json

def save_topics(topics, filename="topics.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(sorted(topics), f, indent=2, ensure_ascii=False)
    print(f"[✓] Saved {len(topics)} topics to {filename}")

def main():
    topics = fetch_topic_list()
    if not topics:
        print("[!] No topics fetched.")
        return
    save_topics(topics)

if __name__ == "__main__":
    main()
