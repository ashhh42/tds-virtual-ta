import requests
import json
from datetime import datetime

BASE_URL = "https://discourse.onlinedegree.iitm.ac.in"

def scrape_discourse_posts(category_slug="tools-in-data-science", category_id=81, max_pages=3):
    """
    Scrapes post titles, IDs, and creation dates from the TDS Discourse forum.
    Returns a list of dictionaries.
    """
    all_posts = []

    for page in range(0, max_pages):
        url = f"{BASE_URL}/c/{category_slug}/{category_id}.json?page={page}"
        try:
            print(f"Scraping: {url}")
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            topics = data.get("topic_list", {}).get("topics", [])
            for topic in topics:
                all_posts.append({
                    "id": topic["id"],
                    "title": topic["title"],
                    "created_at": topic["created_at"],
                    "url": f"{BASE_URL}/t/{topic['slug']}/{topic['id']}"
                })

        except Exception as e:
            print(f"Failed to fetch page {page}: {e}")

    return all_posts

def save_posts_to_file(posts, filename="discourse_posts.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Saved {len(posts)} posts to {filename}")

if __name__ == "__main__":
    posts = scrape_discourse_posts(max_pages=3)  # Adjust pages as needed
    save_posts_to_file(posts)
