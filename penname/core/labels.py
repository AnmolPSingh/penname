"""Plain-language labels. The reader is a fundraiser, not a developer."""

ENTITY_LABELS = {
    "PERSON": "Name",
    "ORGANIZATION": "Organization",
    "EMAIL_ADDRESS": "Email address",
    "PHONE_NUMBER": "Phone number",
    "DATE_TIME": "Date",
    "LOCATION": "Place",
    "URL": "Web address",
    "US_SSN": "Social Security number",
    "CREDIT_CARD": "Card number",
    "IBAN_CODE": "Bank account",
    "IP_ADDRESS": "Computer address",
    "NRP": "Group or nationality",
    "DONATION_AMOUNT": "Gift amount",
    "WEALTH_RATING": "Wealth or capacity rating",
    "FUND_CODE": "Fund or appeal code",
    "CONSTITUENT_ID": "Constituent ID",
    "CUSTOM": "Added by you",
}


def entity_label(entity_type: str) -> str:
    return ENTITY_LABELS.get(entity_type, entity_type.replace("_", " ").title())


def certainty_label(score: float) -> str:
    if score >= 0.85:
        return "Very sure"
    if score >= 0.6:
        return "Fairly sure"
    return "Less sure, check this"
