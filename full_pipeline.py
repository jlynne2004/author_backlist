# full_pipeline.py (HTML Dashboard Version - No More Excel Drama!)

import os
from scrape_goodreads_backlist import search_goodreads_author, scrape_goodreads_books
import pandas as pd
from openpyxl import load_workbook
import time
import re
from html import escape

# ----------------------- SCRAPE PHASE -----------------------
print("[1/2] Scraping Goodreads backlists...")

# Load authors from your real convention xlsx
wb = load_workbook("announced_authors.xlsx")
ws = wb.active

data = []
for row in ws.iter_rows(min_row=2, values_only=True):
    author = row[0]
    role = row[1]
    other_names = row[2]
    website_link = row[3]
    goodreads_link = row[4]
    amazon_link = row[5]
    audible_link = row[6]
    
    data.append({
        "Author Name": author,
        "Role": role,
        "Other Names": other_names,
        "Website": website_link,
        "Goodreads Page": goodreads_link,
        "Amazon Page": amazon_link,
        "Audible Page": audible_link
    })

author_df = pd.DataFrame(data)

# Load existing scraped data if it exists
if os.path.exists("author_backlists_scraped.xlsx"):
    existing_data = pd.read_excel("author_backlists_scraped.xlsx", engine="openpyxl")
    scraped_authors = existing_data["Author"].dropna().unique().tolist()
    print(f"Found existing scraped data. {len(scraped_authors)} authors already scraped.")
else:
    existing_data = pd.DataFrame()
    scraped_authors = []

# Determine which entries still need to be scraped
entries_to_scrape = [entry for entry in data if entry["Author Name"] not in scraped_authors]
print(f"Entries to scrape: {[e['Author Name'] for e in entries_to_scrape]}")

new_books = []
for idx, row in author_df.iterrows():
    name = str(row.get("Author Name", "")).strip()
    if not name or name.lower() == "nan":
        print(f"⚠️  Skipping row {idx} — missing Author Name")
        continue

    if name in scraped_authors:
        continue  # already scraped

    role = str(row.get("Role", "")).strip() or "Author"
    other_names_raw = row.get("Other Names")
    if pd.isna(other_names_raw):
        other_names_raw = ""
    pen_names = [n.strip() for n in str(other_names_raw).split(",") if n.strip()]

    names_to_scrape = [name] + pen_names

    for pen_name in names_to_scrape:
        print(f"🔍 Scraping {pen_name} for {name} ({role})...")
        author_url = search_goodreads_author(pen_name)
        if author_url:
            books = scrape_goodreads_books(author_url, name, role, pen_name)
            for book in books:
                book["Author"] = name
                book["Pen Name"] = pen_name if pen_name != name else ""
                book["Role"] = role
            new_books.extend(books)
        time.sleep(2)
    print(f"✅ Finished scraping {name}")

# Merge new data with existing data
if new_books:
    new_data = pd.DataFrame(new_books)
    full_data = pd.concat([existing_data, new_data], ignore_index=True)
else:
    full_data = existing_data

# Save updated data
full_data.to_excel("author_backlists_scraped.xlsx", index=False)
print("Scraping complete. Data saved to author_backlists_scraped.xlsx\n")

# ----------------------- HTML DASHBOARD PHASE -----------------------
print("[2/2] Building HTML dashboard...")

def clean_url(url):
    """Clean and validate URL"""
    if not url or pd.isna(url) or str(url).strip() == "":
        return None
    
    url = str(url).strip()
    if url.startswith("http://") or url.startswith("https://"):
        return url
    else:
        return "https://" + url

