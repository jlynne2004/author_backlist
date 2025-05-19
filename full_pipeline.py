# full_pipeline.py (updated with new author detection)

import os
from scrape_goodreads_backlist import search_goodreads_author, scrape_goodreads_books
import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
import time

# ----------------------- SCRAPE PHASE -----------------------
print("[1/2] Scraping Goodreads backlists...")

# Load authors from your real convention CSV
wb = load_workbook("announced_authors.xlsx")
ws = wb.active

data = []
for row in ws.iter_rows(min_row=2, values_only=False):
    author = row[0].value
    role = row[1].value
    other_names = row[2].value
    website = row[3].hyperlink.target if row[3].hyperlink else ""
    goodreads = row[4].hyperlink.target if row[4].hyperlink else ""
    amazon = row[5].hyperlink.target if row[5].hyperlink else ""
    audible = row[6].hyperlink.target if row[6].hyperlink else ""
    data.append({"Author Name": author, "Role": role, "Other Names": other_names, "Website": website, "Goodreads Page": goodreads, "Amazon Page": amazon, "Audible Page": audible})

author_df = pd.DataFrame(data)

# Load existing scraped data if it exists
if os.path.exists("author_backlists_scraped.xlsx"):
    existing_data = pd.read_xlsx("author_backlists_scraped.xlsx")
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
full_data.to_xlsx("author_backlists_scraped.xlsx", index=False)
print("Scraping complete. Data saved to author_backlists_scraped.csv\n")

# ----------------------- EXCEL BUILD PHASE -----------------------
print("[2/2] Building Excel dashboard...")

wb = Workbook()
default_sheet = wb.active
wb.remove(default_sheet)

dashboard = wb.create_sheet("Dashboard")
dashboard.append(["Author", "Role", "Link"])

hot_pink_fill = PatternFill(start_color="EC008C", end_color="EC008C", fill_type="solid")
black_font_bold = Font(color="000000", bold=True)
gray_fill = PatternFill(start_color="F7F7F7", end_color="F7F7F7", fill_type="solid")
thin_border = Border(
    left=Side(style='thin', color='000000'),
    right=Side(style='thin', color='000000'),
    top=Side(style='thin', color='000000'),
    bottom=Side(style='thin', color='000000')
)

if role == "Narrator":
    headers = [
        "Narrator","Book Title", "Series Title", "Author","Series Order", "Published Date",
        "Genre", "Standalone/Series", "Other Notes", "Audiobook (Y/N)", 
        "Kindle Unlimited (Y/N)", "Kobo+ (Y/N)", 
    ]
    if pen_name:
        headers.append("Pen Name")
else:
    headers = [
        "Author", "Book Title", "Series Title", "Series Order", "Published Date",
        "Formats Available", "Buy Links", "Rent Links", "Audiobook (Y/N)",
        "Narrators", "Kindle Unlimited (Y/N)", "Kobo+ (Y/N)",
        "Genre", "Standalone/Series", "Other Notes", "Pen Name"
    ]
    if pen_name:
        headers.append("Pen Name")


def clean_url(value: str) -> str:
    """
    Clean up a URL by adding the HTTPS protocol if it's not already there.

    Args:
        value (str): The URL to clean up.

    Returns:
        str: The cleaned up URL.
    """
    value = str(value).strip()
    if value.lower() == "nan":
        return ""  # Return empty string if value is NaN
    elif value.startswith("https://") or value.startswith("http://"):
        return value  # Return the value as is if it already has a protocol
    else:
        return "https://" + value  # Add HTTPS protocol if it's not already there

