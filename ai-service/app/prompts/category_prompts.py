CATEGORY_SYSTEM_PROMPT = """You are a financial transaction categorization engine.
Categorize the expense into EXACTLY ONE of the following valid categories:
1. Food & Dining
2. Groceries
3. Transportation
4. Entertainment
5. Shopping
6. Utilities
7. Travel
8. Healthcare
9. Housing & Rent
10. Other

Output JSON:
{
  "category": "Food & Dining",
  "confidence": 0.95
}
Return ONLY valid JSON.
"""

def build_category_prompt(merchant: str = None, note: str = None, amount: float = None) -> str:
    desc = []
    if merchant:
        desc.append(f"Merchant: {merchant}")
    if note:
        desc.append(f"Note/Description: {note}")
    if amount is not None:
        desc.append(f"Amount: {amount}")
    return "Categorize this transaction:\n" + "\n".join(desc)
