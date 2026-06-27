"""
One-time transform: converts the raw Kaggle multilingual ticket dataset
into this project's tickets.csv schema (ticket_id, category, priority,
description, resolution).

Run once:
    python data/transform_dataset.py

Source: aa_dataset-tickets-multi-lang-5-2-50-version.csv
(Tobias Bück multilingual customer support tickets, Kaggle)
"""

import re
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
SOURCE_FILE = DATA_DIR / "raw_tickets_source.csv"
OUTPUT_FILE = DATA_DIR / "tickets.csv"

# Maps the dataset's `queue` values onto this project's TICKET_CATEGORIES
# (see app/config.py). Anything not listed here falls back to "Other".
QUEUE_TO_CATEGORY = {
    "Technical Support": "Performance Issue",
    "IT Support": "Server Down",
    "Service Outages and Maintenance": "Server Down",
    "Product Support": "Performance Issue",
    "Billing and Payments": "Other",
    "Customer Service": "Other",
    "Returns and Exchanges": "Other",
    "Sales and Pre-Sales": "Other",
    "Human Resources": "Other",
    "General Inquiry": "Other",
}


def clean_field(text) -> str:
    """Strip escaped newlines, placeholder tokens, and excess whitespace."""
    if pd.isna(text):
        return ""
    text = str(text)
    text = text.replace("\\n", " ").replace("\n", " ")
    text = re.sub(r"<name>|<company>|<email>|<phone>", "", text)  # anonymization placeholders
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def transform() -> pd.DataFrame:
    df = pd.read_csv(SOURCE_FILE)

    # English only — keeps the corpus consistent for embedding + LLM prompting
    df = df[df["language"] == "en"].copy()

    # Drop rows with no usable answer (can't be a "resolution" without one)
    df = df[df["answer"].notna()].copy()

    df["description"] = df.apply(
        lambda r: clean_field(r["subject"]) + ". " + clean_field(r["body"])
        if clean_field(r["subject"])
        else clean_field(r["body"]),
        axis=1,
    )
    df["resolution"] = df["answer"].apply(clean_field)
    df["category"] = df["queue"].map(QUEUE_TO_CATEGORY).fillna("Other")
    df["priority"] = df["priority"].str.capitalize()

    df = df[df["description"].str.len() > 10]
    df = df[df["resolution"].str.len() > 10]

    df = df.reset_index(drop=True)
    df["ticket_id"] = [f"INC{i+1:05d}" for i in range(len(df))]

    return df[["ticket_id", "category", "priority", "description", "resolution"]]


if __name__ == "__main__":
    result = transform()
    result.to_csv(OUTPUT_FILE, index=False)
    print(f"[OK] Wrote {len(result)} tickets to {OUTPUT_FILE}")
    print()
    print("Category distribution:")
    print(result["category"].value_counts())
    print()
    print("Priority distribution:")
    print(result["priority"].value_counts())
