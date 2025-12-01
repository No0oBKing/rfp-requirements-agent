PROMPT = (
    "You are a meticulous evaluator. Given the RFP document text and an existing structured extraction, "
    "return the SAME structure but with confidence values filled for each item.\n"
    "- Do not drop, add, or rename fields.\n"
    "- Keep all text, quantities, and metadata exactly as provided unless a confidence value is obviously incorrect.\n"
    "- Set confidence in [0,1]; 0.8-0.95 for explicit statements, 0.5-0.7 for implied, 0-0.4 if uncertain.\n"
    "- Clamp values to the range and prefer one decimal place."
)
