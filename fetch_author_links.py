# fetch_author_links.py (updated for DuckDuckGo redirects + verified fix)

import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import unquote, urlparse, parse_qs

# DuckDuckGo search helper
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

def search_duckduckgo(query):
    url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
    resp = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(resp.text, 'html.parser')
    results = soup.find_all("a", attrs={"class": "result__a"})
    return [link.get("href") for link in results if link.get("href")]

def find_best_match(links, domain):
    for link in links:
        if domain in link:
            return link
    return ""

def clean_link(link):
    if "duckduckgo.com/l/?" in link and "uddg=" in link:
        parsed = urlparse(link)
        qs = parse_qs(parsed.query)
        if "uddg" in qs:
            return unquote(qs["uddg"][0])
    return re.sub(r'(\?.*)|(\#.*)', '', link)

def is_valid_url(url):
    return isinstance(url, str) and url.startswith("http")

# Load the CSV
df = pd.read_csv("announced_authors.csv")

# Ensure link columns exist
df["Website"] = df.get("Website", "")
df["Amazon Page"] = df.get("Amazon Page", "")
df["Goodreads Page"] = df.get("Goodreads Page", "")
df["Verified"] = df.get("Verified", "No")

for idx, row in df.iterrows():
    if row["Verified"] == "Yes":
        continue  # Skip verified rows

    name = row["Author Name"]
    print(f"Searching links for {name}...")

    queries = {
        "Website": f"{name} official site",
        "Amazon Page": f"{name} Amazon author",
        "Goodreads Page": f"{name} Goodreads author"
    }

    links_found = {}
    for key, query in queries.items():
        try:
            results = search_duckduckgo(query)
            match = ""
            if key == "Website":
                match = next((l for l in results if not any(x in l for x in ["amazon.com", "goodreads.com", "facebook.com", "twitter.com", "instagram.com"])), "")
            elif key == "Amazon Page":
                match = find_best_match(results, "amazon.com")
            elif key == "Goodreads Page":
                match = find_best_match(results, "goodreads.com")
            links_found[key] = clean_link(match)
        except Exception as e:
            print(f"Error searching for {key} of {name}: {e}")
            links_found[key] = ""
        time.sleep(1)

    df.at[idx, "Website"] = links_found["Website"] or df.at[idx, "Website"]
    df.at[idx, "Amazon Page"] = links_found["Amazon Page"] or df.at[idx, "Amazon Page"]
    df.at[idx, "Goodreads Page"] = links_found["Goodreads Page"] or df.at[idx, "Goodreads Page"]

    if all(is_valid_url(df.at[idx, col]) for col in ["Website", "Amazon Page", "Goodreads Page"]):
        df.at[idx, "Verified"] = "Yes"
    else:
        df.at[idx, "Verified"] = "No"

    print(f"✅ {name}: Verified = {df.at[idx, 'Verified']}")
    time.sleep(2)

# Save the updated file
df.to_csv("announced_authors.csv", index=False)
print("\n🔗 Author/narrator links updated in announced_authors.csv")