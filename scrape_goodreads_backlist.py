# scrape_goodreads_backlist.py

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Headers to mimic a real browser visit
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

# Function to search Goodreads for an author
def search_goodreads_author(author_name):
    search_url = f"https://www.goodreads.com/search?q={author_name.replace(' ', '+')}&search_type=authors"
    response = requests.get(search_url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    author_link_tag = soup.select_one("a.authorName")
    if author_link_tag:
        author_link = author_link_tag["href"]
        if author_link.startswith("/"):
            author_link = "https://www.goodreads.com" + author_link
        return author_link
    else:
        print(f"No author page found for {author_name}")
        return None

# Function to scrape books from author's Goodreads page
def scrape_goodreads_books(author_url):
    books = []
    response = requests.get(author_url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    book_containers = soup.select("tr[itemtype='http://schema.org/Book']")
    for book in book_containers:
        title_tag = book.select_one("a.bookTitle span")
        title = title_tag.text.strip() if title_tag else "Unknown Title"

        series_tag = book.select_one("span.greyText.smallText")
        if series_tag and "(" in series_tag.text:
            series_info = series_tag.text.strip()
            series_title, series_order = series_info.rsplit('(', 1)
            series_title = series_title.strip()
            series_order = series_order.replace(')', '').replace('#', '').strip()
        else:
            series_title = ""
            series_order = ""

        pub_date = ""  # Placeholder (can enhance later)

        formats = "Ebook, Paperback, Audiobook"  # Default assumption

        books.append({
            "Book Title": title,
            "Series Title": series_title,
            "Series Order": series_order,
            "Published Date": pub_date,
            "Formats Available": formats
        })

    return books

# Main Runner
if __name__ == "__main__":
    authors = [
        "Tessa Bailey",
        "Kennedy Ryan",
        "Lucy Score"
    ]

    all_books = []

    for author in authors:
        print(f"Scraping {author}...")
        author_url = search_goodreads_author(author)
        if author_url:
            books = scrape_goodreads_books(author_url)
            for book in books:
                book["Author"] = author  # Add author field
            all_books.extend(books)
        time.sleep(2)  # Sleep between authors to be polite

    # Create DataFrame
    df = pd.DataFrame(all_books)

    # Save to CSV
    df.to_csv("author_backlists_scraped.csv", index=False)

    print("Scraping completed! Data saved to author_backlists_scraped.csv")