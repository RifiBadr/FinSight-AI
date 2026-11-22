import re

# words analysts use -> words the reports actually use
SYNONYMS = {
    "capex": "purchases of property plant and equipment",
    "capital expenditure": "purchases of property plant and equipment",
    "pp&e": "property plant and equipment net",
    "ppne": "property plant and equipment net",
    "cash flow statement": "statements of cash flows operating investing financing activities",
    "balance sheet": "balance sheets total assets total liabilities equity",
    "statement of financial position": "balance sheets total assets total liabilities equity",
    "income statement": "statements of operations net revenue net income",
    "statement of income": "statements of operations net revenue net income",
    "p&l": "statements of operations net revenue net income",
    "revenue": "net sales total revenues",
    "cogs": "cost of sales",
    "gross margin": "gross profit cost of sales",
    "operating margin": "operating income net sales",
    "quick ratio": "current assets cash marketable securities accounts receivable current liabilities",
    "liquidity": "cash and cash equivalents liquidity capital resources",
    "dividend": "dividends paid per share",
    "debt securities": "securities registered pursuant to section 12(b) trading symbol exchange",
}


def expand_query(question):
    text = question.lower()

    # reports write "2018", not "FY2018" or "FY18"
    text = re.sub(r"fy\s?(\d{4})", r"\1", text)
    text = re.sub(r"fy\s?(\d{2})\b", r"20\1", text)

    for term, words in SYNONYMS.items():
        if term in text:
            text += " " + words
    return text


if __name__ == "__main__":
    print(expand_query("What is the FY2018 capital expenditure for 3M? Use the cash flow statement."))
