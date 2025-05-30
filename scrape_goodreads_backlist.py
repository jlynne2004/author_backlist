# scrape_goodreads_backlist.py (FIXED VERSION)

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

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
    
    print(f"Found {len(book_containers)} books for {name}")
    
    try:
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

            # DATE SCRAPING - FIXED VERSION
            published_date = ""
            
            try:
                # Look for publication date within THIS specific book container
                date_elements = book.select('.greyText')
                
                for elem in date_elements:
                    if elem == series_tag:  # Skip the series tag we already processed
                        continue
                        
                    text = elem.get_text().strip()
                    print(f"  Checking date text: '{text}'")  # Debug output
                    
                    # Pattern for "published Month Day, Year"
                    date_pattern1 = r'published\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})'
                    match1 = re.search(date_pattern1, text, re.IGNORECASE)
                    if match1:
                        published_date = match1.group(1)
                        print(f"  ✅ Found date (pattern 1): {published_date}")
                        break
                    
                    # Pattern for just "Month Day, Year"
                    date_pattern2 = r'\b([A-Za-z]+\s+\d{1,2},\s+\d{4})\b'
                    match2 = re.search(date_pattern2, text)
                    if match2:
                        published_date = match2.group(1)
                        print(f"  ✅ Found date (pattern 2): {published_date}")
                        break
                    
                    # Pattern for "Month Year" (less specific)
                    date_pattern3 = r'\b([A-Za-z]+\s+\d{4})\b'
                    match3 = re.search(date_pattern3, text)
                    if match3:
                        published_date = match3.group(1)
                        print(f"  ✅ Found date (pattern 3): {published_date}")
                        break
                
                # If still no date, check all text in the book container
                if not published_date:
                    all_book_text = book.get_text()
                    
                    # Try the patterns on all text
                    date_pattern1 = r'published\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})'
                    match1 = re.search(date_pattern1, all_book_text, re.IGNORECASE)
                    if match1:
                        published_date = match1.group(1)
                        print(f"  ✅ Found date in full text: {published_date}")
                    else:
                        date_pattern2 = r'\b([A-Za-z]+\s+\d{1,2},\s+\d{4})\b'
                        match2 = re.search(date_pattern2, all_book_text)
                        if match2:
                            published_date = match2.group(1)
                            print(f"  ✅ Found date in full text (pattern 2): {published_date}")
                
            except Exception as e:
                print(f"  ❌ Error extracting date for '{title}': {e}")

            # If still no date found, report it
            if not published_date:
                print(f"  ⚠️  No date found for '{title}'")

            formats = "Ebook, Paperback, Audiobook"  # Default assumption

            book_data = {
                "Author": name,
                "Book Title": title,
                "Series Title": series_title,
                "Series Order": series_order,
                "Published Date": published_date,  # This should now work!
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
                "Pen Name": pen_name,  # Fixed: was empty, now uses the parameter
                "Role": role  # Fixed: was "Book Role", now uses correct field name
            }
            
            books.append(book_data)
            print(f"  📚 Added '{title}' with date: '{published_date}'")

    except Exception as e:
        print(f"❌ Error scraping books for {name}: {e}")

    return books

# Alternative debugging approach - add this to see what's actually on the page:
def debug_goodreads_page(author_url):
    """Debug function to see what's actually on a Goodreads author page"""
    try:
        response = requests.get(author_url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print(f"\n🔍 DEBUGGING PAGE: {author_url}")
        
        # Find all book containers
        book_containers = soup.select("tr[itemtype='http://schema.org/Book']")
        print(f"Found {len(book_containers)} book containers")
        
        if book_containers:
            # Look at the first book in detail
            first_book = book_containers[0]
            print(f"\n📖 FIRST BOOK ANALYSIS:")
            print(f"Full HTML: {first_book}")
            
            # Find all grey text elements
            grey_elements = first_book.select('.greyText')
            print(f"\nFound {len(grey_elements)} .greyText elements:")
            for i, elem in enumerate(grey_elements):
                print(f"  {i+1}: '{elem.get_text().strip()}'")
            
            # Look for date patterns in full book text
            book_text = first_book.get_text()
            print(f"\nFull book text: {book_text}")
            
            # Find potential dates
            import re
            date_patterns = re.findall(r'[A-Za-z]+\s+\d{1,2},\s+\d{4}', book_text)
            print(f"Potential dates found: {date_patterns}")
            
    except Exception as e:
        print(f"❌ Debug error: {e}")

# Test function for a single author
def test_single_author(author_name):
    """Test scraping for a single author with detailed output"""
    print(f"\n🧪 TESTING: {author_name}")
    author_url = search_goodreads_author(author_name)
    if author_url:
        print(f"Found author URL: {author_url}")
        
        # First, debug the page
        debug_goodreads_page(author_url)
        
        # Then try scraping
        books = scrape_goodreads_books(author_url, author_name, "Author", author_name)
        
        print(f"\n📊 RESULTS:")
        for book in books:
            print(f"  📚 {book['Book Title']} - Date: '{book['Published Date']}'")
    else:
        print(f"❌ No URL found for {author_name}")

# Main Runner
if __name__ == "__main__":
    # Test with a single author first
    test_single_author("Tessa Bailey")
    
    # Uncomment below for full scraping
    """
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
            books = scrape_goodreads_books(author_url, author, "Author", author)
            all_books.extend(books)
        time.sleep(2)  # Sleep between authors to be polite

    # Create DataFrame
    df = pd.DataFrame(all_books)

    # Save to xlsx
    df.to_excel("author_backlists_scraped.xlsx", index=False)

    print("Scraping completed! Data saved to author_backlists_scraped.xlsx")
    """