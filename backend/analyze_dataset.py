import pdfplumber
import io
from PIL import Image
import os

dataset_path = r"c:\Users\kinal\OneDrive\Desktop\Neostat_project\New Dataset 1\New Dataset"

# Analyze one invoice
invoice_path = os.path.join(dataset_path, "Invoices", "20251118_000612.jpg")
print("=== INVOICE SAMPLE ===")
try:
    img = Image.open(invoice_path)
    print(f"Image size: {img.size}")
    print(f"Image mode: {img.mode}")
except Exception as e:
    print(f"Error: {e}")

# Analyze one balance sheet
balance_sheet_path = os.path.join(dataset_path, "Balance Sheet", "Consolidated Balance Sheet 2017.pdf")
print("\n=== BALANCE SHEET SAMPLE ===")
try:
    with pdfplumber.open(balance_sheet_path) as pdf:
        print(f"Pages: {len(pdf.pages)}")
        for i, page in enumerate(pdf.pages[:2]):
            text = page.extract_text()
            print(f"\n--- Page {i+1} ---")
            print(text[:1000])
except Exception as e:
    print(f"Error: {e}")
