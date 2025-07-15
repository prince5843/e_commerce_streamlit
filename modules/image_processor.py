import os
import requests
from PIL import Image
from io import BytesIO
from modules.drive_uploader import get_or_create_folder, upload_image_to_drive

# Create images folder if it doesn't exist
os.makedirs("data/images", exist_ok=True)

def download_and_optimize_images(image_urls, product_name, drive=None, parent_folder_id=None):
    """
    Downloads images, validates, resizes, compresses, renames SEO-friendly, and saves them
    inside a dedicated folder for each product. Then uploads to Google Drive if drive is provided.
    Returns list of Google Drive links (or local paths if drive is None)
    """
    import re
    product_slug = re.sub(r'[^a-zA-Z0-9_\-]', '_', product_name.lower())
    product_slug = re.sub(r'_+', '_', product_slug).strip('_')[:50]

    product_folder = os.path.join("data/images", product_slug)
    os.makedirs(product_folder, exist_ok=True)

    drive_links = []
    local_paths = []

    for idx, url in enumerate(image_urls):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))

                # Validate minimum size
                if img.size[0] < 500 or img.size[1] < 500:
                    print(f"Image {idx+1} skipped: too small ({img.size})")
                    continue

                # Resize if too big
                max_size = (1500, 1500)
                img.thumbnail(max_size)

                # Compress and save with SEO-friendly name
                filename = f"{product_slug}_{idx+1}.jpg"
                save_path = os.path.join(product_folder, filename)
                img.save(save_path, format="JPEG", quality=85)
                local_paths.append(save_path)
                print(f"✅ Saved: {filename}")
            else:
                print(f"Failed to download image {idx+1}")

        except Exception as e:
            print(f"Error processing image {idx+1}: {e}")

    # Upload to Google Drive if drive is provided
    if drive and parent_folder_id:
        # Create/find product folder in Drive
        product_drive_folder_id = get_or_create_folder(drive, product_slug, parent_id=parent_folder_id)
        for local_path in local_paths:
            try:
                drive_link = upload_image_to_drive(drive, local_path, product_drive_folder_id)
                drive_links.append(drive_link)
            except Exception as e:
                print(f"Error uploading {local_path} to Drive: {e}")
        return drive_links
    else:
        # Return local relative paths for Excel export (legacy)
        return [os.path.relpath(p, "data/images") for p in local_paths]

# Quick test
if __name__ == "__main__":
    sample_urls = ["https://static.remove.bg/sample-gallery/graphics/bird-thumbnail.jpg"]
    result = download_and_optimize_images(sample_urls, "Sample Product Name")
    print(result)