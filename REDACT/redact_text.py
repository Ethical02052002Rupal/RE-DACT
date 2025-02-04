import fitz
import spacy
import re
from spacy.matcher import Matcher
import usaddress
import string

def combined_address_extraction(raw_data):
    address_pattern = r"\d{1,5}\s[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Square|Sq|Parkway|Pkwy|Court|Ct|Place|Pl|Circle|Cir),?\s[\w\s]+,\s[A-Z]{2}\s\d{5}"
    probable_addresses = re.findall(address_pattern, raw_data)

    validated_addresses = []
    for address in probable_addresses:
        try:
            # Validate with usaddress
            parsed_address, _ = usaddress.tag(address)
            validated_addresses.append(address)
        except usaddress.RepeatedLabelError:
            continue

    return validated_addresses

class redact_text():

    def __init__(self, pdf_path, output_path):
        pdf_document = fitz.open(pdf_path)

        nlp = spacy.load('en_core_web_md')
        
        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)
            word_list = page.get_text("words")
            text = " ".join([word[4] for word in word_list])

            matcher = Matcher(nlp.vocab)

            re_patterns = {
                "phoneNumber_pattern" : r'(?:\+?91[\s-]?)?[\s-]?\d{10}|(?:91[\s-]?)?\d{10}|(?:\+?91[\s-]?)?\d{3}[\s-]?\d{3}[\s-]?\d{4}',
                "passport_pattern" : r"[A-Z]{1}[0-9]{7}|[A-Z]{2}[0-9]{6}|[A-Z]{3}[0-9]{5}|[A-Z]{1}[0-9]{6}",
                "ssn_pattern" : r'(?:\d{3}[\s-]?\d{2}[\s-]\d{4})|(?:\d{9})', #we will se letter
                "pan_pattern" : r'([A-Z]{3}[A|B|C|F|G|H|L|J|P|T|F][A-Z]{1}\d{4}[A-Z])',
                "addhar_pattern" : r'([2-9]{1}[0-9]{3}[\s-][0-9]{4}[\s-][0-9]{4}|[2-9]{1}[0-9]{3}[0-9]{4}[0-9]{4})',
                "card_pattern" : r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}'
            }

            email_patterns = [
                [{"LIKE_EMAIL": True}],  # Matches standard emails
                [{"TEXT": {"REGEX": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"}}]  # Extra regex validation
            ]
            url_patterns = [
                [{"LIKE_URL": True}],  # Matches standard URLs
                [{"TEXT": {"REGEX": r"(https?:\/\/)?(www\.)?[\w-]+\.[a-z]{2,6}(/\S*)?"}}]  # Extra regex validation
            ]
            honorifics = {"Mr.", "Mrs.", "Ms.", "Miss", "Dr.", "Prof.", "Sir", "Madam"}
            name_patterns = [
                [{"TEXT": {"NOT_IN": list(honorifics)}}, 
                 {"POS": "PROPN", "ENT_TYPE": "PERSON", "IS_ALPHA": True, "LENGTH": {">=": 2}, "OP": "+"}],  # Full names
                [{"ENT_TYPE": "PERSON", "IS_ALPHA": True, "LENGTH": {">=": 2}}]  # Single detected person entity
            ]
            date_patterns = [
                [{"ENT_TYPE": "DATE"}],  # Recognized DATE entity
                [{"SHAPE": "dd/dd/dddd"}],  # Matches dates like 12/25/2024
                [{"SHAPE": "dd-dd-dddd"}],  # Matches 12-25-2024
                [{"SHAPE": "dd Month dddd"}],  # Matches 25 December 2024
                [{"TEXT": {"REGEX": r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"}}]  # Extra regex validation
            ]
            matcher.add("EMAIL", email_patterns)
            matcher.add("URL", url_patterns)
            matcher.add("NAME", name_patterns)
            matcher.add("DATE", date_patterns)
            doc = nlp(text)
            # print(doc)
            matches = matcher(doc)
            # for match in matches:
            #     print (nlp.vocab.strings[match[0]], doc[match[1]:match[2]])

            extracted_addresses = combined_address_extraction(str(doc))
            # print("Validated Addresses:")

            #entities_to_redact = {ent.text for ent in doc.ents}
            entities_to_redact = set()
            for address in extracted_addresses:
                entities_to_redact.add(address)
            for label, pattern in re_patterns.items():
                # print(re.findall(pattern, text))
                entities_to_redact.add(str(re.findall(pattern, text)).replace("[", "").replace("]", "").replace("'", ""))
            #print(type(entities_to_redact))
            # for match in matches:
            #     if nlp.vocab.strings[match[0]] == "NAME" and str(doc[match[1]:match[2]]).isdigit():
            #         pass
            #     else:  
            #         entities_to_redact.add(str(doc[match[1]:match[2]]).replace(",", "").replace(".", ""))
            # print(entities_to_redact)

            for match in matches:
                match_label = nlp.vocab.strings[match[0]]  # Get matched entity type
                match_text = str(doc[match[1]:match[2]])   # Extract matched text

                # match_text = match_text.translate(str.maketrans("", "", string.punctuation))

                # match_text = " ".join([word for word in match_text.split() if len(word) > 1])

                # Special handling for names (allow periods, remove other punctuation)
                if match_label == "NAME":
                    if match_text.isdigit():  # Ignore numeric names
                        continue
                    match_text = "".join([char if char.isalpha() or char == "." or char.isspace() else "" for char in match_text])
                
                else:
                    # For all other entities, remove commas and periods
                    match_text = match_text.replace(",", "").replace(".", "")

                entities_to_redact.add(match_text.strip())  # Add cleaned text to the set
                entities_to_redact = {item for item in entities_to_redact if len(item) > 1}

            print(entities_to_redact)
            
            for entity in entities_to_redact:
                search_results = page.search_for(entity)
                
                if search_results:
                    for rect in search_results:
                        page.add_redact_annot(rect, fill=(0, 0, 0))
            
            page.apply_redactions()
        
        pdf_document.save(output_path)
        pdf_document.close()