# full_pipeline.py (updated with new author detection)

import os
from scrape_goodreads_backlist import search_goodreads_author, scrape_goodreads_books
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
import time

# ----------------------- SCRAPE PHASE -----------------------
print("[1/2] Scraping Goodreads backlists...")

# Load authors from your real convention CSV
author_df = pd.read_csv("announced_authors.csv")
all_authors = author_df["Author Name"].dropna().tolist()

# Load existing scraped data if it exists
if os.path.exists("author_backlists_scraped.csv"):
    existing_data = pd.read_csv("author_backlists_scraped.csv")
    scraped_authors = existing_data["Author"].dropna().unique().tolist()
    print(f"Found existing scraped data. {len(scraped_authors)} authors already scraped.")
else:
    existing_data = pd.DataFrame()
    scraped_authors = []

# Determine which authors still need to be scraped
authors_to_scrape = [author for author in all_authors if author not in scraped_authors]

print(f"Authors to scrape: {authors_to_scrape}\n")

new_books = []
for author in authors_to_scrape:
    print(f"Scraping {author}...")
    author_url = search_goodreads_author(author)
    if author_url:
        books = scrape_goodreads_books(author_url)
        for book in books:
            book["Author"] = author
        new_books.extend(books)
    time.sleep(2)

# Merge new data with existing data
if new_books:
    new_data = pd.DataFrame(new_books)
    full_data = pd.concat([existing_data, new_data], ignore_index=True)
else:
    full_data = existing_data

# Save updated data
full_data.to_csv("author_backlists_scraped.csv", index=False)
print("Scraping complete. Data saved to author_backlists_scraped.csv\n")

# ----------------------- EXCEL BUILD PHASE -----------------------
print("[2/2] Building Excel dashboard...")

wb = Workbook()
default_sheet = wb.active
wb.remove(default_sheet)

dashboard = wb.create_sheet("Dashboard")
dashboard.append(["Author Name", "Link to Tab"])

hot_pink_fill = PatternFill(start_color="EC008C", end_color="EC008C", fill_type="solid")
black_font_bold = Font(color="000000", bold=True)
gray_fill = PatternFill(start_color="F7F7F7", end_color="F7F7F7", fill_type="solid")
thin_border = Border(
    left=Side(style='thin', color='000000'),
    right=Side(style='thin', color='000000'),
    top=Side(style='thin', color='000000'),
    bottom=Side(style='thin', color='000000')
)

headers = [
    "Book Title", "Series Title", "Series Order", "Published Date",
    "Formats Available", "Buy Links", "Rent Links", "Audiobook (Y/N)",
    "Narrators", "Kindle Unlimited (Y/N)", "Kobo+ (Y/N)",
    "Genre", "Standalone/Series", "Other Notes"
]

for author in full_data["Author"].dropna().unique():
    author_data = full_data[full_data["Author"] == author]
    tab_name = author if len(author) <= 31 else author[:28] + "..."
    ws = wb.create_sheet(tab_name)

    ws.merge_cells('A1:B1')
    ws['A1'] = f"Connect with {author}"
    ws['A1'].alignment = Alignment(horizontal='left')
    ws['A1'].font = black_font_bold
    ws['A1'].fill = hot_pink_fill

    for row in range(1, 5):
        ws[f'A{row}'].border = thin_border
        ws[f'B{row}'].border = thin_border
    ws['A2'] = "🌐 Website"
    ws['B2'] = ""
    ws['A3'] = "📚 Goodreads"
    ws['B3'] = ""
    ws['A4'] = "🛒 Amazon"
    ws['B4'] = ""

    ws.append([])
    ws.append([])
    ws.append(headers)

    for col_num, column_title in enumerate(headers, 1):
        cell = ws[f'{get_column_letter(col_num)}7']
        cell.font = black_font_bold
        cell.fill = hot_pink_fill
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border

    for idx, row_data in enumerate(author_data.itertuples(index=False), start=8):
        row_list = [
            row_data._1, row_data._2, row_data._3, row_data._4,
            row_data._0, "", "", "", "", "", "", "", "", ""
        ]
        ws.append(row_list)
        for col_num in range(1, len(headers)+1):
            cell = ws[f'{get_column_letter(col_num)}{idx}']
            if idx % 2 == 1:
                cell.fill = gray_fill
            cell.border = thin_border
            if col_num == 4:
                cell.number_format = 'MM/DD/YYYY'

    dashboard.append([author, f"='{tab_name}'!A1"])

for col in range(1, 3):
    cell = dashboard.cell(row=1, column=col)
    cell.fill = hot_pink_fill
    cell.font = black_font_bold
    cell.alignment = Alignment(horizontal='center')
    cell.border = thin_border

for row_idx in range(1, dashboard.max_row + 1):
    for col_idx in range(1, 3):
        dashboard.cell(row=row_idx, column=col_idx).border = thin_border

footer_row = dashboard.max_row + 3
footer_text = "Compiled for Charm City Romanticon 2026 by Plot Twists & Pivot Tables"
dashboard.merge_cells(start_row=footer_row, start_column=1, end_row=footer_row, end_column=2)
dashboard.cell(row=footer_row, column=1).value = footer_text
dashboard.cell(row=footer_row, column=1).alignment = Alignment(horizontal='center')
dashboard.cell(row=footer_row, column=1).font = Font(italic=True)

wb.save("author_backlist_final.xlsx")
print("Done! Your full event-ready Excel dashboard is ready: author_backlist_final.xlsx")
