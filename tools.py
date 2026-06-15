"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    listings = load_listings()

    if not description or not isinstance(description, str):
        return []

    query = description.lower().strip()
    query_words = query.split()

    matches = []

    for item in listings:
        # Build searchable text from multiple fields
        title = str(item.get("title", "")).lower()
        item_description = str(item.get("description", "")).lower()
        category = str(item.get("category", "")).lower()
        style_tags = " ".join(item.get("style_tags", [])).lower()
        colors = " ".join(item.get("colors", [])).lower()
        brand = str(item.get("brand", "")).lower()

        searchable_text = " ".join(
            [title, item_description, category, style_tags, colors, brand]
        )

        # Filter by max price
        if max_price is not None:
            try:
                item_price = float(item.get("price", 0))
                if item_price > float(max_price):
                    continue
            except (TypeError, ValueError):
                continue

        # Filter by size
        # This allows "M" to match "M" or "S/M"
        if size is not None and str(size).strip() != "":
            requested_size = str(size).lower().strip()
            item_size = str(item.get("size", "")).lower().strip()

            if requested_size not in item_size:
                continue

        # Score by keyword overlap
        score = 0

        for word in query_words:
            if word in searchable_text:
                score += 1

        # Extra score for full phrase match
        if query in searchable_text:
            score += 3

        # Keep only relevant matches
        if score > 0:
            item_copy = item.copy()
            item_copy["_score"] = score
            matches.append(item_copy)

    # Sort by relevance first, then cheaper price
    matches.sort(key=lambda item: (-item["_score"], item.get("price", 999999)))

    # Remove internal score before returning
    for item in matches:
        item.pop("_score", None)

    return matches
    # Replace this with your implementation
    # return []


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    # Replace this with your implementation
    if not new_item or not isinstance(new_item, dict):
        return "I could not suggest an outfit because no thrift item was selected."

    wardrobe_items = []

    if isinstance(wardrobe, dict):
        wardrobe_items = wardrobe.get("items", [])

    item_summary = {
        "title": new_item.get("title"),
        "description": new_item.get("description"),
        "category": new_item.get("category"),
        "style_tags": new_item.get("style_tags"),
        "colors": new_item.get("colors"),
        "brand": new_item.get("brand"),
        "price": new_item.get("price"),
        "condition": new_item.get("condition"),
        "platform": new_item.get("platform"),
    }

    if not wardrobe_items:
        wardrobe_text = (
            "The user's wardrobe is empty. Give general styling advice using common basics. "
            "Do not pretend the user owns specific wardrobe items."
        )
    else:
        wardrobe_text = "\n".join(str(item) for item in wardrobe_items)

    prompt = f"""
You are FitFindr, a helpful secondhand fashion styling assistant.

Selected thrift item:
{item_summary}

User wardrobe:
{wardrobe_text}

Task:
Suggest 1 complete outfit using the selected thrift item.

Rules:
- If wardrobe items are available, use specific pieces from the wardrobe.
- If the wardrobe is empty, suggest common basics instead.
- Mention the thrifted item.
- Keep it under 120 words.
- Sound friendly, practical, and stylish.
"""

    try:
        client = _get_groq_client()

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a practical and stylish secondhand fashion assistant.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return (
            "I could not generate an outfit suggestion because the styling tool "
            f"had an error: {str(e)}"
        )
    # return ""



# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # Replace this with your implementation
    if not outfit or not isinstance(outfit, str) or not outfit.strip():
        return "Cannot create a fit card because the outfit suggestion is empty or missing."

    if not new_item or not isinstance(new_item, dict):
        return "Cannot create a fit card because no thrift item was selected."

    item_title = new_item.get("title", "this thrifted piece")
    price = new_item.get("price", "a good price")
    platform = new_item.get("platform", "a secondhand platform")
    condition = new_item.get("condition", "good condition")
    style_tags = new_item.get("style_tags", [])

    prompt = f"""
Create a short, shareable outfit caption for social media.

Thrifted item:
- Title: {item_title}
- Price: {price}
- Platform: {platform}
- Condition: {condition}
- Style tags: {style_tags}

Outfit suggestion:
{outfit}

Requirements:
- 2 to 4 sentences.
- Casual and authentic, like a real OOTD caption.
- Mention the item name, price, and platform naturally once each.
- Capture the outfit vibe in specific terms.
- Do not sound like a product advertisement.
"""

    try:
        client = _get_groq_client()

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You write short, stylish captions for thrifted outfits.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=1.0,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return (
            "I could not create a fit card because the caption tool had an error: "
            f"{str(e)}"
        )
    # return ""
