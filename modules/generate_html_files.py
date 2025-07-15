import pandas as pd
import os
from content_formatter import convert_content_to_html
import re

def safe_filename(name, max_length=50):
    """Remove problematic characters for Windows filenames."""
    name = re.sub(r'[<>:"/\\|?*\n\r\t]', '', name)
    name = re.sub(r'\s+', ' ', name)
    return name.strip()[:max_length]

def generate_html_files(excel_file="data/product_listing.xlsx", output_dir="data/html_descriptions"):
    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_excel(excel_file)

    for idx, row in df.iterrows():
        product_title = row["post_title"]
        content_text = row["post_content"]

        html_content = convert_content_to_html(content_text)

        filename = safe_filename(product_title) + ".html"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"✅ Saved HTML: {filepath}")

if __name__ == "__main__":
    generate_html_files()