def create_html_dashboard():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Charm City Romanticon 2026 - Author Backlists</title>
    <style>
        * {
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        
        .header {
            background: #EC008C;
            color: white;
            padding: 40px 30px;
            text-align: center;
        }
        
        .header h1 {
            margin: 0;
            font-size: 2.8em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            margin: 10px 0 0 0;
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .support-message {
            background: linear-gradient(45deg, #f8f9fa, #e9ecef);
            padding: 25px;
            margin: 25px;
            border-radius: 12px;
            border-left: 6px solid #EC008C;
            font-style: italic;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .support-message strong {
            color: #EC008C;
            font-size: 1.1em;
        }
        
        .search-bar {
            padding: 20px;
            text-align: center;
            background: #f8f9fa;
            border-bottom: 1px solid #eee;
        }
        
        .search-input {
            padding: 12px 20px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 25px;
            width: 300px;
            max-width: 90%;
            outline: none;
            transition: border-color 0.3s ease;
        }
        
        .search-input:focus {
            border-color: #EC008C;
        }
        
        .authors-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 25px;
            padding: 30px;
        }
        
        .author-card {
            background: white;
            border: 2px solid #EC008C;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .author-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #EC008C, #ff6b9d);
        }
        
        .author-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.15);
            border-color: #d1007a;
        }
        
        .author-name {
            font-size: 1.5em;
            font-weight: bold;
            color: #EC008C;
            margin-bottom: 8px;
        }
        
        .author-role {
            color: #666;
            margin-bottom: 20px;
            font-style: italic;
            font-size: 1.05em;
        }
        
        .links {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .link-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 10px 15px;
            background: linear-gradient(45deg, #EC008C, #ff6b9d);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            transition: all 0.3s ease;
            font-size: 0.9em;
            font-weight: 500;
            text-align: center;
        }
        
        .link-btn:hover {
            background: linear-gradient(45deg, #d1007a, #e55a87);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(236, 0, 140, 0.3);
        }
        
        .link-btn span {
            margin-right: 8px;
            font-size: 1.1em;
        }
        
        .books-section {
            margin-top: 20px;
            padding-top: 20px;
            border-top: 2px solid #f0f0f0;
        }
        
        .books-toggle {
            background: linear-gradient(45deg, #f8f9fa, #e9ecef);
            border: 2px solid #EC008C;
            padding: 12px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            margin-bottom: 15px;
            transition: all 0.3s ease;
            color: #EC008C;
            text-align: center;
        }
        
        .books-toggle:hover {
            background: #EC008C;
            color: white;
        }
        
        .books-list {
            display: none;
            max-height: 400px;
            overflow-y: auto;
            font-size: 0.95em;
        }
        
        .books-list.show {
            display: block;
            animation: slideDown 0.3s ease;
        }
        
        @keyframes slideDown {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .book-item {
            padding: 12px;
            border-bottom: 1px solid #f0f0f0;
            transition: background 0.2s ease;
        }
        
        .book-item:hover {
            background: #f8f9fa;
        }
        
        .book-title {
            font-weight: bold;
            color: #333;
            margin-bottom: 4px;
        }
        
        .book-series {
            color: #666;
            font-size: 0.85em;
        }
        
        .book-meta {
            color: #888;
            font-size: 0.8em;
            margin-top: 4px;
        }
        
        .footer {
            text-align: center;
            padding: 30px;
            background: #f8f9fa;
            font-style: italic;
            color: #666;
            border-top: 1px solid #eee;
        }
        
        .stats {
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            color: #666;
            font-size: 0.9em;
        }
        
        .hidden {
            display: none !important;
        }
        
        @media (max-width: 768px) {
            .authors-grid {
                grid-template-columns: 1fr;
                padding: 20px;
                gap: 20px;
            }
            
            .header h1 {
                font-size: 2.2em;
            }
            
            .support-message {
                margin: 15px;
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Charm City Romanticon 2026</h1>
            <p>Author & Narrator Backlists</p>
        </div>
        
        <div class="support-message">
            <strong>💡 Support Authors Directly</strong><br>
            Whenever possible, consider purchasing books directly from the author's website if they have a store.
            Amazon takes a significant portion of royalties and can penalize authors for piracy and other issues beyond their control — even removing their accounts.
            We understand that Amazon is convenient and affordable, and authors still rely on it.
            But every direct purchase makes a bigger impact. 💖
        </div>
        
        <div class="search-bar">
            <input type="text" class="search-input" placeholder="Search authors..." onkeyup="searchAuthors()">
        </div>
        
        <div class="stats" id="stats">
            Loading authors...
        </div>
        
        <div class="authors-grid" id="authorsGrid">
"""
    
    # Track stats
    total_authors = 0
    total_books = 0
    
    # Add each author
    for person in sorted(full_data["Author"].dropna().unique()):
        person_data = full_data[full_data["Author"].str.lower() == person.lower()]
        role = person_data["Role"].iloc[0] if "Role" in person_data else "Author"
        
        # Find author info
        author_row = None
        for entry in data:
            if entry["Author Name"] == person:
                author_row = entry
                break
        
        if not author_row:
            continue
        
        total_authors += 1
        books = person_data.to_dict('records')
        total_books += len(books)
        
        # Clean person name for JavaScript
        clean_person = escape(person).replace("'", "\\'")
        
        html_content += f"""
            <div class="author-card" data-name="{escape(person.lower())}" data-role="{escape(role.lower())}">
                <div class="author-name">{escape(person)}</div>
                <div class="author-role">{escape(role)}</div>
                <div class="links">
        """
        
        # Add links only if they exist
        links_added = 0
        if clean_url(author_row.get("Website")):
            html_content += f'<a href="{clean_url(author_row.get("Website"))}" class="link-btn" target="_blank"><span>🌐</span>Website</a>'
            links_added += 1
        
        if clean_url(author_row.get("Goodreads Page")):
            html_content += f'<a href="{clean_url(author_row.get("Goodreads Page"))}" class="link-btn" target="_blank"><span>📚</span>Goodreads</a>'
            links_added += 1
        
        if clean_url(author_row.get("Amazon Page")):
            html_content += f'<a href="{clean_url(author_row.get("Amazon Page"))}" class="link-btn" target="_blank"><span>🛒</span>Amazon</a>'
            links_added += 1
        
        if clean_url(author_row.get("Audible Page")):
            html_content += f'<a href="{clean_url(author_row.get("Audible Page"))}" class="link-btn" target="_blank"><span>🎧</span>Audible</a>'
            links_added += 1
        
        if links_added == 0:
            html_content += '<div style="text-align: center; color: #999; font-style: italic;">Links coming soon!</div>'
        
        html_content += '</div>'
        
        # Add books section
        if books:
            html_content += f"""
                <div class="books-section">
                    <div class="books-toggle" onclick="toggleBooks('{clean_person}')">
                        📖 View Books ({len(books)})
                    </div>
                    <div id="books-{clean_person}" class="books-list">
            """
            
            for book in books:
                title = escape(str(book.get("Book Title", "Unknown Title")))
                series = escape(str(book.get("Series Title", "")))
                series_order = escape(str(book.get("Series Order", "")))
                published = escape(str(book.get("Published Date", "")))
                genre = escape(str(book.get("Genre", "")))
                
                series_info = ""
                if series and series != "nan":
                    series_info = f'<div class="book-series">📚 {series}'
                    if series_order and series_order != "nan":
                        series_info += f' #{series_order}'
                    series_info += '</div>'
                
                meta_info = []
                if published and published != "nan":
                    meta_info.append(f"📅 {published}")
                if genre and genre != "nan":
                    meta_info.append(f"🏷️ {genre}")
                
                meta_html = ""
                if meta_info:
                    meta_html = f'<div class="book-meta">{" • ".join(meta_info)}</div>'
                
                html_content += f"""
                    <div class="book-item">
                        <div class="book-title">{title}</div>
                        {series_info}
                        {meta_html}
                    </div>
                """
            
            html_content += """
                    </div>
                </div>
            """
        
        html_content += "</div>"
    
    html_content += f"""
        </div>
        
        <div class="footer">
            Compiled for Charm City Romanticon 2026 by Plot Twists & Pivot Tables
        </div>
    </div>
    
    <script>
        // Update stats
        document.getElementById('stats').innerHTML = `📊 {total_authors} Authors & Narrators • {total_books} Books`;
        
        function toggleBooks(author) {{
            const booksList = document.getElementById('books-' + author);
            booksList.classList.toggle('show');
        }}
        
        function searchAuthors() {{
            const searchTerm = document.querySelector('.search-input').value.toLowerCase();
            const cards = document.querySelectorAll('.author-card');
            let visibleCount = 0;
            
            cards.forEach(card => {{
                const name = card.dataset.name;
                const role = card.dataset.role;
                const isVisible = name.includes(searchTerm) || role.includes(searchTerm);
                
                if (isVisible) {{
                    card.classList.remove('hidden');
                    visibleCount++;
                }} else {{
                    card.classList.add('hidden');
                }}
            }});
            
            // Update stats
            if (searchTerm) {{
                document.getElementById('stats').innerHTML = `🔍 Showing ${{visibleCount}} results for "${{searchTerm}}"`;
            }} else {{
                document.getElementById('stats').innerHTML = `📊 {total_authors} Authors & Narrators • {total_books} Books`;
            }}
        }}
        
        // Add some smooth scrolling
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({{
                    behavior: 'smooth'
                }});
            }});
        }});
    </script>
</body>
</html>
    """
    
    # Save the HTML file
    with open("charm_city_romanticon_2026_backlists.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("✅ HTML Dashboard created: charm_city_romanticon_2026_backlists.html")
    print(f"   📊 {total_authors} authors/narrators with {total_books} total books")
    print("   🌐 Just double-click the file to open in your browser!")
    print("   📱 Works on desktop, tablet, and mobile")

# Create the beautiful HTML dashboard
create_html_dashboard()
print("\n🎉 Done! No more Excel drama - just pure HTML awesomeness!")