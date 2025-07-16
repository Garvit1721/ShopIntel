# --- prompt.py ---
import json
from typing import Dict, Any, List

def classifier_prompt(info: Dict[str, Any]) -> str:
    """
    Constructs a JSON-formatted prompt for product classification with relevant items.
    """
    prompt = {
        "task": "Product Category Classification",
        "description": (
            "You are a product classification assistant. Based on the given product information, "
            "classify the product into one of the following categories:\n"
            "- Electronics\n"
            "- Clothes\n"
            "- Food\n\n"
            "Also provide 5 relevant product names.\n"
            "Respond only in JSON with the format:\n"
            "{\n  \"product_classifier\": \"<Category>\",\n  \"relevant_items\": [\"item1\", \"item2\", ...]\n}"
        ),
        "few_shot_examples": [
            {
                "input": {
                    "title": "Sony WH-1000XM4 Wireless Headphones",
                    "price": "299.99",
                    "rating": "4.8 out of 5 stars",
                    "about_this_item": ["Industry-leading noise cancellation", "30 hours battery"]
                },
                "output": {
                    "product_classifier": "Electronics",
                    "relevant_items": [
                        "Bose 700 Headphones",
                        "Jabra Elite 85h",
                        "Sennheiser Momentum 4",
                        "Apple AirPods Max",
                        "Beats Studio3 Wireless"
                    ]
                }
            }
        ],
        "input": info,
        "instruction": "Classify and return 5 relevant items. Only return JSON."
    }
    return json.dumps(prompt, indent=2)

def generate_llm_report(result: dict) -> str:
    product_info = result.get("product_info", "")
    classification = result.get("classification_result", {})
    tech_spec = result.get("specifications", "")
    reviews = result.get("reviews", "")
    similar_items = result.get("similar_items", "")
    youtube_videos = result.get("youtube_videos", "")
    relevant_items = result.get("relevant_search_items", "")
    customer_profile = result.get("customer_data", {})

    category = classification.get("product_classifier", "").lower()

    prompt = f"""
You are a product analyst AI generating a **clean, professional Markdown report** for a given product.

Follow these formatting and content rules very strictly to ensure clarity, structure, and usefulness:

---

### 🧾 Markdown Formatting Instructions:
- Use **bold section headings** (e.g., `**1. Product Summary**`)
- Use **bullet points (`-`)** for concise highlights (limit 3–5).
- Use **Markdown tables** whenever suitable (e.g., specs, comparisons, YouTube links).
- **Embed all links** using `[text](url)` format – DO NOT miss any links.
- DO NOT use HTML, JSON, or code formatting blocks.
- Tone should be professional, helpful, and concise.

---

### 📋 Sections to include (in this exact order):

**1. Product Summary**  
Brief overview including:
- What the product is and its purpose  
- Price (if available)  
- Rating  
- Top 2–3 selling points  

**2. Key Specifications**  
- List only the **top 4–5 most important** specs  
- Present them in a **Markdown table** with two columns: `Feature` | `Details`

**3. Review Analysis**  
Summarize top review insights:
- Positive comments  
- Common complaints or negatives  
- Any trends or repeated mentions  

**4. Product Comparison with Similar Items**  
Compare with 3–4 similar products in a **Markdown table** with columns:  
`Product Name` | `Difference` | `Price` | `Link`

**5. Similar Items (with links)**  
List 3–5 related items with:
- Product name  
- Price  
- [Markdown link](url)

Use a table if possible: `Product Name` | `Price` | `Link`

**6. YouTube Reviews**  
Mention 2–3 relevant video reviews with:
- Video Title  
- Channel Name  
- Clickable Link

Use a Markdown table: `Title` | `Channel` | `Watch`

**7. Relevant Alternatives**  
AI-recommended alternatives with:
- Product name  
- Price  
- Clickable link

Again, format as a table.

**8. Personalized Recommendation Check**  
Based on the provided customer profile, evaluate how well the product fits:
- Use the customer profile to assess fit (e.g., preferences, decision style)
- Mention if the product aligns with the user's interests or preferences
- Highlight any specific features that match the profile
- Discuss any mismatches or concerns based on the profile
- Provide a final recommendation based on the profile
- Evaluate whether the product fits any interest or preference
- Suggest cross-category complementary products (max 3) with proper `[markdown links](url)`
- Highlight how the product fits the profile
- Mention any mismatches or concerns based on the profile
- Provide a final recommendation based on the profile
- Evaluate whether the **given product fits** any interest or preference  
- Suggest **cross-category complementary products** (max 3)  
- Provide proper `[markdown links](url)` for the suggested products  

Examples:
- electronics: [Smartphone](https://example.com/smartphone)  
- clothes: [Casual Shoes](https://example.com/casual-shoes)  
- food: [Protein Bars](https://example.com/protein-bars)

**9. Category-Specific Tips**  
Give helpful advice based on product type:
"""

    if category == "electronics":
        prompt += "- Suggest care or usage tips (e.g., screen care, battery usage).\n- Recommend accessories or pairing items (e.g., cases, earbuds).\n"
    elif category == "food":
        prompt += "- Mention key ingredients or health benefits.\n- Suggest food pairings or time of day usage.\n"
    else:
        prompt += "- Suggest primary use cases (e.g., travel, daily wear).\n- Identify ideal users (e.g., students, professionals).\n- Mention care instructions if relevant.\n"

    prompt += f"""

---

## 🧩 Raw Data Below (for your reference only):

### Product Info
{product_info}

### Classification Result
{classification}

### Specifications
{tech_spec}

### Reviews
{reviews}

### Similar Items
{similar_items}

### YouTube Videos
{youtube_videos}

### Relevant Search Items
{relevant_items}

### Customer Profile
{customer_profile}

---

Now generate a **fully structured Markdown report** using all the formatting rules and section definitions provided above.

**Respond ONLY with the Markdown content. No preambles. No explanations. Just the report.**
"""
    return prompt

