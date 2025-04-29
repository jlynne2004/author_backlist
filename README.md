# Goodreads Author Backlist Scraper 📚✨

This Python script automatically scrapes authors' backlists from Goodreads and exports the data into a CSV file — perfect for creating event guides, reader tools, or personal libraries!

## Features
- Searches Goodreads for authors based on name
- Scrapes book titles, series information, and basic format availability
- Exports all collected data to a CSV
- Easy to extend for Excel dashboard creation

## Requirements
- Python 3.8+
- Packages:
  - `requests`
  - `beautifulsoup4`
  - `pandas`

## Setup
1. Clone this repository.
2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3. Run the script:
    ```bash
    python scrape_goodreads_backlist.py
    ```

## Output
- Generates a file called `author_backlists_scraped.csv` containing the author's backlist.

## Notes
- This version assumes standard Goodreads author pages. Some edge cases may require additional handling.
- Be mindful of Goodreads' robots.txt and rate-limit yourself appropriately.

---

**Built with ☕ and 📚 by [Your Name or Brand].**
