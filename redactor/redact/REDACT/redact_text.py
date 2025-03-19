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
            parsed_address, _ = usaddress.tag(address)
            validated_addresses.append(address)
        except usaddress.RepeatedLabelError:
            continue
    
    return validated_addresses

class RedactText:
    global entities_to_redact
    entities_to_redact = set()
    
    @staticmethod
    def generate_list(pdf_path):
        global entities_to_redact
        pdf_document = fitz.open(pdf_path)
        nlp = spacy.load('en_core_web_md')
        
        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)
            text = " ".join([word[4] for word in page.get_text("words")])
            matcher = Matcher(nlp.vocab)
            
            re_patterns = {
                "phoneNumber": r'(?:\+?91[\s-]?)?[\s-]?\d{10}|(?:91[\s-]?)?\d{10}|(?:\+?91[\s-]?)?\d{3}[\s-]?\d{3}[\s-]?\d{4}',
                "passport": r"[A-Z]{1}[0-9]{7}|[A-Z]{2}[0-9]{6}|[A-Z]{3}[0-9]{5}|[A-Z]{1}[0-9]{6}",
                "ssn": r'(?:\d{3}[\s-]?\d{2}[\s-]\d{4})|(?:\d{9})',
                "pan": r'([A-Z]{3}[A|B|C|F|G|H|L|J|P|T|F][A-Z]{1}\d{4}[A-Z])',
                "aadhar": r'([2-9]{1}[0-9]{3}[\s-][0-9]{4}[\s-][0-9]{4}|[2-9]{1}[0-9]{3}[0-9]{4}[0-9]{4})',
                "card": r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}'
            }
            
            matcher.add("EMAIL", [[{"LIKE_EMAIL": True}]])
            matcher.add("URL", [[{"LIKE_URL": True}]])
            matcher.add("NAME", [[{"POS": "PROPN", "ENT_TYPE": "PERSON", "IS_ALPHA": True, "LENGTH": {">=": 2}, "OP": "+"}]])
            matcher.add("DATE", [[{"ENT_TYPE": "DATE"}]])
            
            doc = nlp(text)
            matches = matcher(doc)
            extracted_addresses = combined_address_extraction(str(doc))
            
            for address in extracted_addresses:
                entities_to_redact.add(address)
            
            for pattern in re_patterns.values():
                entities_to_redact.add(str(re.findall(pattern, text)).replace("[", "").replace("]", "").replace("'", ""))
            
            for match in matches:
                match_label = nlp.vocab.strings[match[0]]
                match_text = str(doc[match[1]:match[2]]).strip()
                
                if match_label == "NAME" and match_text.isdigit():
                    continue
                
                match_text = match_text.replace(",", "").replace(".", "")
                entities_to_redact.add(match_text)
                
        pdf_document.close()
    
    @staticmethod
    def redact(pdf_path, entities_to_redact, output_path):
        pdf_document = fitz.open(pdf_path)
        
        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)
            
            for entity in entities_to_redact:
                search_results = page.search_for(entity)
                if search_results:
                    for rect in search_results:
                        page.add_redact_annot(rect, fill=(0, 0, 0))
            
            page.apply_redactions()
        
        pdf_document.save(output_path)
        pdf_document.close()
    
    @staticmethod
    def display_entities():
        global entities_to_redact
        return entities_to_redact
