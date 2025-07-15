import re
import json
import random
from urllib.parse import urlparse, urljoin
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

# Robust user-agent list
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.70 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
]

# Mapping of domain to their best price selectors
SITE_PRICE_SELECTORS = {
    "amazon.": [
        ".a-price .a-offscreen",  # Main price
        "#priceblock_ourprice",   # Standard price
        "#priceblock_dealprice",  # Deal price
        "#priceblock_saleprice",  # Sale price
        "#corePriceDisplay_desktop_feature_div .a-offscreen",  # Newer price block
        ".apexPriceToPay .a-offscreen",  # Used in some new layouts
        ".a-size-medium.a-color-price.priceBlockBuyingPriceString",  # Alternate
        ".a-size-base.a-color-price.a-color-price",  # Alternate
        ".a-price-whole",  # Sometimes price is split
        ".a-price-fraction",  # Sometimes price is split
    ],
    "flipkart.com": [
        ".Nx9bqj.CxhGGd",  # New selector for discounted price
        "._30jeq3._16Jk6d",  # Old selector for discounted price
        "._25b18c ._30jeq3", ".pdp-price"
    ],
    "croma.com": [
        ".amount", ".pdpPrice"
    ],
    "reliancedigital.in": [
        ".pdp__offerPrice", ".price"
    ],
    "tatacliq.com": [
        ".ProductDetailsMainCard_Price", ".ProductDetailsMainCard_BestPrice"
    ],
    "snapdeal.com": [
        ".pdp-final-price", ".payBlkBig", ".product-price"
    ],
    "paytmmall.com": [
        ".price", ".offer-price", ".final-price"
    ],
    "shopclues.com": [
        ".price", ".f_price", ".offer-price"
    ],
    "myntra.com": [
        ".pdp-price", ".price", ".price-discounted"
    ],
    "ajio.com": [
        ".price", ".prod-sp", ".price-value"
    ],
    "nykaa.com": [
        ".price", ".price-value", ".offer-price"
    ],
    "bigbasket.com": [
        ".price", ".discounted-price", ".final-price"
    ],
    "grofers.com": [
        ".price", ".product-price", ".final-price"
    ],
    "firstcry.com": [
        ".price", ".discounted-price", ".final-price"
    ],
    "bookmyshow.com": [
        ".price", ".ticket-price", ".final-price"
    ],
    "cleartrip.com": [
        ".price", ".fare-price", ".final-price"
    ],
    "makemytrip.com": [
        ".price", ".fare-price", ".final-price"
    ],
    "goibibo.com": [
        ".price", ".fare-price", ".final-price"
    ]
}

GENERIC_SELECTORS = [
    "[itemprop='price']", ".price", "span:has-text('₹')", "span:has-text('Rs.')", "span:has-text('INR')", "span:has-text('$')"
]

def get_site_selectors(url):
    domain = urlparse(url).netloc
    for key in SITE_PRICE_SELECTORS:
        if key in domain:
            return SITE_PRICE_SELECTORS[key] + GENERIC_SELECTORS
    return GENERIC_SELECTORS

def is_flipkart(url):
    return "flipkart.com" in urlparse(url).netloc

def is_amazon(url):
    return "amazon." in urlparse(url).netloc

def extract_best_price(page):
    price_texts = []
    selectors = [
        ".a-price .a-offscreen", ".a-price-whole", ".a-price-fraction",
        "#priceblock_ourprice", "#priceblock_dealprice", "#priceblock_saleprice",
        ".a-size-medium.a-color-price.priceBlockBuyingPriceString",
        ".a-size-base.a-color-price.a-color-price",
        "[data-a-color='price'] .a-offscreen", "span:has-text('₹')", "span:has-text('Rs.')"
    ]
    for selector in selectors:
        try:
            elems = page.query_selector_all(selector)
            for elem in elems:
                text = elem.inner_text().strip()
                if text and any(char.isdigit() for char in text):
                    price_texts.append(text)
        except Exception:
            continue
    price_texts = list(set(price_texts))
    filtered = [p for p in price_texts if not any(x in p.lower() for x in ['mrp', 'list', 'was', 'save', 'you save'])]
    prices = []
    for p in filtered:
        match = re.search(r'₹\s?([\d,]+)', p)
        if match:
            value = int(match.group(1).replace(',', ''))
            prices.append(value)
    if prices:
        return f'₹{min(prices)}'
    return 'Not Available'

