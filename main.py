from modules.scraper import scrape_product_data
from modules.content_generator import generate_product_content
from modules.image_processor import download_and_optimize_images
from modules.excel_exporter import export_to_excel, extract_short_description, extract_category, extract_brand, CATEGORY_KEYWORDS
from modules.content_formatter import convert_content_to_html
from modules.drive_uploader import authenticate_drive
from playwright.sync_api import sync_playwright
import os
import pandas as pd
import requests
import re

# Set your Google Drive parent folder ID here (the one you provided)
GOOGLE_DRIVE_PARENT_FOLDER_ID = "1HDtj__UkZC8fOkhqkpc-53-Y9ClxlswI"

TOGETHER_API_KEY = "59c00bb34ce46908ead205258a034bc7e2c796a36459838bd1de0c621100db62"  # <-- Set your Together.ai API key here

def get_product_urls_progressive(product_name):
    site_sets = [
        (["amazon.in", "flipkart.com", "croma.com", "reliancedigital.in", "tatacliq.com", "vijaysales.com", "snapdeal.com", "paytmmall.com", "shopclues.com", "myntra.com", "ajio.com", "nykaa.com"],
         "Amazon India (amazon.in), Flipkart (flipkart.com), Croma (croma.com), Reliance Digital (reliancedigital.in), TataCliq (tatacliq.com), Vijay Sales (vijaysales.com), Snapdeal (snapdeal.com), Paytm Mall (paytmmall.com), ShopClues (shopclues.com), Myntra (myntra.com), AJIO (ajio.com), and Nykaa (nykaa.com)", 6),
        (["amazon.in", "flipkart.com", "croma.com", "reliancedigital.in", "tatacliq.com", "vijaysales.com", "snapdeal.com", "paytmmall.com", "shopclues.com"],
         "Amazon India (amazon.in), Flipkart (flipkart.com), Croma (croma.com), Reliance Digital (reliancedigital.in), TataCliq (tatacliq.com), Vijay Sales (vijaysales.com), Snapdeal (snapdeal.com), Paytm Mall (paytmmall.com), and ShopClues (shopclues.com)", 4),
        ([], "any reputable e-commerce or online store", 3)
    ]
    global_seen = set()
    all_unique_urls = []
    for allowed_domains, site_text, required_count in site_sets:
        prompt = (
            f"You are an expert online shopping assistant. Given the product name: \"{product_name}\", "
            f"find direct product page URLs from {site_text}.\n\n"
            "Requirements:\n"
            "- Only include direct product page URLs (no search, category, or home pages).\n"
        )
        if allowed_domains:
            prompt += "- Only include links from the specified sites.\n"
        prompt += (
            "- Each URL should be on its own line, with no extra text or explanation.\n"
            "- Do not include duplicate URLs.\n"
            "- Prefer the most popular or best-matching products for the given product name.\n\n"
            f"Product name: {product_name}\n"
            "List the URLs below:"
        )
        response = requests.post(
            "https://api.together.xyz/v1/completions",
            headers={"Authorization": f"Bearer {TOGETHER_API_KEY}"},
            json={
                "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
                "prompt": prompt,
                "max_tokens": 512,
                "temperature": 0.2,
                "stop": None,
            },
            timeout=60
        )
        result = response.json()
        text = result["choices"][0]["text"]
        urls = re.findall(r'https?://[^\s]+', text)
        if allowed_domains:
            urls = [url for url in urls if any(domain in url for domain in allowed_domains)]
        # Remove duplicates across all attempts
        for url in urls:
            url_norm = url.rstrip('/').split('?')[0]
            if url_norm not in global_seen:
                all_unique_urls.append(url)
                global_seen.add(url_norm)
        if len(all_unique_urls) >= required_count:
            return all_unique_urls[:required_count]
    # If all else fails, return whatever was found last (up to 3)
    return all_unique_urls[:3]

