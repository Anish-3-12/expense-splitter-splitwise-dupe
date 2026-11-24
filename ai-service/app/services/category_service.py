import re
from app.core.logging import logger
from app.providers.ollama_provider import ollama_provider
from app.schemas.category import CategorizeRequest, CategorizeResponse
from app.prompts.category_prompts import CATEGORY_SYSTEM_PROMPT, build_category_prompt

MERCHANT_RULES = {
    # Food & Dining
    "swiggy": "Food & Dining",
    "zomato": "Food & Dining",
    "mcdonald": "Food & Dining",
    "starbucks": "Food & Dining",
    "domino": "Food & Dining",
    "pizza hut": "Food & Dining",
    "kfc": "Food & Dining",
    "burger king": "Food & Dining",
    "subway": "Food & Dining",
    "cafe": "Food & Dining",
    "restaurant": "Food & Dining",
    "diner": "Food & Dining",
    "bar": "Food & Dining",
    "pub": "Food & Dining",

    # Groceries
    "blinkit": "Groceries",
    "zepto": "Groceries",
    "instamart": "Groceries",
    "bigbasket": "Groceries",
    "dmart": "Groceries",
    "nature basket": "Groceries",
    "supermarket": "Groceries",
    "grocery": "Groceries",

    # Transportation
    "uber": "Transportation",
    "ola": "Transportation",
    "rapido": "Transportation",
    "metro": "Transportation",
    "irctc": "Transportation",
    "railway": "Transportation",
    "petrol": "Transportation",
    "fuel": "Transportation",
    "shell": "Transportation",
    "hpcl": "Transportation",
    "bpcl": "Transportation",

    # Entertainment
    "netflix": "Entertainment",
    "spotify": "Entertainment",
    "hotstar": "Entertainment",
    "prime video": "Entertainment",
    "bookmyshow": "Entertainment",
    "pvr": "Entertainment",
    "inox": "Entertainment",
    "steam": "Entertainment",
    "playstation": "Entertainment",

    # Shopping
    "amazon": "Shopping",
    "flipkart": "Shopping",
    "myntra": "Shopping",
    "zara": "Shopping",
    "h&m": "Shopping",
    "uniqlo": "Shopping",
    "ikea": "Shopping",

    # Utilities
    "electricity": "Utilities",
    "bescom": "Utilities",
    "water": "Utilities",
    "broadband": "Utilities",
    "wifi": "Utilities",
    "airtel": "Utilities",
    "jio": "Utilities",
    "vi": "Utilities",
    "gas": "Utilities",

    # Travel
    "makemytrip": "Travel",
    "airbnb": "Travel",
    "oyo": "Travel",
    "hotel": "Travel",
    "resort": "Travel",
    "indigo": "Travel",
    "air india": "Travel",
    "agoda": "Travel",
    "booking.com": "Travel",

    # Healthcare
    "apollo": "Healthcare",
    "pharmeasy": "Healthcare",
    "1mg": "Healthcare",
    "netmeds": "Healthcare",
    "hospital": "Healthcare",
    "clinic": "Healthcare",
    "pharmacy": "Healthcare",
    "medplus": "Healthcare",

    # Housing & Rent
    "landlord": "Housing & Rent",
    "nobroker": "Housing & Rent",
    "magicbricks": "Housing & Rent",
    "housing": "Housing & Rent"
}

KEYWORD_RULES = {
    # Travel & vehicle rentals
    "Travel": ["suv rental", "car rental", "vehicle rental", "bike rental", "snow chains", "stay", "room", "flight", "tour", "visa", "cottage", "camp", "chalet", "resort"],
    "Transportation": ["cab", "auto", "taxi", "toll", "parking", "train", "bus", "flight ticket"],
    # Residential housing rent (distinguished from vehicle/equipment rentals)
    "Housing & Rent": ["apartment rent", "flat rent", "house rent", "home rent", "room rent", "monthly rent", "office rent", "property rent", "lease", "landlord", "flat", "apartment"],
    "Food & Dining": ["lunch", "dinner", "breakfast", "snacks", "pizza", "burger", "biryani", "drinks", "beers", "cocktail", "tea", "coffee", "dessert"],
    "Groceries": ["milk", "eggs", "bread", "vegetables", "fruits", "curd", "ration", "flour", "rice", "dal"],
    "Entertainment": ["movie", "cinema", "concert", "match", "game", "bowling"],
    "Shopping": ["shoes", "clothes", "shirt", "pants", "dress", "watch", "laptop", "gadget"],
    "Utilities": ["bill", "recharge", "maintenance", "wifi bill", "power bill"],
    "Healthcare": ["medicine", "doctor", "tablet", "test", "consultation", "dental", "blood test"]
}

class CategoryService:
    """
    Hybrid categorization:
    1. Instant rule/merchant matching (0ms latency, zero RAM/CPU load).
    2. Keyword heuristic matching.
    3. LLM (Ollama) fallback for ambiguous descriptions.
    """

    async def categorize(self, req: CategorizeRequest) -> CategorizeResponse:
        search_text = f"{req.merchant or ''} {req.note or ''}".lower().strip()

        # 1. Check Merchant Rules
        for merchant_key, cat in MERCHANT_RULES.items():
            if merchant_key in search_text:
                return CategorizeResponse(category=cat, confidence=0.98, method="RULE")

        # 2. Check for vehicle/equipment rentals first to prevent miscategorization as housing
        if any(vr in search_text for vr in ["suv rental", "car rental", "vehicle rental", "auto rental", "snow chains"]):
            return CategorizeResponse(category="Travel", confidence=0.95, method="KEYWORD")

        # 3. Check Keyword Rules
        for cat, keywords in KEYWORD_RULES.items():
            for kw in keywords:
                if re.search(rf"\b{re.escape(kw)}\b", search_text):
                    # Guard: If "rent" matched but context is vehicle/equipment, do not classify as Housing & Rent
                    if cat == "Housing & Rent" and any(v in search_text for v in ["car", "suv", "vehicle", "bike", "ski", "snow"]):
                        continue
                    return CategorizeResponse(category=cat, confidence=0.90, method="KEYWORD")

        # 4. Check for standalone "rent"
        if re.search(r"\brent\b", search_text) and not any(v in search_text for v in ["car", "suv", "vehicle", "bike", "ski", "equipment"]):
            return CategorizeResponse(category="Housing & Rent", confidence=0.92, method="KEYWORD")

        # 3. LLM classification if ambiguous and non-empty
        if len(search_text) >= 3:
            try:
                prompt = build_category_prompt(
                    merchant=req.merchant,
                    note=req.note,
                    amount=float(req.amount) if req.amount else None
                )
                structured = await ollama_provider.generate_structured(
                    prompt=prompt,
                    system_prompt=CATEGORY_SYSTEM_PROMPT
                )
                cat = structured.get("category", "Other")
                conf = float(structured.get("confidence", 0.85))
                return CategorizeResponse(category=cat, confidence=conf, method="LLM")
            except Exception as e:
                logger.info(f"Ollama categorization skipped/failed: {e}")

        # 4. Default fallback
        return CategorizeResponse(category="Other", confidence=0.50, method="DEFAULT")

category_service = CategoryService()
