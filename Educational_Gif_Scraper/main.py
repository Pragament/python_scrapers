from utils.github_scraper import fetch_topic_list
from utils.gif_fetcher import fetch_gif_urls
from utils.file_manager import save_results
from utils.ai_generator import suggest_gif_description
import json
import os
import time

MIN_TOPICS = 75
TOPIC_FILE = "topics.json"

def fetch_topic_list_from_file(filename=TOPIC_FILE):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] Could not read {filename}: {e}")
        return []

def main():
    topics = fetch_topic_list_from_file()

    if not topics:
        print("[~] Local file not found or empty. Fetching from GitHub...")
        topics = fetch_topic_list()
        if not topics:
            print("[!] Invalid or empty topic list.")
            return
        else:
            with open(TOPIC_FILE, "w", encoding="utf-8") as f:
                json.dump(sorted(topics), f, indent=2, ensure_ascii=False)
            print(f"[✓] Saved {len(topics)} topics to {TOPIC_FILE}")

    gif_data = {}
    count = 0

    try:
        for topic in topics:
            if count >= MIN_TOPICS:
                break
            if topic in gif_data:
                continue

            gifs = fetch_gif_urls(topic)
            if gifs:
                gif_data[topic] = gifs
                count += 1
                print(f"[+] {count}: {topic} — {len(gifs)} GIF(s)")
            else:
                description = suggest_gif_description(topic)
                gif_data[topic] = {"description": description}
                print(f"[~] Suggested idea for: {topic}")

            time.sleep(1.5)
    except KeyboardInterrupt:
        print("\n[✋] Interrupted by user. Saving progress...")

    save_results(gif_data)

if __name__ == "__main__":
    main()
