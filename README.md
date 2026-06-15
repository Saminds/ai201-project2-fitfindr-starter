# FitFindr

FitFindr is a multi-tool AI agent that helps users find secondhand clothing pieces and figure out how to style them. The agent searches a mock thrift listings dataset, selects a matching item, suggests an outfit using the user's wardrobe, and creates a short shareable fit card.

Unlike a simple chatbot, FitFindr uses a planning loop. It decides which tool to call next based on the result of the previous tool. If a search returns no results, the agent stops early and explains what the user can try instead.

---

## Tools

### 1. `search_listings(description: str, size: str | None, max_price: float | None) -> list[dict]`

**Purpose:**
Searches the mock secondhand listings dataset for items that match the user's requested description, size, and maximum price.

**Inputs:**

* `description` (`str`): Natural language description of the item, such as `"vintage graphic tee"` or `"black combat boots"`.
* `size` (`str | None`): Desired size, such as `"M"`, `"XXS"`, or `None` if no size is provided.
* `max_price` (`float | None`): Maximum price the user wants to pay, or `None` if no price limit is provided.

**Output:**
A list of listing dictionaries. Each listing may contain fields such as `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

**Error handling:**
If no listings match, the tool returns an empty list `[]`. The agent then stops early and tells the user to try a broader description, a higher budget, or removing the size filter.

---

### 2. `suggest_outfit(new_item: dict, wardrobe: dict) -> str`

**Purpose:**
Suggests a complete outfit using the selected thrift item and the user's wardrobe.

**Inputs:**

* `new_item` (`dict`): The selected listing returned by `search_listings`.
* `wardrobe` (`dict`): The user's wardrobe data, including an `items` list.

**Output:**
A non-empty string containing a practical outfit suggestion.

**Error handling:**
If the wardrobe is empty, the tool still returns general styling advice using common basics. It does not crash or pretend the user owns specific items.

---

### 3. `create_fit_card(outfit: str, new_item: dict) -> str`

**Purpose:**
Creates a short social-media-style outfit caption based on the selected thrift item and outfit suggestion.

**Inputs:**

* `outfit` (`str`): The outfit suggestion from `suggest_outfit`.
* `new_item` (`dict`): The selected thrift listing.

**Output:**
A short fit card or caption that mentions the thrifted item and captures the outfit vibe.

**Error handling:**
If the outfit input is empty or missing, the tool returns a clear error message instead of raising an exception.

---

## Planning Loop

The agent starts by parsing the user's natural language query into three pieces of information: `description`, `size`, and `max_price`.

The planning loop works conditionally:

1. The agent calls `search_listings(description, size, max_price)`.
2. If the search returns an empty list, the agent stores an error message in `session["error"]` and returns early.
3. If the search returns results, the agent stores them in `session["search_results"]`.
4. The agent selects the first result and stores it in `session["selected_item"]`.
5. The selected item is passed into `suggest_outfit(selected_item, wardrobe)`.
6. The outfit suggestion is stored in `session["outfit_suggestion"]`.
7. The outfit suggestion and selected item are passed into `create_fit_card(outfit_suggestion, selected_item)`.
8. The final fit card is stored in `session["fit_card"]`.

The agent does not call all tools blindly. Its behavior changes depending on the search result. If there is no selected item, the workflow stops before outfit generation.

---

## State Management

FitFindr uses a session dictionary to pass information between tools during one user interaction.

The session tracks:

* `query`: the original user query
* `parsed`: extracted search parameters such as description, size, and max price
* `search_results`: the list returned by `search_listings`
* `selected_item`: the top listing selected from the search results
* `wardrobe`: the selected wardrobe data
* `outfit_suggestion`: the result from `suggest_outfit`
* `fit_card`: the result from `create_fit_card`
* `error`: any error message that causes early termination

This state object allows the output from one tool to become the input for the next tool. For example, the item found by `search_listings` is stored as `session["selected_item"]` and then passed into `suggest_outfit`.

---

## Error Handling

| Tool              | Failure mode                     | Agent response                                                                                                                                                  |
| ----------------- | -------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `search_listings` | No listings match the query      | The agent returns a message explaining that no listings were found and suggests broadening the description, increasing the budget, or removing the size filter. |
| `suggest_outfit`  | Wardrobe is empty                | The agent gives general styling advice using common basics instead of crashing.                                                                                 |
| `create_fit_card` | Outfit input is empty or missing | The tool returns the message: `"Cannot create a fit card because the outfit suggestion is empty or missing."`                                                   |

### Example failure test

For this query:

```text
designer ballgown size XXS under $5
```

`search_listings` returns:

```python
[]
```

The agent stops early and returns an error message. It does not call `suggest_outfit` or `create_fit_card`.

---

## Example Interaction

User query:

```text
vintage graphic tee under $30
```

The agent parses the query and calls:

```python
search_listings("vintage graphic tee", size=None, max_price=30.0)
```

If results are found, the top item is stored as `session["selected_item"]`.

Then the agent calls:

```python
suggest_outfit(session["selected_item"], wardrobe)
```

The outfit suggestion is stored in `session["outfit_suggestion"]`.

Finally, the agent calls:

```python
create_fit_card(session["outfit_suggestion"], session["selected_item"])
```

The user sees the selected listing, the outfit idea, and a final shareable fit card.

---

## How to Run

Create and activate a virtual environment:

```bash
py -m venv .venv
source .venv/Scripts/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```text
GROQ_API_KEY=your_key_here
```

Run the app:

```bash
py app.py
```

Open the local URL shown in the terminal.

---

## Testing

Run the tool tests with:

```bash
pytest tests/
```

Expected result:

```text
5 passed
```

I tested the following failure modes:

1. `search_listings("designer ballgown", size="XXS", max_price=5)` returns `[]`.
2. `suggest_outfit()` works with an empty wardrobe and returns general styling advice.
3. `create_fit_card("", item)` returns a descriptive error message instead of crashing.

---

## Spec Reflection

The planning spec helped me decide the exact inputs, outputs, and failure behavior for each tool before writing the implementation. This made the agent loop easier to build because I already knew what each tool should return and when the workflow should stop.

One implementation detail changed during coding: I used a simple rule-based parser in `agent.py` to extract size and price from the user's query instead of using the LLM. I chose this because it was easier to test and more predictable for the required demo queries.