def get_product_urls_serpapi(product_name, num_results=4):
    api_key = "2884467bdf873a4bdb1ec01a22d864ec8ed0e4927df3fd6eff917868c1bb3e8f"
    search_url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": product_name,
        "api_key": api_key,
        "num": 20,  # Fetch more results to increase chances of getting different domains
        "hl": "en",
        "gl": "in"
    }
    response = requests.get(search_url, params=params)
    response.raise_for_status()
    results = response.json()
    urls = []
    found_domains = set()
    allowed_domains = [
        "amazon.in", "flipkart.com", "croma.com", "reliancedigital.in", "tatacliq.com", "vijaysales.com", 
        "snapdeal.com", "paytmmall.com", "shopclues.com", "myntra.com", "ajio.com", "nykaa.com"
    ]
    for result in results.get("organic_results", []):
        link = result.get("link")
        if link:
            for domain in allowed_domains:
                if domain in link and domain not in found_domains:
                    # For Flipkart, only accept direct product URLs
                    if domain == "flipkart.com" and "/p/" not in link:
                        continue
                    urls.append(link)
                    found_domains.add(domain)
                    break
        if len(urls) >= num_results:
            break
    return urls

def get_product_links(product_name, num_results=7):
    query = f"{product_name}"
    links = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"https://www.google.com/search?q={query.replace(' ', '+')}")
        page.wait_for_timeout(3000)
        results = page.locator("a:visible")
        print("\n[DEBUG] All hrefs found on the page:")
        for i in range(results.count()):
            link = results.nth(i).get_attribute("href")
            if link:
                print(link)
            if link and link.startswith("http"):
                if any(domain in link for domain in ["amazon.in", "flipkart.com", "croma.com", "reliancedigital.in", "tatacliq.com", "vijaysales.com", 
                                                "snapdeal.com", "paytmmall.com", "shopclues.com", "myntra.com", "ajio.com", "nykaa.com"]):
                    if link not in links:
                        links.append(link)
            if len(links) >= num_results:
                break
        browser.close()
    return links

def get_brand_and_category_llm(product_title):
    prompt = (
        f'Given the product: "{product_title}", what is the most likely brand and category for this product?\n'
        "Respond in the format:\nBrand: <brand>\nCategory: <category>"
    )
    response = requests.post(
        "https://api.together.xyz/v1/completions",
        headers={"Authorization": f"Bearer {TOGETHER_API_KEY}"},
        json={
            "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            "prompt": prompt,
            "max_tokens": 50,
            "temperature": 0.1,
            "stop": None,
        },
        timeout=30
    )
    result = response.json()
    if "choices" not in result or not result["choices"]:
        print("Together API error or empty response:", result)
        return "", ""
    text = result["choices"][0]["text"]
    brand = ""
    category = ""
    for line in text.splitlines():
        if line.lower().startswith("brand:"):
            brand = line.split(":", 1)[-1].strip()
        if line.lower().startswith("category:"):
            category = line.split(":", 1)[-1].strip()
    return brand, category

def get_brand_category_serpapi(product_title):
    api_key = "8b2762e078b582428e61322daf9ac36b40181c0603bce9b7d4854d5e3a27f501"
    params = {
        "engine": "google_shopping",
        "q": product_title,
        "api_key": api_key,
        "hl": "en",
        "gl": "in"
    }
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=20)
        if response.status_code != 200:
            return "", ""
        data = response.json()
        shopping_results = data.get("shopping_results", [])
        if shopping_results:
            product = shopping_results[0]
            brand = product.get("brand", "")
            category = product.get("category", "")
            return brand, category
    except Exception:
        pass
    return "", ""

