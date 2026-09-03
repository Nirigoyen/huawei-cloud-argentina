import re

import pandas as pd


def clean_phone(phone):
    if pd.isna(phone):
        return None
    digits = re.sub(r"\D", "", str(phone))
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        return None
    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"


def clean_zip(zip_code):
    if pd.isna(zip_code):
        return zip_code
    digits = re.sub(r"\D", "", str(zip_code))
    if not digits:
        return None
    return digits[:5].zfill(5)


def is_valid_email(email):
    if pd.isna(email):
        return False
    email = str(email).strip().lower()
    return bool(re.match(r"^[^@]+@[^@]+\.[^@]+$", email))


def clean_data(df):
    df = df.copy()

    # Standardize names
    for col in ["first_name", "last_name"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()

    # Standardize email
    df["email"] = df["email"].astype(str).str.strip().str.lower()
    df = df[df["email"].apply(is_valid_email)]

    # Standardize phone
    df["phone"] = df["phone"].apply(clean_phone)

    # Standardize state
    df["state"] = df["state"].astype(str).str.strip().str.upper()

    # Standardize zip
    df["zip_code"] = df["zip_code"].apply(clean_zip)

    # Fill missing city
    df["city"] = df["city"].astype(str).str.strip()
    df.loc[df["city"] == "", "city"] = "Unknown"
    df.loc[df["city"].str.lower() == "nan", "city"] = "Unknown"

    # Remove duplicates after cleaning
    df = df.drop_duplicates()

    return df.reset_index(drop=True)


if __name__ == "__main__":
    df = pd.read_csv("addresses.csv")
    original_count = len(df)
    cleaned = clean_data(df)
    cleaned.to_csv("cleaned_addresses.csv", index=False)
    print(f"Original rows: {original_count}")
    print(f"Cleaned rows: {len(cleaned)}")
    print(f"Rows removed: {original_count - len(cleaned)}")
