# fetch_author_links.py (reverted to DuckDuckGo and improved for type safety + author filtering + stricter website logic)

import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re
import json
import os
import urllib.parse
from urllib.parse import unquote, urlparse, parse_qs
import concurrent.futures as cf
import validators

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}
CACHE_FILE = "link_cache.json"

# Load existing cache
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        link_cache = json.load(f)
else:
    link_cache = {}

def save_cache():
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(link_cache, f, indent=2)

def search_duckduckgo(query, retries=3):
    url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            results = soup.find_all("a", attrs={"class": "result__a"})
            return [link.get("href") for link in results if link.get("href")]
        except requests.exceptions.RequestException as e:
            print(f"Retry {attempt + 1} failed for query: {query} — {e}")
            time.sleep(5)
    return []

def find_best_match(links, domain):
    for link in links:
        if domain in link:
            return link
    return ""

def clean_link(link):
    parsed = urllib.parse.urlparse(link)
    if parsed.scheme in ["http", "https"]:
        return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, "","",""))
    return link

def is_valid_url(url):
    return validators.url(url)

def name_in_domain(link, name):
    try:
        parsed = urlparse(link)
        domain = parsed.netloc.lower()
        name_parts = name.lower().split()
        return any(part in domain for part in name_parts)
    except Exception as e:
        print(f"Error parsing link: {link} - {e}")
        return False

# Load the CSV
df = pd.read_csv("announced_authors.csv")

# Ensure link columns exist and cast to string
for col in ["Website", "Amazon Page", "Goodreads Page", "Verified"]:
    if col not in df.columns:
        df[col] = ""
    else:
        df[col] = df[col].astype(str)

df["Verified"] = df["Verified"].fillna("No")

for idx, row in df.iterrows():
    name = row["Author Name"]
    if not isinstance(name, str) or not name.strip():
        continue

    if row["Verified"] == "Yes":
        continue

    if name in link_cache:
        cached = link_cache[name]
        df.at[idx, "Website"] = cached.get("Website", "")
        df.at[idx, "Amazon Page"] = cached.get("Amazon Page", "")
        df.at[idx, "Goodreads Page"] = cached.get("Goodreads Page", "")
        print(f"✅ Loaded from cache: {name}")
        continue

    print(f"🔍 Searching links for {name} using DuckDuckGo...")

    queries = {
        "Website": f"{name} official site",
        "Amazon Page": f"{name} Amazon author page",
        "Goodreads Page": f"{name} Goodreads profile"
    }

    links_found = {}
    with cf.ThreadPoolExecutor() as executor:
        futures = []
        for key, query in queries.items():
            futures.append(executor.submit(search_duckduckgo, query))
        for key, future in zip(queries.keys(), futures):
            try:
                results = future.result()
                if not results:
                    print(f"No results found for {key} of {name}")
                    links_found[key] = ""
                    continue
                match = ""
                if key == "Website":
                    match = next((l for l in results if not any(x in l for x in ["amazon.com", "goodreads.com", "facebook.com", "twitter.com", "instagram.com"]) and name_in_domain(l, name)), "")
                elif key == "Amazon Page":
                    match = find_best_match(results, "amazon.com")
                elif key == "Goodreads Page":
                    match = find_best_match(results, "goodreads.com")
                links_found[key] = clean_link(match)
            except Exception as e:
                print(f"Error searching for {key} of {name}: {e}")
                links_found[key] = ""

    for col in ["Website", "Amazon Page", "Goodreads Page"]:
        df.at[idx, col] = str(links_found[col] or df.at[idx, col])

    if all(is_valid_url(df.at[idx, col]) for col in ["Website", "Amazon Page", "Goodreads Page"]):
        df.at[idx, "Verified"] = "Yes"
    else:
        df.at[idx, "Verified"] = "No"

    link_cache[name] = {
        "Website": df.at[idx, "Website"],
        "Amazon Page": df.at[idx, "Amazon Page"],
        "Goodreads Page": df.at[idx, "Goodreads Page"]
    }
    print(f"✅ {name}: Verified = {df.at[idx, 'Verified']}")
    time.sleep(2)

# Save the updated CSV
try:
    df.to_csv("announced_authors.csv", index=False)
    print("\n🔗 Author/narrator links updated in announced_authors.csv")
    save_cache()
except PermissionError:
    print("⚠️ Could not write to announced_authors.csv — is it still open in Excel?")
