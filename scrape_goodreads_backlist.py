# scrape_goodreads_backlist.py

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import pandas as pd

# Load author names from your xlsx
author_df = pd.read_excel("announced_authors.xlsx", engine='openpyxl')
authors = author_df["Author Name"].dropna().tolist()

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
def scrape_goodreads_books(author_url, name, role, pen_name):
    books = []
    response = requests.get(author_url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    book_containers = soup.select("tr[itemtype='http://schema.org/Book']")
    for book in book_containers:
        title_tag = book.select_one("a.bookTitle span")
        title = title_tag.text.strip() if title_tag else "Unknown Title"

        series_tag = book.select_one("span.greyText.smallText")

        series_title = ""
        series_order = ""

        if series_tag and "Series" in series_tag.text:
            series_info = series_tag.text.strip()
            try:
                # Extract series name and order
                series_title, series_order = series_info.replace("Series:", "").strip().rsplit("(", 1)
                series_order = series_order.replace(")", "").replace("#", "").strip()
                series_title = series_title.strip()
            except ValueError:
                series_title = series_info.strip()
                series_order = ""

        pub_date = ""  # Placeholder (can enhance later)

        formats = "Ebook, Paperback, Audiobook"  # Default assumption

        books.append({
            "Author": name,
            "Book Title": title,
            "Series Title": series_title,
            "Series Order": series_order,
            "Published Date": pub_date,
            "Formats Available": formats,
            "Buy Links": "",  # Placeholder for buy links
            "Rent Links": "",  # Placeholder for rent links
            "Audiobook (Y/N)": "Y" if formats and "Audiobook" in formats else "N",
            "Narrators": "",  # Placeholder for narrators
            "Kindle Unlimited (Y/N)": "",  # Placeholder for Kindle Unlimited
            "Kobo+ (Y/N)": "",  # Placeholder for Kobo+
            "Genre": "",  # Placeholder for genre
            "Standalone/Series": "Series" if series_title else "Standalone",
            "Other Notes": "",  # Placeholder for other notes
            "Pen Name": "",  # Placeholder for pen name
            "Book Role": "Author"  # Default role
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

    # Save to xlsx
    df.to_xlsx("author_backlists_scraped.xlsx", index=False)

    print("Scraping completed! Data saved to author_backlists_scraped.xlsx")