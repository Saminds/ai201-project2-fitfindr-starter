# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
This tool searches the mock secondhand clothing listings dataset for items that match the user's requested description, size, and maximum price. It filters the available listings and returns the best matching thrift items.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): A natural language description of the item the user wants, such as "vintage graphic tee", "black denim jacket", or "chunky sneakers".
- `size` (str): The user's requested clothing size, such as "S", "M", "L", or "XL". If the user does not specify a size, this can be None.
- `max_price` (float): The highest price the user is willing to pay. For example, if the user says “under $30,” then max_price is 30.0.

**What it returns:**
It returns a list of matching listing dictionaries. Each listing can include fields such as id, title, description, category, style_tags, size, condition, price, colors, brand, and platform. The list should be sorted so the most relevant or useful matches appear first.

**What happens if it fails or returns nothing:**
If no listings match the user's request, the tool returns an empty list []. The agent should not continue to suggest_outfit or create_fit_card because there is no selected item. Instead, the agent should tell the user that no matching listings were found and suggest loosening the search, such as increasing the budget, removing the size filter, or using a broader description.

---

### Tool 2: suggest_outfit

**What it does:**
This tool takes a selected thrift item and the user's wardrobe, then suggests one or more complete outfit ideas. It helps the user understand how the thrifted item could fit with clothes they already own.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): The selected listing from search_listings. It contains information such as the item title, category, colors, style tags, price, condition, brand, and platform.
- `wardrobe` (dict): The user's existing wardrobe data. It contains wardrobe items that can be used to build an outfit around the selected thrift item.

**What it returns:**
It returns a natural-language outfit suggestion as a string. The suggestion should mention the thrifted item and, when possible, combine it with items from the user's wardrobe. It should be specific, practical, and style-focused.

**What happens if it fails or returns nothing:**
If the wardrobe is empty or minimal, the tool should still return a useful outfit suggestion using common basics instead of crashing. For example, it can suggest pairing the thrifted item with jeans, sneakers, boots, a basic jacket, or neutral layers. If the tool cannot generate an outfit, the agent should explain that the outfit suggestion could not be created and ask the user to add more wardrobe details.

---

### Tool 3: create_fit_card

**What it does:**
This tool creates a short, shareable outfit description based on the selected thrift item and the outfit suggestion. The result should sound like a caption someone might post on Instagram or TikTok.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): The outfit suggestion created by suggest_outfit.
- `new_item` (dict): The selected thrift listing used in the outfit.

**What it returns:**
It returns a short social-media-style fit card or caption as a string. The fit card should mention the thrifted item and capture the overall style of the outfit in a fun, natural way.

**What happens if it fails or returns nothing:**
If the outfit input is missing, empty, or incomplete, the tool should return a clear error message instead of crashing. The agent should tell the user that a fit card cannot be created until there is a valid outfit suggestion.
---

### Additional Tools (if any)

No additional tools will be implemented for the required version of this project. I will focus on the three required tools first: search_listings, suggest_outfit, and create_fit_card.

---

## Planning Loop

**How does your agent decide which tool to call next?**
The agent starts with the user's request and extracts the item description, size, and maximum price. First, it calls search_listings(description, size, max_price).

After search_listings returns, the agent checks whether the result list is empty. If the list is empty, the agent stores an error message in the session and stops early. It does not call suggest_outfit or create_fit_card because there is no item to style.

If listings are found, the agent stores the full search result list in the session and chooses the first result as the selected item. Then it calls suggest_outfit(selected_item, wardrobe).

After the outfit suggestion is created, the agent stores it in the session. If the outfit suggestion is empty or contains an error message, the agent stops and returns that message to the user.

If the outfit suggestion is valid, the agent calls create_fit_card(outfit_suggestion, selected_item). Finally, the agent stores the fit card in the session and returns the selected listing, outfit suggestion, and fit card to the user.

The agent is done when it has either created a complete fit card or reached an error branch that prevents the next tool from being useful.
---

## State Management

**How does information from one tool get passed to the next?**
The agent uses a session dictionary to store information during one user interaction. This session keeps track of the original query, the search results, the selected item, the outfit suggestion, the fit card, and any error message.

The data from one tool becomes the input for the next tool. For example, search_listings returns a list of matching items. The agent stores that list in session["search_results"] and stores the first item in session["selected_item"]. Then session["selected_item"] is passed into suggest_outfit.

Next, the outfit suggestion is stored in session["outfit_suggestion"]. That value is then passed into create_fit_card along with session["selected_item"]. This lets the agent complete a multi-step workflow without asking the user to re-enter the same information.
The session will track:

query: the user's original search information
search_results: the list returned by search_listings
selected_item: the item chosen from the search results
outfit_suggestion: the result from suggest_outfit
fit_card: the result from create_fit_card
error: any failure message that stops the workflow
---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query |The agent tells the user that no matching listings were found. It suggests trying a broader description, increasing the budget, or removing the size filter. The agent stops early and does not call the other tools.|
| suggest_outfit | Wardrobe is empty |The agent still gives general styling advice using common clothing basics. It does not pretend the user owns specific wardrobe items.|
| create_fit_card | Outfit input is missing or incomplete |The agent returns a clear message saying that a fit card cannot be created without a valid outfit suggestion. It does not crash or return a blank caption. |

---

## Architecture
User query | v Planning Loop | |-- Extract description, size, and max_price | |-- Call search_listings(description, size, max_price) | | | |-- If results == []: | | session["error"] = "No listings found. Try a broader search." | | return session | | | |-- If results found: | session["search_results"] = results | session["selected_item"] = results[0] | |-- Call suggest_outfit(session["selected_item"], wardrobe) | | | |-- If wardrobe is empty: | | return general styling advice | | | |-- If outfit suggestion fails: | | session["error"] = "Could not create outfit suggestion." | | return session | | | v | session["outfit_suggestion"] = outfit_suggestion | |-- Call create_fit_card(session["outfit_suggestion"], session["selected_item"]) | | | |-- If outfit input is missing: | | session["error"] = "Cannot create fit card without an outfit." | | return session | | | v | session["fit_card"] = fit_card | v Return selected listing, outfit suggestion, and fit card to user

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**
I will use ChatGPT to help implement each required tool one at a time. For search_listings, I will give ChatGPT the Tool 1 section of this planning document and ask it to implement search_listings(description, size, max_price) using load_listings() from utils/data_loader.py. I will verify the result by checking that it filters by description, size, and max price, and that it returns an empty list when no listings match.

For suggest_outfit, I will give ChatGPT the Tool 2 section and ask it to implement the function using the Groq API. I will verify that the function accepts new_item and wardrobe, returns a string, and handles an empty wardrobe without crashing.

For create_fit_card, I will give ChatGPT the Tool 3 section and ask it to implement a function that creates a short caption using the Groq API. I will verify that it accepts outfit and new_item, returns a string, produces different captions for different inputs, and returns a clear error message if the outfit input is empty.

Before trusting the tools, I will run each one directly with hardcoded inputs and also write pytest tests for the main success and failure cases.
**Milestone 4 — Planning loop and state management:**
I will use ChatGPT to help implement the planning loop in agent.py. I will give it the Planning Loop section, the State Management section, and the Architecture diagram from this document. I expect it to produce a run_agent() implementation that calls the tools conditionally, stores intermediate results in a session dictionary, and stops early when search returns no results.

I will verify the output by checking that the agent does not call all three tools blindly. Specifically, I will test a successful query and confirm that selected_item, outfit_suggestion, and fit_card are all stored in the session. Then I will test an impossible query and confirm that session["error"] is set and session["fit_card"] remains None.
---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
The agent first identifies the user's search request. It extracts:

description = "vintage graphic tee"
size = None, because the user did not give a specific size
max_price = 30.0

Then the agent calls:

search_listings("vintage graphic tee", size=None, max_price=30.0)

This tool searches the mock listings dataset for matching thrift items.

**Step 2:**
If search_listings returns matching items, the agent stores them in session["search_results"]. The agent then selects the first result and stores it in session["selected_item"].
For example, the selected item might be a faded vintage band tee from Depop for $22.

Then the agent calls:

suggest_outfit(session["selected_item"], wardrobe)

The selected item is passed into the outfit tool along with the user's wardrobe.
**Step 3:**
suggest_outfit returns a styling suggestion. For example, it might suggest pairing the vintage graphic tee with baggy jeans, chunky sneakers, and a casual jacket for a relaxed streetwear look.

The agent stores this result in session["outfit_suggestion"].

Then the agent calls:

create_fit_card(session["outfit_suggestion"], session["selected_item"])

This tool uses the selected thrift item and the outfit suggestion to create a short shareable caption.

**Final output to user:**
The user sees three pieces of information:

The selected thrift listing, including title, price, size, condition, and platform.
A complete outfit suggestion explaining how to style the item.
A short fit card/caption, such as:

“Found this vintage graphic tee under $30 and styled it with baggy denim and chunky sneakers for an easy thrifted streetwear look. Low effort, high personality.”
