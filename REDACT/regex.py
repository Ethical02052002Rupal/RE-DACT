import re

text = """
John Doe, born on 01-15-1985, can be reached at john.doe@example.com or +91-974-982-2918.
His SSN is 123-45-6789, and his credit card number is 1234-5678-9012-3456.
"""
star ="******"

# Example patterns
patterns = {
    "email_pattern" : r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',   #regular expression for email id
    "phoneNumber_pattern" : r'(?:\+?91[\s-]?)?[\s-]?\d{10}|(?:91[\s-]?)?\d{10}|(?:\+?91[\s-]?)?\d{3}[\s-]?\d{3}[\s-]?\d{4}',
    "dob_pattern" : r'(?:0[1-9]|1[0-2])[/-](?:0[1-9]|[12][0-9]|3[01])[/-]\d{4}',
    "passport_pattern" : r"[A-Z]{1}[0-9]{7}|[A-Z]{2}[0-9]{6}|[A-Z]{3}[0-9]{5}|[A-Z]{1}[0-9]{6}",
    "race_pattern": r"(White|Black|Asian|Hispanic|Other)",
    "religion_pattern" : r"(Christianity|Islam|Hinduism|Buddhism|Other|Hindu)", #NLP will be better
    "gender_pattern" : r"(Male|Female|Non-binary|Other)",
    "ssn_pattern" : r'(?:\d{3}[\s-]?\d{2}[\s-]\d{4})|(?:\d{9})', #we will se letter
    "pan_pattern" : r'([A-Z]{3}[A|B|C|F|G|H|L|J|P|T|F][A-Z]{1}\d{4}[A-Z])',
    "addhar_pattern" : r'([2-9]{1}[0-9]{3}[\s-][0-9]{4}[\s-][0-9]{4}|[2-9]{1}[0-9]{3}[0-9]{4}[0-9]{4})',
    "card_pattern" : r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}'
}

result = text
# Finding matches
for label, pattern in patterns.items():
    matches = re.findall(pattern, text)
    result = re.sub(pattern,star, result)
    print(f"{label}: {matches}")
    print(result)
