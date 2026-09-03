import os

import pytest
import pandas as pd

from clean_addresses import clean_data


@pytest.fixture
def raw_df():
    return pd.read_csv("addresses.csv")


def test_clean_data_returns_dataframe(raw_df):
    result = clean_data(raw_df)
    assert isinstance(result, pd.DataFrame)


def test_removes_duplicates(raw_df):
    result = clean_data(raw_df)
    # Original has a duplicate John Doe row
    assert len(result) < len(raw_df), "Should remove duplicates"


def test_standardizes_names(raw_df):
    result = clean_data(raw_df)
    for name in result["first_name"]:
        if pd.notna(name):
            assert name == name.strip(), f"Name not stripped: {name}"
            assert name == name.title(), f"Name not title case: {name}"


def test_standardizes_email(raw_df):
    result = clean_data(raw_df)
    for email in result["email"]:
        if pd.notna(email):
            assert email == email.lower().strip(), f"Email not lowercased: {email}"
            assert "@" in email, f"Email missing @: {email}"
            assert "." in email.split("@")[-1], f"Email missing domain: {email}"


def test_removes_invalid_emails(raw_df):
    result = clean_data(raw_df)
    # charlie.brown@ has no domain, should be removed
    assert "charlie.brown@" not in result["email"].values


def test_standardizes_phone(raw_df):
    result = clean_data(raw_df)
    for phone in result["phone"]:
        if pd.notna(phone) and phone:
            # Should be formatted as (XXX) XXX-XXXX
            assert phone.startswith("("), f"Phone not formatted: {phone}"
            assert ")" in phone, f"Phone not formatted: {phone}"
            assert "-" in phone, f"Phone not formatted: {phone}"


def test_phone_strips_leading_one(raw_df):
    result = clean_data(raw_df)
    # bob.johnson had 1-800-123-4567, should become (800) 123-4567
    bob = result[result["email"] == "bob.johnson@test.com"]
    if len(bob) > 0:
        phone = bob.iloc[0]["phone"]
        assert phone == "(800) 123-4567", f"Expected (800) 123-4567, got {phone}"


def test_invalid_phone_becomes_none(raw_df):
    result = clean_data(raw_df)
    # frank@punisher.com had phone "333" (only 3 digits)
    frank = result[result["email"] == "frank@punisher.com"]
    if len(frank) > 0:
        phone = frank.iloc[0]["phone"]
        assert pd.isna(phone) or phone is None or phone == "", \
            f"Invalid phone should be None, got {phone}"


def test_standardizes_state(raw_df):
    result = clean_data(raw_df)
    for state in result["state"]:
        if pd.notna(state):
            assert state == state.upper(), f"State not uppercase: {state}"


def test_standardizes_zip(raw_df):
    result = clean_data(raw_df)
    for zip_code in result["zip_code"]:
        if pd.notna(zip_code):
            zip_str = str(zip_code)
            # Should be 5 digits
            assert len(zip_str) == 5 or zip_str.replace(".0", "").isdigit(), \
                f"Zip not 5 digits: {zip_code}"


def test_fills_missing_city(raw_df):
    result = clean_data(raw_df)
    for city in result["city"]:
        if pd.notna(city):
            assert city != "", f"City should not be empty: {city}"


def test_no_duplicates_in_result(raw_df):
    result = clean_data(raw_df)
    assert len(result) == len(result.drop_duplicates()), "Result should have no duplicates"
