import re

def convert_content_to_html(content):
    # Product Name
    title_match = re.search(r"(?:\*\*?1\.|\b1\.)\s*\*?\*?SEO-optimized Product Name\**?:?\s*(.*)", content, re.IGNORECASE)
    product_name = title_match.group(1).strip() if title_match else "Product Name"

    # Short Description
    short_desc_match = re.search(r"(?:\*\*?2\.|\b2\.)\s*\*?\*?Short Description\**?:?\s*(.*)", content, re.IGNORECASE)
    short_desc = short_desc_match.group(1).strip() if short_desc_match else "No short description provided."

    # Long Description
    long_desc_match = re.search(r"(?:\*\*?3\.|\b3\.)\s*\*?\*?Long Description\**?:?\s*(.*)", content, re.IGNORECASE | re.DOTALL)
    long_desc_raw = long_desc_match.group(1).strip() if long_desc_match else ""

    # Bullet points — lines starting with * or -
    bullet_points = re.findall(r"^[\*\-]\s*(.+)", long_desc_raw, re.MULTILINE)

    # Remove bullet lines from long description text
    long_desc_text = re.sub(r"^[\*\-]\s*.+", "", long_desc_raw, flags=re.MULTILINE).strip()

    # Build HTML
    html_content = f"<h2>{product_name}</h2>\n"
    html_content += f"<p><strong>Short Description:</strong> {short_desc}</p>\n"
    html_content += f"<p><strong>Description:</strong></p>\n"

    if long_desc_text:
        paragraphs = [f"<p>{para.strip()}</p>" for para in long_desc_text.split('\n') if para.strip()]
        html_content += "\n".join(paragraphs) + "\n"

    if bullet_points:
        html_content += "<ul>\n"
        for point in bullet_points:
            html_content += f"  <li>{point.strip()}</li>\n"
        html_content += "</ul>\n"

    return html_content