def extract_amazon_prices(page):
    # Extract all visible prices in the main buy box
    prices = []
    try:
        price_elems = page.query_selector_all(".a-price .a-offscreen")
        for elem in price_elems:
            text = elem.inner_text().strip()
            match = re.search(r'₹\s?([\d,]+(?:\.\d{2})?)', text)
            if match:
                prices.append(f"₹{match.group(1)}")
    except Exception:
        pass
    # Remove duplicates, keep order
    prices = list(dict.fromkeys(prices))
    discounted_price = prices[0] if prices else "Not Available"
    mrp = prices[1] if len(prices) > 1 else ""
    return discounted_price, mrp

def extract_flipkart_price(page):
    # Try all known selectors first
    selectors = [
        ".Nx9bqj.CxhGGd",  # New selector from user screenshot
        "._30jeq3._16Jk6d",  # Old selector
        ".pdp-price",  # Sometimes used
        # Add more as you discover them
    ]
    for selector in selectors:
        try:
            page.wait_for_selector(selector, timeout=5000)
            price = page.query_selector(selector)
            if price:
                text = price.inner_text().strip()
                if "₹" in text and any(char.isdigit() for char in text):
                    return text
        except Exception:
            continue
    # Fallback: Find any div/span with ₹ and numbers
    price_candidates = page.locator("div,span").all_text_contents()
    for text in price_candidates:
        match = re.search(r'₹\s?[\d,]+', text)
        if match:
            return match.group().strip()
    return "Not Available"

def scrape_flipkart_product(url):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        time.sleep(3) # Wait for JS to load

        # Title (try multiple selectors)
        title = ""
        title_selectors = [
            "h1._6EBuvT span.VU-ZEz",  # new structure: h1 with class, span with class
            "span.VU-ZEz",             # direct span
            "h1",                      # fallback to any h1
            "span.B_NuCI"              # old selector
        ]
        for sel in title_selectors:
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                if el:
                    title = el.text.strip()
                    if title:
                        break
            except NoSuchElementException:
                continue

        # Images (try multiple selectors, print what you find)
        image_urls = []
        main_img_selectors = [
            "img.DByu4f.IZexXJ.jLEJ7H",
            "img.DByu4f",
            "img.IZexXJ",
            "img.jLEJ7H",
            "img[class*='DByu4f']",
            "img[class*='IZexXJ']",
            "img[class*='jLEJ7H']",
            "img"
        ]
        for sel in main_img_selectors:
            try:
                imgs = driver.find_elements(By.CSS_SELECTOR, sel)
                for img in imgs:
                    src = img.get_attribute("src")
                    if src and "rukminim2.flixcart.com" in src and src not in image_urls:
                        image_urls.append(src)
            except Exception:
                continue
        # Gallery thumbnails
        try:
            thumb_imgs = driver.find_elements(By.CSS_SELECTOR, "img._3GnUWp, img._2OHU_q, img[class*='thumb']")
            for img in thumb_imgs:
                src = img.get_attribute("src")
                if src and "rukminim2.flixcart.com" in src and src not in image_urls:
                    image_urls.append(src)
            thumb_divs = driver.find_elements(By.CSS_SELECTOR, "div[style*='background-image']")
            for div in thumb_divs:
                style = div.get_attribute("style")
                if style:
                    match = re.search(r"url\\([\"\\']?(https://rukminim2\\.flixcart\\.com/[^\"\\')]+)[\"\\']?\\)", style)
                    if match:
                        src = match.group(1)
                        if src not in image_urls:
                            image_urls.append(src)
        except Exception:
            pass
        # Price
        price = ""
        try:
            price_selectors = [
                ".Nx9bqj.CxhGGd",
                "._30jeq3._16Jk6d",
                ".pdp-price"
            ]
            for sel in price_selectors:
                try:
                    price_elem = driver.find_element(By.CSS_SELECTOR, sel)
                    text = price_elem.text.strip()
                    if "₹" in text and any(char.isdigit() for char in text):
                        price = text
                        break
                except NoSuchElementException:
                    continue
            if not price:
                # Fallback: Find any div/span with ₹ and numbers
                elems = driver.find_elements(By.CSS_SELECTOR, "div,span")
                for elem in elems:
                    text = elem.text
                    match = re.search(r'₹\s?[\d,]+', text)
                    if match:
                        price = match.group().strip()
                        break
        except Exception:
            pass
        return {
            "title": title,
            "price": price,
            "image_urls": image_urls,
            "brand": "",
            "category": "",
            "sku": "",
            "mrp": ""
        }
    finally:
        driver.quit()