def process_product(url, drive=None, parent_folder_id=None):
    print("\n🔍 Scraping product data...")
    product_data = scrape_product_data(url)
    if not product_data:
        print("❌ Failed to scrape product data. Exiting.")
        return
    product_title = product_data["title"]
    # --- Hybrid brand/category extraction ---
    brand = product_data.get("brand", "")
    category = product_data.get("category", "")
    if not brand or brand.lower() in ["", "unknown", "brand"]:
        serpapi_brand, _ = get_brand_category_serpapi(product_title)
        if serpapi_brand:
            brand = serpapi_brand
        else:
            brand, _ = get_brand_and_category_llm(product_title)
    if not category or category.lower() in ["", "unknown", "category"]:
        _, serpapi_category = get_brand_category_serpapi(product_title)
        if serpapi_category:
            category = serpapi_category
        else:
            _, category = get_brand_and_category_llm(product_title)
    product_data["brand"] = brand
    product_data["category"] = category
    print("\n✅ Scraped Product Data:")
    print(product_data)
    print("\nExtracted image URLs:")
    print(product_data.get("image_urls", []))

    print("\n✍️ Generating AI product content...")
    generated_content = generate_product_content(product_title)
    print("\n✅ AI-Generated Content (Plain Text):")
    print(generated_content)

    print("\n🔀 Converting AI Content to HTML format...")
    html_format = convert_content_to_html(generated_content)
    print("\n✅ HTML Formatted Content:")
    print(html_format)

    print("\n📸 Downloading and optimizing images...")
    saved_images = download_and_optimize_images(
        product_data.get("image_urls", []),
        product_title,
        drive=drive,
        parent_folder_id=parent_folder_id
    )
    print("\n✅ Images Saved:")
    print(saved_images)

    print("\n📊 Exporting everything to Excel (with HTML content)...")
    final_result = {
        "product_data": product_data,
        "generated_content": html_format
    }
    export_to_excel(final_result, saved_images)

    print("\n🎉 Product listing completed successfully!")

def process_products_from_excel(excel_path, drive=None, parent_folder_id=None):
    print(f"\n📥 Reading URLs from: {excel_path}")
    df = pd.read_excel(excel_path)
    url_col = None
    for col in df.columns:
        if 'url' in col.lower():
            url_col = col
            break
    if url_col is None:
        print("❌ No URL column found in the Excel file. Please ensure a column contains 'url' in its header.")
        return
    urls = df[url_col].dropna().unique()
    print(f"Found {len(urls)} URLs. Starting batch processing...")
    output_rows = []
    for idx, url in enumerate(urls, 1):
        print(f"\n--- Processing {idx}/{len(urls)}: {url} ---")
        try:
            product_data = scrape_product_data(url)
            if not product_data:
                print(f"❌ Failed to scrape product data for {url}. Skipping.")
                continue
            product_title = product_data["title"]
            # --- Hybrid brand/category extraction ---
            brand = product_data.get("brand", "")
            category = product_data.get("category", "")
            if not brand or brand.lower() in ["", "unknown", "brand"]:
                serpapi_brand, _ = get_brand_category_serpapi(product_title)
                if serpapi_brand:
                    brand = serpapi_brand
                else:
                    brand, _ = get_brand_and_category_llm(product_title)
            if not category or category.lower() in ["", "unknown", "category"]:
                _, serpapi_category = get_brand_category_serpapi(product_title)
                if serpapi_category:
                    category = serpapi_category
                else:
                    _, category = get_brand_and_category_llm(product_title)
            product_data["brand"] = brand
            product_data["category"] = category
            generated_content = generate_product_content(product_title)
            html_format = convert_content_to_html(generated_content)
            saved_images = download_and_optimize_images(
                product_data.get("image_urls", []),
                product_title,
                drive=drive,
                parent_folder_id=parent_folder_id
            )
            short_description = extract_short_description(html_format)
            part_code = product_data["sku"] if product_data.get("sku") else "Not Available"
            scraped_category = product_data.get("category")
            if scraped_category and scraped_category.lower() in CATEGORY_KEYWORDS:
                product_category = scraped_category.capitalize()
            else:
                product_category = extract_category(product_title)
            product_brand = product_data.get("brand")
            if not product_brand:
                product_brand = extract_brand(product_title)
            new_row = {
                "post_title": product_title,
                "short_description": short_description,
                "post_content": html_format,
                "part_code": part_code,
                "_regular_price": product_data["price"] if product_data["price"] else "Not Available",
                "_product_image_gallery": "|".join(saved_images),
                "_featured_image": saved_images[0] if saved_images else "",
                "product_category": product_category,
                "product_tags": product_brand
            }
            output_rows.append(new_row)
        except Exception as e:
            print(f"❌ Error processing {url}: {e}")
    if output_rows:
        out_df = pd.DataFrame(output_rows)
        os.makedirs("data", exist_ok=True)
        out_df.to_excel("data/product_listing.xlsx", index=False)
        print("\n✅ Batch processing complete! Output written to data/product_listing.xlsx")
    else:
        print("❌ No products were successfully processed.")