def chat_prompt(result: Dict[str, Any], chat_history: List[Dict[str, str]], question: str) -> str:
    product_info = result.get("product_info", "")
    classification = result.get("classification_result", {})
    tech_spec = result.get("specifications", "")
    reviews = result.get("reviews", "")
    similar_items = result.get("similar_items", "")
    youtube_videos = result.get("youtube_videos", "")
    relevant_items = result.get("relevant_search_items", "")

    prompt = (
        "You're a friendly and knowledgeable product assistant designed to help users make smart shopping decisions.\n\n"
        "Use all the provided data—from Amazon, YouTube, search results, and more—to chat naturally with the user, while still being informative and accurate.\n\n"
        
        "-------------------\n"
        "**Style & Formatting Tips:**\n"
        "- Keep it casual yet helpful, as if you're chatting with a friend who asked for product advice.\n"
        "- Format your answer using **Markdown**.\n"
        "- Use **bullet points** for features, pros/cons, and other lists.\n"
        "- Use **Markdown tables** to neatly compare specs or list videos.\n"
        "- Link to products or resources using this format: `[Product Name](https://example.com)`.\n"
        "- Avoid code blocks, raw JSON, or overly technical explanations unless the user asks.\n\n"
        "- Don’t hesitate to share brief opinions like “This looks like a solid choice for...”, or “You might want to consider...”.\n"
        "- Offer related suggestions if it helps.\n\n"

        "-------------------\n"
        "**What You Know About the Product:**\n"
        f"- **Info**: {product_info}\n"
        f"- **Classification**: {classification}\n"
        f"- **Specifications**: {tech_spec}\n"
        f"- **Reviews**: {reviews}\n"
        f"- **Similar Items**: {similar_items}\n"
        f"- **YouTube Videos**: {youtube_videos}\n"
        f"- **Relevant Search Items**: {relevant_items}\n\n"

        "-------------------\n"
        "**Chat History So Far:**\n"
        f"{chat_history}\n\n"

        "-------------------\n"
        "**Current User Question:**\n"
        f"{question}\n\n"

        "-------------------\n"
        "**What to Do:**\n"
        "- Answer the user’s question clearly and conversationally.\n"
        "- Structure your response using helpful **Markdown sections** like `### Overview`, `### Pros & Cons`, `### Alternatives`, etc.\n"
        "- Highlight useful insights from reviews or tech specs.\n"
        "- Include links or references when helpful.\n"
        "- Make sure it’s easy to read, helpful, and feels like a real conversation.\n\n"

        "**Now reply with just the markdown-formatted response below:**"
    )
    return prompt
