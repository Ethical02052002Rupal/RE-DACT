import cv2

import pytesseract
from pytesseract import Output
import numpy as np

class redact_image:
    def __init__(self, image_path, output_path):
        # Load the pre-trained face cascade classifier
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        # Load the image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error: Unable to load image at {image_path}")
            return

        # Convert the image to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detect faces in the image
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # Redact each detected face
        for (x, y, w, h) in faces:
            padding = 10  # Extend the area by 10 pixels on all sides
            top_padding = 50
            x_start = max(x - padding, 0)
            y_start = max(y - top_padding, 0)
            x_end = min(x + w + padding, image.shape[1])
            y_end = min(y + h + padding, image.shape[0])

            # Black out the detected face area
            image[y_start:y_end, x_start:x_end] = (0, 0, 0)

        # Save the redacted image
        cv2.imwrite(output_path, image)

        print(f"Redacted image saved to {output_path}")




        #########################################################
        #########################################################

        def redact_pii(image_path, output_path):
                    # Load the image
                    image = cv2.imread(image_path)
                    if image is None:
                        print("Error: Unable to load image.")
                        return

                    # Convert the image to grayscale
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                    # Use pytesseract to get bounding box information for text
                    d = pytesseract.image_to_data(gray, output_type=Output.DICT)

                    # List of PII keywords to redact (customize as needed)
                    pii_keywords = ["name", "dob", "father", "mother", "address", "pan", "aadhaar", "account", "number", "signature", "id", "card"]

                    # Iterate over each detected text element
                    n_boxes = len(d['level'])
                    for i in range(n_boxes):
                        text = d['text'][i].lower()
                        for keyword in pii_keywords:
                            if keyword in text:
                                # Get the bounding box coordinates
                                (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
                                # Blackout the PII by drawing a rectangle over it
                                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 0), -1)
                                break

                    # Save the redacted image
                    cv2.imwrite(output_path, image)
                    print(f"Redacted image saved to {output_path}")

        redact_pii(output_path, output_path)