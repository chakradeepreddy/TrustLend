# src/decide.py  (FAKE version: same answer every time. Replaced in Step 4.)

def decide(applicant: dict) -> dict:
    """applicant: one row, with the same column names as the CSV."""
    return {
        "decision": "REVIEW",           # "APPROVE" | "DENY" | "REVIEW"
        "model_says": "APPROVE",         # what the plain AI would have done
        "p_default": 0.017,              # risk of not repaying, 0 to 1
        "unsure": False,                 # Check 1 fired?
        "unfamiliar": True,              # Check 2 fired?
        "familiarity_distance": 1.90,    # bigger = more unusual
        "reasons": ["age is higher than 99.5% of past applicants",
                    "MonthlyIncome is higher than 99.5% of past applicants"],
        "neighbours": [                  # the 5 most similar past applicants
            {"age": 56, "MonthlyIncome": 110775, "outcome": "repaid"},
        ],
    }