if __name__ == "__main__":
    print("🛒 E-Commerce Listing Automation System 🛒") 

    # Authenticate Google Drive at start
    drive = authenticate_drive()
    parent_folder_id = GOOGLE_DRIVE_PARENT_FOLDER_ID

    print("\nChoose an option:")
    print("1. Search for product links by name (LLM-powered)")
    print("2. Directly paste a product page URL")
    print("3. Batch process product URLs from Excel file")
    choice = input("\n👉 Enter 1, 2, or 3: ").strip()

    if choice == "1":
        product_name = input("Enter product name: ").strip()
        candidate_urls = get_product_urls_serpapi(product_name, num_results=10)  # get more candidates
        if not candidate_urls:
            print("\n❌ No product links found. Try a different product name.")
            exit()
        print("\n🔗 Candidate product page URLs:")
        for idx, url in enumerate(candidate_urls, start=1):
            print(f"{idx}. {url}")
        print("\n➡️ Scraping up to 4 working product URLs from different sites...")
        output_rows = []
        used_domains = set()
        max_attempts = 20  # Increase attempts to ensure we get 4 different sites
        attempted_urls = set()
        
        # First pass: try all candidate URLs
        for url in candidate_urls:
            if len(output_rows) >= 4:
                break
            domain = None
            for d in ["amazon.in", "flipkart.com", "croma.com", "reliancedigital.in", "tatacliq.com", "vijaysales.com", 
                      "snapdeal.com", "paytmmall.com", "shopclues.com", "myntra.com", "ajio.com", "nykaa.com"]:
                if d in url:
                    domain = d
                    break
            if not domain or domain in used_domains:
                continue
            print(f"\n--- Attempting: {url} ---")
            try:
                product_data = scrape_product_data(url)
                # Check for access denied or missing data
                if (not product_data or not product_data.get("title") or
                    "access denied" in product_data.get("title", "").lower() or
                    product_data.get("title", "").strip() == "Access Denied"):
                    print(f"❌ Access denied or invalid data for {url}. Skipping.")
                    attempted_urls.add(url)
                    continue
                product_title = product_data["title"]
                generated_content = generate_product_content(product_title)
                html_format = convert_content_to_html(generated_content)
                saved_images = download_and_optimize_images(
                    product_data.get("image_urls", []),
                    product_title,
                    drive=drive,
                    parent_folder_id=parent_folder_id
                )
                short_description = extract_short_description(html_format)
                part_code = product_data["sku"] if product_data.get("sku") else "Not Available"
                scraped_category = product_data.get("category")
                if scraped_category and scraped_category.lower() in CATEGORY_KEYWORDS:
                    product_category = scraped_category.capitalize()
                else:
                    product_category = extract_category(product_title)
                product_brand = product_data.get("brand")
                if not product_brand:
                    product_brand = extract_brand(product_title)
                new_row = {
                    "post_title": product_title,
                    "short_description": short_description,
                    "post_content": html_format,
                    "part_code": part_code,
                    "_regular_price": product_data["price"] if product_data["price"] else "Not Available",
                    "_product_image_gallery": "|".join(saved_images),
                    "_featured_image": saved_images[0] if saved_images else "",
                    "product_category": product_category,
                    "product_tags": product_brand
                }
                output_rows.append(new_row)
                used_domains.add(domain)
                print(f"✅ Successfully scraped from {domain}")
            except Exception as e:
                print(f"❌ Error processing {url}: {e}")
                attempted_urls.add(url)
        
        # Second pass: if we don't have 4 sites, try additional websites
        if len(output_rows) < 4:
            print(f"\n⚠️ Only got {len(output_rows)} sites. Trying additional websites...")
            additional_domains = [
                "bigbasket.com", "grofers.com", "dunzo.com", "swiggy.in", "zomato.com",
                "bookmyshow.com", "cleartrip.com", "makemytrip.com", "goibibo.com",
                "urbancompany.com", "firstcry.com", "babyoye.com", "kidsstop.in"
            ]
            
            # Try to find URLs for additional domains
            for additional_domain in additional_domains:
                if len(output_rows) >= 4:
                    break
                if additional_domain in used_domains:
                    continue
                    
                print(f"\n🔍 Searching for {additional_domain}...")
                try:
                    # Use SerpAPI to find product URLs for this domain
                    search_params = {
                        "engine": "google",
                        "q": f"{product_name} site:{additional_domain}",
                        "api_key": "2884467bdf873a4bdb1ec01a22d864ec8ed0e4927df3fd6eff917868c1bb3e8f",
                        "num": 5,
                        "hl": "en",
                        "gl": "in"
                    }
                    response = requests.get("https://serpapi.com/search", params=search_params, timeout=20)
                    if response.status_code == 200:
                        results = response.json()
                        for result in results.get("organic_results", []):
                            url = result.get("link")
                            if url and additional_domain in url and url not in attempted_urls:
                                print(f"\n--- Attempting additional site: {url} ---")
                                try:
                                    product_data = scrape_product_data(url)
                                    if (not product_data or not product_data.get("title") or
                                        "access denied" in product_data.get("title", "").lower() or
                                        product_data.get("title", "").strip() == "Access Denied"):
                                        print(f"❌ Access denied or invalid data for {url}. Skipping.")
                                        attempted_urls.add(url)
                                        continue
                                        
                                    product_title = product_data["title"]
                                    generated_content = generate_product_content(product_title)
                                    html_format = convert_content_to_html(generated_content)
                                    saved_images = download_and_optimize_images(
                                        product_data.get("image_urls", []),
                                        product_title,
                                        drive=drive,
                                        parent_folder_id=parent_folder_id
                                    )
                                    short_description = extract_short_description(html_format)
                                    part_code = product_data["sku"] if product_data.get("sku") else "Not Available"
                                    scraped_category = product_data.get("category")
                                    if scraped_category and scraped_category.lower() in CATEGORY_KEYWORDS:
                                        product_category = scraped_category.capitalize()
                                    else:
                                        product_category = extract_category(product_title)
                                    product_brand = product_data.get("brand")
                                    if not product_brand:
                                        product_brand = extract_brand(product_title)
                                    new_row = {
                                        "post_title": product_title,
                                        "short_description": short_description,
                                        "post_content": html_format,
                                        "part_code": part_code,
                                        "_regular_price": product_data["price"] if product_data["price"] else "Not Available",
                                        "_product_image_gallery": "|".join(saved_images),
                                        "_featured_image": saved_images[0] if saved_images else "",
                                        "product_category": product_category,
                                        "product_tags": product_brand
                                    }
                                    output_rows.append(new_row)
                                    used_domains.add(additional_domain)
                                    print(f"✅ Successfully scraped from {additional_domain}")
                                    break  # Found one from this domain, move to next
                                except Exception as e:
                                    print(f"❌ Error processing {url}: {e}")
                                    attempted_urls.add(url)
                except Exception as e:
                    print(f"❌ Error searching {additional_domain}: {e}")
                    continue
        if output_rows:
            output_file = "data/product_listing.xlsx"
            if os.path.exists(output_file):
                existing_df = pd.read_excel(output_file)
                new_df = pd.DataFrame(output_rows)
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            else:
                combined_df = pd.DataFrame(output_rows)
            os.makedirs("data", exist_ok=True)
            combined_df.to_excel(output_file, index=False)
            print("\n✅ SerpAPI product search complete! Output written to data/product_listing.xlsx")
        else:
            print("❌ No products were successfully processed.")

    elif choice == "2":
        selected_url = input("Paste full product page URL: ").strip()
        print(f"\n➡️ You selected: {selected_url}")
        process_product(selected_url, drive=drive, parent_folder_id=parent_folder_id)

    elif choice == "3":
        excel_path = input("Enter path to Excel file with product URLs: ").strip()
        process_products_from_excel(excel_path, drive=drive, parent_folder_id=parent_folder_id)

    else:
        print("Invalid choice. Exiting.")
        exit()
