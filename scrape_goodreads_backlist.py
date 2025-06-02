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
                
                for i, elem in enumerate(date_elements):
                    text = elem.get_text().strip()
                    print(f"  Checking date element {i+1}: '{text[:100]}...'")  # Debug output (truncated)
                    
                    # Skip if this is clearly ONLY a rating element or ONLY editions
                    if ('rate this book' in text.lower() and 'published' not in text.lower()) or \
                       (text.lower().strip().endswith('editions') and 'published' not in text.lower()):
                        print(f"    Skipping non-date element")
                        continue
                    
                    # Look for the word "published" in the text - this is our main indicator
                    if 'published' in text.lower():
                        print(f"    Found 'published' in text, parsing...")
                        
                        # Pattern for "published Month Day, Year"
                        date_pattern1 = r'published\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})'
                        match1 = re.search(date_pattern1, text, re.IGNORECASE)
                        if match1:
                            published_date = match1.group(1)
                            print(f"  ✅ Found date (pattern 1): {published_date}")
                            break
                        
                        # Pattern for "published Year" (like "published 2021")
                        date_pattern_year = r'published\s+(\d{4})'
                        match_year = re.search(date_pattern_year, text, re.IGNORECASE)
                        if match_year:
                            published_date = match_year.group(1)
                            print(f"  ✅ Found year (published pattern): {published_date}")
                            break
                        
                        # Pattern for "published Month Year" (like "published March 2021")
                        date_pattern_month_year = r'published\s+([A-Za-z]+\s+\d{4})'
                        match_month_year = re.search(date_pattern_month_year, text, re.IGNORECASE)
                        if match_month_year:
                            published_date = match_month_year.group(1)
                            print(f"  ✅ Found month/year (published pattern): {published_date}")
                            break
                    
                    # If no "published" found, try general date patterns (but be more careful)
                    else:
                        # Pattern for just "Month Day, Year"
                        date_pattern2 = r'\b([A-Za-z]+\s+\d{1,2},\s+\d{4})\b'
                        match2 = re.search(date_pattern2, text)
                        if match2:
                            published_date = match2.group(1)
                            print(f"  ✅ Found date (pattern 2): {published_date}")
                            break
                        
                        # Pattern for just a year (4 digits) - only if not in ratings context
                        if 'avg rating' not in text.lower():
                            date_pattern3 = r'\b(\d{4})\b'
                            match3 = re.search(date_pattern3, text)
                            if match3:
                                year = match3.group(1)
                                # Make sure it's a reasonable publication year
                                if 1900 <= int(year) <= 2030:
                                    published_date = year
                                    print(f"  ✅ Found year: {published_date}")
                                    break
                
            except Exception as e:
                print(f"  ❌ Error extracting date for '{title}': {e}")

            # If still no date found, report it
            if not published_date:
                print(f"  ⚠️  No date found for '{title}'")

            formats = "Ebook, Paperback" # Default formats

            book_data = {
                "Author": name,
                "Book Title": title,
                "Series Title": series_title,
                "Series Order": series_order,
                "Published Date": published_date,  # This should now work!
                "Formats Available": formats,  # Use the defult format
                "Standalone/Series": "Series" if series_title else "Standalone",
                "Pen Name": pen_name,  # Fixed: was empty, now uses the parameter
                "Role": role  # Fixed: was "Book Role", now uses correct field name
            }
            
            books.append(book_data)
            print(f"  📚 Added '{title}'")

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
    author_df = pd.read_excel("announced_authors.xlsx", engine='openpyxl')
   
    all_books = []

    for idx, row in author_df.iterrows():
        author_name = row["Author Name"]
        role = row.get("Role", "Author")
        other_names = row.get("Other Names", "")
        
        if pd.isna(author_name):
            continue
            
        print(f"\n🔍 Scraping {author_name} ({role})...")
        
        # Scrape main name
        author_url = search_goodreads_author(author_name)
        if author_url:
            books = scrape_goodreads_books(author_url, author_name, role, author_name)
            all_books.extend(books)
            time.sleep(2)  # Be polite to Goodreads
        
        # Scrape pen names if they exist
        if not pd.isna(other_names) and str(other_names).strip():
            pen_names = [name.strip() for name in str(other_names).split(",") if name.strip()]
            for pen_name in pen_names:
                print(f"  🖋️  Also scraping pen name: {pen_name}")
                pen_url = search_goodreads_author(pen_name)
                if pen_url:
                    pen_books = scrape_goodreads_books(pen_url, author_name, role, pen_name)
                    all_books.extend(pen_books)
                    time.sleep(2)

    # Create DataFrame and save
    df = pd.DataFrame(all_books)
    df.to_excel("author_backlists_scraped.xlsx", index=False)
    
    print(f"\n🎉 Scraping completed! Found {len(all_books)} total books")
    print("Data saved to author_backlists_scraped.xlsx")