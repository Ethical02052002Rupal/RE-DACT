import cv2
import pytesseract
from pytesseract import Output
import numpy as np
import re
import spacy
import os

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
nlp = spacy.load("en_core_web_md")

class RedactImage:
    
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    @staticmethod
    def detect_faces(image_path, face_output_dir="faces"):
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Error: Unable to load image at {image_path}")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = RedactImage.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        face_coords = []

        for i, (x, y, w, h) in enumerate(faces):
            face = image[y:y+h, x:x+w]
            face_path = os.path.join(face_output_dir, f"face.jpg")
            print(face_path)
            cv2.imwrite(face_path, face)
            face_coords.append((x, y, w, h))

        return face_coords

    @staticmethod
    def extract_pii(image_path):
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Error: Unable to load image.")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        d = pytesseract.image_to_data(gray, output_type=Output.DICT)

        pii_patterns = {
            "email": r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
            "phone": r'(?:\+?91[\s-]?)?\d{10}',
            "dob": r'\d{2}[-/]\d{2}[-/]\d{4}',
            "passport": r"[A-Z]{1}[0-9]{7}|[A-Z]{2}[0-9]{6}",
            "ssn": r'\d{3}[\s-]?\d{2}[\s-]?\d{4}',
            "aadhaar": r'\d{4}[\s-]?\d{4}[\s-]?\d{4}',
            "credit_card": r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}',
            "pincode": r"\b\d{6}\b"
        }

        detected_texts = []
        list_pii = []
        text_coords = []

        for i in range(len(d['level'])):
            text = d['text'][i].strip()
            if text:
                detected_texts.append(text)
                for pattern in pii_patterns.values():
                    if re.search(pattern, text, re.IGNORECASE):
                        list_pii.append(text)
                        text_coords.append((d['left'][i], d['top'][i], d['width'][i], d['height'][i]))
                        break

        extracted_text = pytesseract.image_to_string(gray)
        doc = nlp(extracted_text)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                list_pii.append(ent.text)
                for i in range(len(d['level'])):
                    if d['text'][i].strip() == ent.text:
                        text_coords.append((d['left'][i], d['top'][i], d['width'][i], d['height'][i]))
                        break

        print(detected_texts)
        print(list_pii)

        return detected_texts, list_pii, text_coords

    @staticmethod
    def redact(image_path, output_path, face_coords, text_coords):
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Error: Unable to load image.")

        for (x, y, w, h) in face_coords:
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 0), -1)

        for (x, y, w, h) in text_coords:
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 0), -1)

        print(output_path)

        cv2.imwrite(output_path, image)

    @staticmethod
    def update_text_coords(image_path, list_pii):
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Error: Unable to load image.")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        d = pytesseract.image_to_data(gray, output_type=Output.DICT)

        updated_text_coords = []

        for i in range(len(d['level'])):
            text = d['text'][i].strip()
            if text and text in list_pii:
                updated_text_coords.append((d['left'][i], d['top'][i], d['width'][i], d['height'][i]))

        return updated_text_coords


    @staticmethod
    def process_image(image_path, output_path, list_pii, face_output_dir="faces"):
        face_coords = RedactImage.detect_faces(image_path, face_output_dir)
        updated_text_coord = RedactImage.update_text_coords(image_path, list_pii)
        RedactImage.redact(image_path, output_path, face_coords, updated_text_coord)
