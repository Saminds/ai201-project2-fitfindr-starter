"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import re

from tools import search_listings, suggest_outfit, create_fit_card
# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────
def _parse_query(query: str) -> dict:
    """
    Extract description, size, and max_price from the user's natural language query.
    This is a simple rule-based parser for the project demo.
    """

    query_lower = query.lower()

    # Find max price from phrases like "under $30", "$30", or "under 30"
    max_price = None
    price_match = re.search(r"(?:under\s*)?\$?(\d+(?:\.\d+)?)", query_lower)
    if price_match:
        max_price = float(price_match.group(1))

    # Find size from phrases like "size M" or "size XXS"
    size = None
    size_match = re.search(r"size\s+([a-zA-Z0-9/]+)", query_lower)
    if size_match:
        size = size_match.group(1).upper()

    # Remove price and size phrases to create a cleaner description
    description = query_lower
    description = re.sub(r"under\s*\$?\d+(?:\.\d+)?", "", description)
    description = re.sub(r"\$?\d+(?:\.\d+)?", "", description)
    description = re.sub(r"size\s+[a-zA-Z0-9/]+", "", description)

    # Remove common filler words
    filler_phrases = [
        "looking for",
        "i am",
        "i'm",
        "find me",
        "can you find",
        "what's out there",
        "what is out there",
        "and how would i style it",
        "how would i style it",
    ]

    for phrase in filler_phrases:
        description = description.replace(phrase, "")

    description = description.strip(" ,.?")

    if not description:
        description = query

    return {
        "description": description,
        "size": size,
        "max_price": max_price,
    }
def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.

    TODO — implement this function using the planning loop you designed in planning.md:

        Step 1: Initialize the session with _new_session().

        Step 2: Parse the user's query to extract a description, size, and
                max_price. You can use regex, string splitting, or ask the LLM
                to parse it — document your choice in planning.md.
                Store the result in session["parsed"].

        Step 3: Call search_listings() with the parsed parameters.
                Store results in session["search_results"].
                If no results: set session["error"] to a helpful message and
                return the session early. Do NOT proceed to suggest_outfit
                with empty input.

        Step 4: Select the item to use (e.g., the top result).
                Store it in session["selected_item"].

        Step 5: Call suggest_outfit() with the selected item and wardrobe.
                Store the result in session["outfit_suggestion"].

        Step 6: Call create_fit_card() with the outfit suggestion and selected item.
                Store the result in session["fit_card"].

        Step 7: Return the session.

    Before writing code, complete the Planning Loop and State Management sections
    of planning.md — your implementation should match what you described there.
    """
    # Step 1: Initialize session
    session = _new_session(query, wardrobe)

    # Step 2: Parse query
    parsed = _parse_query(query)
    session["parsed"] = parsed

    description = parsed["description"]
    size = parsed["size"]
    max_price = parsed["max_price"]

    # Step 3: Search listings
    results = search_listings(
        description=description,
        size=size,
        max_price=max_price,
    )

    session["search_results"] = results

    # If no results, stop early
    if not results:
        session["error"] = (
            f"No listings found for '{description}'. "
            "Try using a broader description, increasing your budget, "
            "or removing the size filter."
        )
        return session

    # Step 4: Select top item
    selected_item = results[0]
    session["selected_item"] = selected_item

    # Step 5: Suggest outfit
    outfit_suggestion = suggest_outfit(selected_item, wardrobe)
    session["outfit_suggestion"] = outfit_suggestion

    if not outfit_suggestion or not outfit_suggestion.strip():
        session["error"] = (
            "A listing was found, but the agent could not create an outfit suggestion."
        )
        return session

    if outfit_suggestion.startswith("I could not generate"):
        session["error"] = outfit_suggestion
        return session

    # Step 6: Create fit card
    fit_card = create_fit_card(outfit_suggestion, selected_item)
    session["fit_card"] = fit_card

    # Step 7: Return completed session
    return session

# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