def scrape_flipkart_serpapi(url):
    """
    Scrape Flipkart product data using SerpApi Google Shopping engine.
    """
    api_key = "8b2762e078b582428e61322daf9ac36b40181c0603bce9b7d4854d5e3a27f501"  # <-- Replace with your SerpApi key or pass as env/config
    params = {
        "engine": "google_shopping",
        "q": url,
        "api_key": api_key,
        "hl": "en",
        "gl": "in"
    }
    response = requests.get("https://serpapi.com/search", params=params)
    if response.status_code != 200:
        print(f"SerpApi error: {response.status_code}")
        return None
    data = response.json()
    product_data = {
        "title": "",
        "price": "",
        "image_urls": [],
        "brand": "",
        "category": "",
        "sku": "",
        "mrp": ""
    }
    # Try to extract from shopping_results
    shopping_results = data.get("shopping_results", [])
    if shopping_results:
        product = shopping_results[0]
        product_data["title"] = product.get("title", "")
        # Prefer extracted_price (discounted), fallback to price
        product_data["price"] = product.get("extracted_price", product.get("price", ""))
        product_data["image_urls"] = [product.get("thumbnail")] if product.get("thumbnail") else []
        product_data["brand"] = product.get("source", "")
        # Try to get MRP if available
        if "original_price" in product:
            product_data["mrp"] = product["original_price"]
        return product_data
    return None


def scrape_product_data(url):
    if is_flipkart(url):
        try:
            serpapi_result = scrape_flipkart_serpapi(url)
            if (
                not serpapi_result or
                len(serpapi_result.get("image_urls", [])) <= 1 or
                not serpapi_result.get("price") or
                serpapi_result.get("price") == serpapi_result.get("mrp")
            ):
                print("SerpApi incomplete, using Selenium for Flipkart.")
                return scrape_flipkart_product(url)
            return serpapi_result
        except Exception as e:
            print(f"Flipkart SerpApi scrape failed: {e}")
            try:
                return scrape_flipkart_product(url)
            except Exception as e2:
                print(f"Flipkart Selenium scrape failed: {e2}")
                return None
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        time.sleep(3)
        price_text = "Not Available"
        found = False
        price_selectors = get_site_selectors(url)
        mrp = ""
        if is_amazon(url):
            # Try all selectors for price
            for selector in SITE_PRICE_SELECTORS["amazon."]:
                try:
                    price_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    text = price_elem.text.strip()
                    if text and any(char.isdigit() for char in text):
                        price_text = text
                        found = True
                        break
                except NoSuchElementException:
                    continue
        if not found:
            for selector in price_selectors:
                try:
                    price_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    text = price_elem.text.strip()
                    if text and any(char.isdigit() for char in text):
                        price_text = text
                        found = True
                        break
                except NoSuchElementException:
                    continue
        # Product Title
        try:
            product_title = driver.title
        except Exception:
            product_title = "Title Not Found"
        # Brand and Category (try meta tags and JSON-LD)
        brand = ""
        category = ""
        try:
            metas = driver.find_elements(By.TAG_NAME, "meta")
            for meta in metas:
                name = meta.get_attribute("name")
                prop = meta.get_attribute("property")
                content = meta.get_attribute("content")
                if name and "brand" in name.lower() and content:
                    brand = content
                if name and "category" in name.lower() and content:
                    category = content
                if prop and "brand" in prop.lower() and content:
                    brand = content
                if prop and "category" in prop.lower() and content:
                    category = content
        except Exception:
            pass
        # Images
        image_urls = []
        try:
            imgs = driver.find_elements(By.TAG_NAME, "img")
            for img in imgs:
                src = img.get_attribute("src")
                if src and src.startswith("http") and src not in image_urls:
                    image_urls.append(src)
        except Exception:
            pass
        return {
            "title": product_title,
            "price": price_text,
            "image_urls": image_urls,
            "brand": brand,
            "category": category,
            "sku": "",
            "mrp": mrp
        }
    finally:
        driver.quit()
