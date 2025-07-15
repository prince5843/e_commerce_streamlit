from together import Together
##This imports the Together AI Python client library.
##It's a wrapper that simplifies how you send API requests to Together’s hosted LLaMA, Mistral, and other models.
client = Together(api_key="59c00bb34ce46908ead205258a034bc7e2c796a36459838bd1de0c621100db62")

def generate_product_content(product_title):
    """
    Uses Together API to generate:
    - Product Name (max 60 chars)
    - Short Description (2 lines)
    - Long Description (hook, features, benefits, CTA)
    """

    prompt = f"""
You are an expert e-commerce copywriter. Based on the product title below, create:

1. An SEO-optimized Product Name (max 60 characters)
2. A 2-line Short Description highlighting emotional benefits
3. A Long Description (150-200 words) with:
- 1-sentence hook
- 3 bullet-point features with benefits
- 2-3 sentences explaining how it improves the user's life
- Technical specifications (if any)
- A subtle call-to-action

Product Title: {product_title}
"""
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=512,
        temperature=0.7,
        top_p=0.9,
    )
    content = response.choices[0].message.content
    return content

# Quick test
if __name__ == "__main__":
    sample_title = "Wireless Bluetooth Neckband Earphones with 30 Hours Battery Life"
    result = generate_product_content(sample_title)
    print(result)