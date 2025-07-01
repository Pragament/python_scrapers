import feedparser
import pandas as pd
import random
import time
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

i = 0
time.sleep(random.uniform(10, 20)) 

while i < 3: 
    rss_urls = [
    "https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi",
    "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtaHBHZ0pKVGlnQVAB?hl=hi&gl=IN&ceid=IN:hi",
    "https://news.google.com/rss/topics/CAAqIQgKIhtDQkFTRGdvSUwyMHZNRE55YXpBU0FtaHBLQUFQAQ?hl=hi&gl=IN&ceid=IN:hi",
    "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtaHBHZ0pKVGlnQVAB?hl=hi&gl=IN&ceid=IN:hi",
    "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y1RjU0FtaHBHZ0pKVGlnQVAB?hl=hi&gl=IN&ceid=IN:hi",
    "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtaHBHZ0pKVGlnQVAB?hl=hi&gl=IN&ceid=IN:hi",
    "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtaHBHZ0pKVGlnQVAB?hl=hi&gl=IN&ceid=IN:hi",
    "https://news.google.com/rss/topics/CAAqJAgKIh5DQkFTRUFvS0wyMHZNREp3TUhRMVpoSUNhR2tvQUFQAQ?hl=hi&gl=IN&ceid=IN:hi",
    "https://news.google.com/rss/topics/CAAqIggKIhxDQkFTRHdvSkwyMHZNREp0WmpGdUVnSm9hU2dBUAE?hl=hi&gl=IN&ceid=IN:hi",
    "https://news.google.com/rss/topics/CAAqJAgKIh5DQkFTRUFvS0wyMHZNSEk0YkhsM054SUNhR2tvQUFQAQ?hl=hi&gl=IN&ceid=IN:hi",
    "https://news.google.com/rss/topics/CAAqHAgKIhZDQklTQ2pvSWJHOWpZV3hmZGpJb0FBUAE?hl=hi&gl=IN&ceid=IN:hi",
    "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxYUdjU0FtaHBHZ0pKVGlnQVAB?hl=hi&gl=IN&ceid=IN:hi"
]



    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:102.0) Gecko/20100101 Firefox/102.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
        "Mozilla/5.0 (Linux; Android 11; SM-A515F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Mobile Safari/537.36",
    ]

    data = []
    seen_links = set()

    for rss_url in rss_urls:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        feed = feedparser.parse(rss_url, request_headers=headers)

        for entry in feed.entries:
            link = entry.link
            if link in seen_links:
                continue

            title = entry.title
            published = entry.published if 'published' in entry else ''
            source = entry.source.title if 'source' in entry else ''
            summary = entry.summary if 'summary' in entry else ''

            data.append({"source": source, "title": title, "summary": summary, "published": published, "link": link})
            seen_links.add(link)

        time.sleep(random.uniform(1, 3))

    print(f"Collected {len(data)} news items.")

    if len(data) < 100:
        raise ValueError("Not enough news articles collected. Try later.")

    titles = [item['title'] for item in data]
    links = [item['link'] for item in data]
    sources = [item['source'] for item in data]

    vectorizer = TfidfVectorizer().fit_transform(titles)
    similarity_matrix = cosine_similarity(vectorizer)

    paired_data = []
    used = set()

    for i1 in range(len(titles)):
        if i1 in used:
            continue
        similarity_scores = list(enumerate(similarity_matrix[i1]))
        similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)

        for j, score in similarity_scores[1:]:
            if j not in used and score > 0.3:
                paired_data.append({
                    "Headline1_text": titles[i1],
                    "Headline1_source": sources[i1],
                    "Headline1_url": links[i1],
                    "Headline2_text": titles[j],
                    "Headline2_source": sources[j],
                    "Headline2_url": links[j]
                })
                used.add(i1)
                used.add(j)
                break

    # Save to CSV
    output_file = r'News_pairs.csv'

    if os.path.exists(output_file):
        existing_df = pd.read_csv(output_file)
        new_df = pd.DataFrame(paired_data)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        combined_df.drop_duplicates(subset=["Headline1_url", "Headline2_url"], inplace=True)
        combined_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"Appended {len(new_df)} new pairs. Total pairs now: {len(combined_df)}")
    else:
        new_df = pd.DataFrame(paired_data)
        new_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"Created new file with {len(new_df)} headline pairs.")

    print("In file :")
    print(pd.read_csv(output_file).head())
    
    i += 1  
