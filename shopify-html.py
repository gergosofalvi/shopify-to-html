import requests
from bs4 import BeautifulSoup
import os
import time
from tqdm import tqdm

# Main URL
base_url = "https://youtshopifypage.com"

# Fetch collections from the JSON source
collections_url = f"{base_url}/collections.json"
collections_response = requests.get(collections_url)
collections_data = collections_response.json()

# Create a directory for images
if not os.path.exists("images"):
    os.makedirs("images")

# Product limit variable
product_limit = 30  # Default limit, max 30

# Page limit variable
page_limit = None  # Default, no page limit

# Create HTML file
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Cubic Dissection Collections</title>
    <style>
        .collection-filter {{
            margin-bottom: 20px;
        }}
        .collection-buttons {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .collection-button {{
            padding: 10px;
            background-color: #007BFF;
            color: white;
            border: none;
            cursor: pointer;
            border-radius: 5px;
        }}
        .product-list {{
            display: flex;
            flex-wrap: wrap;
        }}
        .product {{
            width: 30%;
            margin: 10px;
            padding: 10px;
            border: 1px solid #ddd;
            transition: transform 0.2s;
        }}
        .product:hover {{
            transform: scale(1.05);
        }}
        .product img {{
            max-width: 100%;
            height: auto;
            cursor: pointer;
        }}
        .pagination {{
            display: flex;
            justify-content: center;
            align-items: center;
            margin-top: 20px;
        }}
        .page-link {{
            margin: 0 5px;
            cursor: pointer;
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <h1>Cubic Dissection Collections</h1>
    <div class="collection-filter">
        <div class="collection-buttons">
"""

# Process collections and add buttons
for collection in collections_data['collections']:
    collection_name = collection['title']
    collection_handle = collection['handle']
    product_count = collection['products_count']  # Number of products

    # Include the product count in the button's name
    html_content += f'<button class="collection-button" data-collection="{collection_handle}">{collection_name} ({product_count})</button>'

    # Create a directory for collection images
    if not os.path.exists(f"images/{collection_handle}"):
        os.makedirs(f"images/{collection_handle}")

html_content += """
        </div>
    </div>
    <div class="product-list">
"""

# Download and process products
for collection in collections_data['collections']:
    collection_name = collection['title']
    collection_handle = collection['handle']

    page_size = product_limit  # Number of products per request
    page_number = 1
    while True:
        products_url = f"{base_url}/collections/{collection_handle}/products.json?page={page_number}&limit={page_size}"
        products_response = requests.get(products_url)
        products_data = products_response.json()

        if not products_data['products']:
            break  # If there are no more products on the page, exit the loop

        for product in tqdm(products_data['products'], desc=f"Collection: {collection_name}, Page: {page_number}"):
            product_name = product['title']
            product_handle = product['handle']
            product_description = product['body_html']
            product_image_urls = [image['src'] for image in product['images']]

            # Check if the image has already been downloaded
            existing_images = os.listdir(f"images/{collection_handle}")
            for i, image_url in enumerate(product_image_urls):
                image_filename = f"{product_handle}_{i}.jpg"
                if image_filename in existing_images:
                    continue  # Skip download if the image is already in place

                retry_count = 0
                while True:
                    image_response = requests.get(image_url)
                    if image_response.status_code == 200:
                        break
                    elif retry_count < 3:
                        retry_count += 1
                        time.sleep(5)  # Wait for 5 seconds and retry
                    else:
                        print(f"Error downloading image ({product_name}): {image_url}")
                        break
                with open(f"images/{collection_handle}/{image_filename}", "wb") as image_file:
                    image_file.write(image_response.content)

            # Add product to HTML
            html_content += f'''
            <div class="product {collection_handle}">
                <h3>{product_name}</h3>
                <p>{product_description}</p>
                <div class="image-gallery">
'''

            # Process and display all product images
            for i, image_url in enumerate(product_image_urls):
                image_filename = f"{product_handle}_{i}.jpg"
                image_path = f"images/{collection_handle}/{image_filename}"
                html_content += f'''
                <a href="{image_path}" target="_blank">
                    <img src="{image_path}" alt="{product_name}" width="100" height="100">
                </a>
                '''

            html_content += """
                </div>
            </div>
            """

        # Check page limit
        if page_limit is not None and page_number >= page_limit:
            break

        page_number += 1

html_content += """
    </div>
</body>
<script>
    const collectionButtons = document.querySelectorAll(".collection-button");
    const products = document.querySelectorAll(".product");

    collectionButtons.forEach(button => {
        button.addEventListener("click", () => {
            const collectionHandle = button.getAttribute("data-collection");
            products.forEach(product => {
                if (product.classList.contains(collectionHandle)) {
                    product.style.display = "block";
                } else {
                    product.style.display = "none";
                }
            });
        });
    });
</script>
</html>
"""

# Save HTML file
with open("index.html", "w", encoding="utf-8") as html_file:
    html_file.write(html_content)

print("index.html file created. Data downloaded, images available locally, filtering works, and progress is visible.")
