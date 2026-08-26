"""
category_predictor.py

Implements a simple, transparent KEYWORD-BASED category prediction
system for the Smart Expense Tracker.

IMPORTANT: This is NOT a machine learning model. It is a rule-based
/ keyword-matching approach used to intelligently pre-fill a
category for the user based on the words used in the expense
description. It is deliberately simple, explainable, and easy to
present during a college viva.
"""

# Mapping of category -> list of keywords that suggest that category.
# All matching is done in lowercase, so the mapping keys/values are
# kept lowercase here for clarity (comparison is case-insensitive).
CATEGORY_KEYWORDS = {
    "Food": [
        "pizza", "burger", "restaurant", "food",
        "swiggy", "zomato", "lunch", "dinner",
        "breakfast", "cafe", "coffee", "snack",
        "meal", "dominos", "kfc", "mcdonald",
    ],

    "Travel": [
        "uber", "ola", "bus", "train",
        "taxi", "fuel", "petrol", "diesel",
        "travel", "auto", "flight", "cab",
        "metro", "toll", "parking", "ticket",
    ],

    "Shopping": [
        "amazon", "flipkart", "clothes",
        "dress", "shoes", "shopping", "mall",
        "myntra", "ajio", "fashion",
    ],

    "Bills": [
        "electricity", "water", "internet",
        "recharge", "rent", "bill", "wifi",
        "broadband", "gas", "maintenance",
    ],

    "Education": [
        "book", "course", "college",
        "exam", "fees", "education", "tuition",
        "school", "university", "stationery",
    ],

    "Entertainment": [
        "movie", "cinema", "netflix",
        "spotify", "game", "concert", "pvr",
        "amazon prime", "hotstar", "youtube",
        "outing", "party",
    ],

    "Health": [
        "medicine", "doctor", "hospital",
        "pharmacy", "health", "clinic",
        "dentist", "checkup", "medical",
    ],

    "Groceries": [
        "vegetables", "grocery", "milk",
        "rice", "fruits", "supermarket",
        "bigbasket", "groceries", "kirana",
    ],
}

DEFAULT_CATEGORY = "Other"


def predict_category(description: str) -> str:
    """
    Predict an expense category from its description using simple,
    case-insensitive keyword matching.

    Args:
        description: The free-text expense description entered by
            the user (e.g. "Uber ride to college").

    Returns:
        The predicted category name as a string. Falls back to
        "Other" when no keyword match is found.
    """
    if not description:
        return DEFAULT_CATEGORY

    text = description.lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return category

    return DEFAULT_CATEGORY