for person in full_data["Author"].dropna().unique():
    person_data = full_data[full_data["Author"].str.lower() == person.lower()]
    role =  person_data["Role"].iloc[0] if "Role" in person_data else "Author"
    author_row = author_df[author_df["Author Name"] == person].iloc[0]
    website_url = clean_url(author_row.get("Website", ""))
    goodreads_url = clean_url(author_row.get("Goodreads Page", ""))
    amazon_url = clean_url(author_row.get("Amazon Page", ""))
    audible_url = clean_url(author_row.get("Audible Page", ""))
    tab_name = person if len(person) <= 31 else person[:28] + "..."
    dashboard.append([person, role, f'=HYPERLINK("#{tab_name}!A1", "Go To Tab")'])
    ws = wb.create_sheet(tab_name)

    ws.merge_cells('A1:B1')
    ws['A1'] = f"Connect with {person}"
    ws['A1'].alignment = Alignment(horizontal='left')
    ws['A1'].font = black_font_bold
    ws['A1'].fill = hot_pink_fill

    for row in range(1, 5):
        ws[f'A{row}'].border = thin_border
        ws[f'B{row}'].border = thin_border
    ws["A2"] = "🌐 Website"
    ws["B2"].value = "Author Website"
    ws["B2"].hyperlink = website_url
    ws["B2"].style = "Hyperlink"

    ws["A3"] = "📚 Goodreads"
    ws["B3"].value = "Goodreads Page"
    ws["B3"].hyperlink = goodreads_url
    ws["B3"].style = "Hyperlink"

    ws["A4"] = "🛒 Amazon"
    ws["B4"].value = "Amazon Page"
    ws["B4"].hyperlink = amazon_url
    ws["B4"].style = "Hyperlink"

    ws["A5"] = "🎧 Audible"
    ws["B5"].value = "Audible Page"
    ws["B5"].hyperlink = audible_url
    ws["B5"].style = "Hyperlink"


    ws.append([])
    ws.append([])
    ws.append(headers)

    for col_num, column_title in enumerate(headers, 1):
        cell = ws[f'{get_column_letter(col_num)}7']
        cell.font = black_font_bold
        cell.fill = hot_pink_fill
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border

    for idx, row_data in person_data.iterrows():
        person_name = person.strip().lower()
        narrators_raw = row_data.get("Narrators", "")
        narrators = str(narrators_raw).lower()
        if narrators == "nan":
            narrators = ""

        if person_name in narrators and role.lower() == "author":
            book_role = "Author & Narrator"
        elif person_name in narrators:
            book_role = "Narrator"
        else:
            book_role = "Author"

    row_list = [
        row_data.get("Author", "") if role != "Narrator" else row_data.get("Narrator", ""),
        row_data.get("Book Title", ""),
        row_data.get("Series Title", ""),
        row_data.get("Series Order", ""),
        row_data.get("Published Date", ""),
        row_data.get("Formats Available", ""),
        row_data.get("Buy Links", ""),
        row_data.get("Rent Links", ""),
        row_data.get("Audiobook (Y/N)", ""),
        row_data.get("Narrators", ""),
        row_data.get("Kindle Unlimited (Y/N)", ""),
        row_data.get("Kobo+ (Y/N)", ""),
        row_data.get("Genre", ""),
        row_data.get("Standalone/Series", ""),
        row_data.get("Other Notes", ""),
        row_data.get("Pen Name", "") if row_data.get("Pen Name","") != row_data.get("Author", "") else ""
    ]

    ws.append(row_list)

    for col_num in range(1, len(headers) + 1):
        cell = ws[f"{get_column_letter(col_num)}{idx + 1}"]
        if idx % 2 == 1:
            cell.fill = gray_fill
        cell.border = thin_border
        if col_num == 5:  # Published Date column
            cell.number_format = "MM/DD/YYYY"


    dashboard.append([person, role, f'=HYPERLINK("#{tab_name}!A1", "Go To Tab")'])

for col in range(1, 4):
    cell = dashboard.cell(row=1, column=col)
    cell.fill = hot_pink_fill
    cell.font = black_font_bold
    cell.alignment = Alignment(horizontal='center')
    cell.border = thin_border

for row_idx in range(1, dashboard.max_row + 1):
    for col_idx in range(1, 4):
        dashboard.cell(row=row_idx, column=col_idx).border = thin_border

# Add support message to the right of the dashboard table
support_col = 5
support_row = 2
support_message = (
    "💡 Support Authors Directly\n"
    "Whenever possible, consider purchasing books directly from the author's website if they have a store.\n"
    "Amazon takes a significant portion of royalties and can penalize authors for piracy and other issues beyond their control — even removing their accounts.\n\n"
    "We understand that Amazon is convenient and affordable, and authors still rely on it.\n"
    "But every direct purchase makes a bigger impact. 💖"
)

for i, line in enumerate(support_message.split("\n")):
    cell = dashboard.cell(row=support_row + i, column=support_col)
    cell.value = line
    cell.alignment = Alignment(wrap_text=True, vertical='top', horizontal='left')
    cell.font = Font(italic=True)

# Add a footer message
footer_row = dashboard.max_row + 3
footer_text = "Compiled for Charm City Romanticon 2026 by Plot Twists & Pivot Tables"
dashboard.merge_cells(start_row=footer_row, start_column=1, end_row=footer_row, end_column=2)
dashboard.cell(row=footer_row, column=1).value = footer_text
dashboard.cell(row=footer_row, column=1).alignment = Alignment(horizontal='center')
dashboard.cell(row=footer_row, column=1).font = Font(italic=True)

wb.save("author_backlist_final.xlsx")
print("Done! Your full event-ready Excel dashboard is ready: author_backlist_final.xlsx")
