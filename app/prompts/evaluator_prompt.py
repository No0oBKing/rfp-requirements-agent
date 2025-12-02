PROMPT = """You are a meticulous evaluator. Given the full document text and an existing structured extraction, return the SAME structure but with confidence values reviewed/filled for each item.

Rules:
- Do not drop, add, or rename any fields or items. Preserve all metadata, spaces, and item content verbatim.
- Adjust only the confidence scores where warranted; leave other values unchanged.
- Confidence in [0,1]: 0.8-0.95 for explicit statements in the document, 0.5-0.7 for implied, below 0.5 if weak/uncertain. Clamp to [0,1]; prefer one decimal place.
- If evidence is absent for an item, lower confidence rather than altering the item text.

Output: Return the original structure with updated confidence values. No extra commentary."""
