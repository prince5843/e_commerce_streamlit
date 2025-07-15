import pandas as pd
import os
import re

# --- Category and Brand Extraction Helpers ---
CATEGORY_KEYWORDS = {
    'electronics': ['laptop', 'phone', 'mobile', 'tablet', 'camera', 'headphone', 'earbud', 'tv', 'television', 'monitor', 'printer', 'router', 'mouse', 'keyboard', 'controller', 'smartwatch', 'speaker', 'charger', 'power bank', 'ssd', 'hdd', 'hard disk', 'graphics card', 'processor', 'cpu', 'ram', 'memory', 'motherboard', 'gadget'],
    'fashion': ['shirt', 'jeans', 't-shirt', 'dress', 'jacket', 'shoes', 'sneaker', 'sandal', 'kurta', 'saree', 'lehenga', 'skirt', 'trouser', 'pant', 'shorts', 'blouse', 'top', 'suit', 'hoodie', 'sweater', 'coat', 'boot', 'cap', 'hat', 'belt', 'watch', 'bag', 'wallet'],
    'food': ['chocolate', 'biscuit', 'snack', 'juice', 'beverage', 'cookie', 'candy', 'sweet', 'cake', 'bread', 'noodle', 'pasta', 'rice', 'oil', 'spice', 'tea', 'coffee', 'milk', 'cheese', 'butter', 'ghee', 'honey', 'jam', 'pickle', 'sauce', 'chips', 'namkeen'],
    'sports': ['football', 'cricket', 'bat', 'ball', 'racket', 'racquet', 'shuttle', 'badminton', 'tennis', 'basketball', 'volleyball', 'skate', 'cycle', 'bicycle', 'dumbbell', 'treadmill', 'yoga', 'mat', 'fitness', 'gym', 'jersey', 'kit', 'glove', 'helmet'],
    'home': ['sofa', 'bed', 'pillow', 'blanket', 'curtain', 'lamp', 'light', 'fan', 'table', 'chair', 'cushion', 'mattress', 'sheet', 'towel', 'carpet', 'rug', 'cookware', 'utensil', 'mug', 'cup', 'bottle', 'plate', 'bowl', 'pan', 'pot', 'stove', 'oven', 'mixer', 'grinder', 'toaster', 'kettle'],
    'beauty': ['cream', 'lotion', 'perfume', 'deodorant', 'shampoo', 'conditioner', 'soap', 'face wash', 'lipstick', 'makeup', 'cosmetic', 'nail', 'hair oil', 'serum', 'gel', 'moisturizer', 'sunscreen', 'razor', 'trimmer'],
    'automotive': ['car', 'bike', 'motorcycle', 'scooter', 'helmet', 'tyre', 'tire', 'engine', 'seat cover', 'wiper', 'battery', 'horn', 'mirror', 'indicator', 'headlight', 'tail light', 'mat', 'accessory'],
}

# Example brand list (expand as needed)
BRAND_KEYWORDS = [
    'apple', 'samsung', 'sony', 'hp', 'dell', 'lenovo', 'asus', 'acer', 'motorola', 'xiaomi', 'oneplus', 'realme', 'oppo', 'vivo', 'boat', 'jbl', 'philips', 'panasonic', 'lg', 'mi', 'nokia', 'cosco', 'nike', 'adidas', 'puma', 'reebok', 'levis', 'zara', 'h&m', 'allen solly', 'bata', 'woodland', 'pepe', 'wrangler', 'van heusen', 'fossil', 'casio', 'timex', 'titan', 'fastrack', 'redmi', 'intex', 'voltas', 'whirlpool', 'godrej', 'prestige', 'usha', 'bajaj', 'hero', 'honda', 'maruti', 'tata', 'mahindra', 'hyundai', 'ford', 'toyota', 'kia', 'mg', 'royal enfield', 'skoda', 'renault', 'chevrolet', 'fiat', 'jeep', 'mercedes', 'bmw', 'audi', 'volkswagen', 'jaguar', 'land rover', 'tesla', 'bosch', 'honeywell', 'colgate', 'dabur', 'amul', 'britannia', 'parle', 'cadbury', 'nestle', 'lays', 'haldiram', 'bingo', 'balaji', 'fortune', 'saffola', 'mtr', 'mdh', 'everest', 'catch', 'tata salt', 'patanjali', 'gillette', 'nivea', 'garnier', 'maybelline', 'lakme', 'lotus', 'biotique', 'himalaya', 'vlcc', 'wow', 'mamaearth', 'beardo', 'veet', 'set wet', 'park avenue', 'wild stone', 'engage', 'axe', 'old spice', 'rexona', 'dove', 'pears', 'lux', 'lifebuoy', 'cinthol', 'medimix', 'himalaya', 'fiama', 'pantene', 'head & shoulders', 'clinic plus', 'sunsilk', 'tresemme', 'loreal', 'matrix', 'schwarzkopf', 'streax', 'indulekha', 'parachute', 'vaseline', 'ponds', 'fair & lovely', 'fair and lovely', 'joy', 'johnson', 'johnson & johnson', 'johnson and johnson', 'mamaearth', 'wow', 'forest essentials', 'the body shop', 'nykaa', 'purplle', 'sugar', 'colorbar', 'faces', 'blue heaven', 'insight', 'swiss beauty', 'miss claire', 'wet n wild',
]


def extract_short_description(content):
    # Try to find text between "Short Description" and "Long Description" headings
    match = re.search(r"Short Description\**\s*(.*?)\n\s*(?=\*\*3|Long Description|\n)", content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    else:
        return "No short description found"


def extract_category(title):
    title_lower = title.lower()
    matches = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in title_lower:
                matches.append((category, kw))
    if matches:
        # Prefer the category with the longest keyword match
        best = max(matches, key=lambda x: len(x[1]))
        return best[0].capitalize()
    return "Other"

def extract_brand(title):
    title_lower = title.lower()
    for brand in BRAND_KEYWORDS:
        if brand in title_lower:
            return brand.capitalize()
    # Fallback: first word (capitalized)
    return title.split()[0].capitalize() if title else "Unknown"


def export_to_excel(data, images, output_file="data/product_listing.xlsx"):
    """
    Appends product and content data into an Excel file (WooCommerce import-ready)
    """

    # Extract short description from AI content
    short_description = extract_short_description(data["generated_content"])

    # Fallback for missing part_code
    part_code = data["product_data"]["sku"] if data["product_data"]["sku"] else "Not Available"

    # --- Prefer structured brand/category if available ---
    product_title = data["product_data"]["title"]
    scraped_category = data["product_data"].get("category")
    # Only use scraped category if it matches known categories
    if scraped_category and scraped_category.lower() in CATEGORY_KEYWORDS:
        product_category = scraped_category.capitalize()
    else:
        product_category = extract_category(product_title)
    product_brand = data["product_data"].get("brand")
    if not product_brand:
        product_brand = extract_brand(product_title)

    # Prepare final data row
    new_row = {
        "post_title": product_title,
        "short_description": short_description,
        "post_content": data["generated_content"],
        "part_code": part_code,
        "_regular_price": data["product_data"]["price"] if data["product_data"]["price"] else "Not Available",
        "_product_image_gallery": "|".join(images),
        "_featured_image": images[0] if images else "",
        "product_category": product_category,
        "product_tags": product_brand
    }

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # If file exists, append; else, create new
    if os.path.exists(output_file):
        df = pd.read_excel(output_file)
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    else:
        df = pd.DataFrame([new_row])

    df.to_excel(output_file, index=False)
    print(f"\n✅ Excel file updated at {output_file}")


