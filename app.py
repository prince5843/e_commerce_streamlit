import streamlit as st
import pandas as pd
import os
import io
from modules.scraper import scrape_product_data
from modules.content_generator import generate_product_content
from modules.image_processor import download_and_optimize_images
from modules.excel_exporter import export_to_excel, extract_short_description, extract_category, extract_brand, CATEGORY_KEYWORDS
from modules.content_formatter import convert_content_to_html
from modules.drive_uploader import authenticate_drive
from main import get_product_urls_serpapi, get_brand_category_serpapi, get_brand_and_category_llm, process_product, process_products_from_excel, GOOGLE_DRIVE_PARENT_FOLDER_ID

st.set_page_config(page_title="E-Commerce Listing Automation", layout="wide")
st.title("🛒 E-Commerce Listing Automation System")

# Authenticate Google Drive only once per session
if 'drive' not in st.session_state:
    st.session_state['drive'] = authenticate_drive()
    st.session_state['parent_folder_id'] = GOOGLE_DRIVE_PARENT_FOLDER_ID

drive = st.session_state['drive']
parent_folder_id = st.session_state['parent_folder_id']

mode = st.radio(
    "Choose an option:",
    (
        "Search for product links by name (LLM-powered)",
        "Directly paste a product page URL",
        "Batch process product URLs from Excel file"
    )
)

if mode == "Search for product links by name (LLM-powered)":
    product_name = st.text_input("Enter product name:")
    if st.button("Search and Scrape"):        
        if not product_name:
            st.warning("Please enter a product name.")
        else:
            with st.spinner("Searching for product links and scraping data..."):
                candidate_urls = get_product_urls_serpapi(product_name, num_results=10)
                if not candidate_urls:
                    st.error("No product links found. Try a different product name.")
                else:
                    st.write("### Candidate product page URLs:")
                    for idx, url in enumerate(candidate_urls, start=1):
                        st.write(f"{idx}. {url}")
                    output_rows = []
                    used_domains = set()
                    for url in candidate_urls:
                        if len(output_rows) >= 4:
                            break
                        domain = None
                        for d in [
                            "amazon.in", "flipkart.com", "croma.com", "reliancedigital.in", "tatacliq.com", "vijaysales.com", 
                            "snapdeal.com", "paytmmall.com", "shopclues.com", "myntra.com", "ajio.com", "nykaa.com"
                        ]:
                            if d in url:
                                domain = d
                                break
                        if not domain or domain in used_domains:
                            continue
                        try:
                            product_data = scrape_product_data(url)
                            if (not product_data or not product_data.get("title") or
                                "access denied" in product_data.get("title", "").lower() or
                                product_data.get("title", "").strip() == "Access Denied"):
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
                        except Exception as e:
                            continue
                    if output_rows:
                        st.success(f"Scraped {len(output_rows)} products!")
                        df = pd.DataFrame(output_rows)
                        st.dataframe(df)
                        # Always save to disk
                        os.makedirs("data", exist_ok=True)
                        df.to_excel("data/product_listing.xlsx", index=False)
                        # For download button
                        excel_buffer = io.BytesIO()
                        df.to_excel(excel_buffer, index=False, engine='openpyxl')
                        excel_buffer.seek(0)
                        st.download_button(
                            label="Download Excel",
                            data=excel_buffer,
                            file_name="product_listing.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.error("No products were successfully processed.")

elif mode == "Directly paste a product page URL":
    url = st.text_input("Paste full product page URL:")
    if st.button("Scrape Product"):
        if not url:
            st.warning("Please enter a product URL.")
        else:
            with st.spinner("Scraping product data..."):
                try:
                    product_data = scrape_product_data(url)
                    if not product_data:
                        st.error("Failed to scrape product data.")
                    else:
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
                        st.success("Product scraped successfully!")
                        st.write(new_row)
                        if saved_images:
                            if len(saved_images) == 1:
                                st.image(saved_images[0], caption="Product Image", width=200)
                            else:
                                captions = [f"Image {i+1}" for i in range(len(saved_images))]
                                st.image(saved_images, caption=captions, width=200)
                        # FIXED DOWNLOAD BUTTON
                        df = pd.DataFrame([new_row])
                        os.makedirs("data", exist_ok=True)
                        df.to_excel("data/product_listing.xlsx", index=False)
                        excel_buffer = io.BytesIO()
                        df.to_excel(excel_buffer, index=False, engine='openpyxl')
                        excel_buffer.seek(0)
                        st.download_button(
                            label="Download Excel",
                            data=excel_buffer,
                            file_name="product_listing.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                except Exception as e:
                    st.error(f"Error: {e}")

elif mode == "Batch process product URLs from Excel file":
    uploaded_file = st.file_uploader("Upload Excel file with product URLs", type=["xlsx"])
    if st.button("Process Batch"):
        if not uploaded_file:
            st.warning("Please upload an Excel file.")
        else:
            with st.spinner("Processing batch..."):
                try:
                    # Save uploaded file to disk
                    temp_path = os.path.join("data", "uploaded_batch.xlsx")
                    os.makedirs("data", exist_ok=True)
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    process_products_from_excel(temp_path, drive=drive, parent_folder_id=parent_folder_id)
                    # Read and display the output
                    output_path = "data/product_listing.xlsx"
                    if os.path.exists(output_path):
                        df = pd.read_excel(output_path)
                        st.success("Batch processing complete!")
                        st.dataframe(df)
                        excel_buffer = io.BytesIO()
                        df.to_excel(excel_buffer, index=False, engine='openpyxl')
                        excel_buffer.seek(0)
                        st.download_button(
                            label="Download Excel",
                            data=excel_buffer,
                            file_name="product_listing.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.error("No output file found after processing.")
                except Exception as e:
                    st.error(f"Error: {e}") 