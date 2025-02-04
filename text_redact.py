# import TEXT

# pdf_path = "INPUTS/health_report.pdf"
# output_path = "OUTPUTS/redacted_output2.pdf"
# redact = TEXT.redact_text(pdf_path, output_path)

import os
from REDACT import redact_text
from REDACT import redact_video

input_folder = "INPUTS"
output_folder = "OUTPUTS"

def process_pdfs(input_folder, output_folder, prefix="redacted"):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder) 

    pdf_files = sorted([f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')]) 
    
    for index, pdf_file in enumerate(pdf_files, start=1):
        input_path = os.path.join(input_folder, pdf_file)
        output_path = os.path.join(output_folder, f"{prefix}_{index}.pdf")
        
        print(f"Processing: {pdf_file} → {output_path}")
        redact_text(input_path, output_path) 

print("1. Redact text")
print("2. Redact video")
choice = int(input("Enter choice: "))
match choice:
    case 1:
        process_pdfs(input_folder, output_folder)
    case 2:
        redact_video("videoplayback.mp4")
