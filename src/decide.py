# src/decide.py (FAKE version: same answer every time. Unblocks Streamlit app.)
def decide(applicant: dict) -> dict:
    return {
        "decision": "REVIEW",
        "model_says": "APPROVE",
        "p_default": 0.017,
        "unsure": False,
        "unfamiliar": True,
        "familiarity_distance": 1.90,
        "reasons": [
            "age is higher than 99.5% of past applicants",
            "MonthlyIncome is higher than 99.5% of past applicants"
        ],
        "neighbours": [
            {"age": 56, "MonthlyIncome": 110775, "outcome": "repaid"}
        ]
    }
