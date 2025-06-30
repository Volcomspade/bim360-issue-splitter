
import re
import fitz  # PyMuPDF
from pathlib import Path

def detect_report_type(first_page_text: str) -> str:
    if "#1:" in first_page_text or "#01:" in first_page_text:
        return "ACC Build"
    elif "Issue ID:" in first_page_text and "Location:" in first_page_text:
        return "BIM 360"
    else:
        return "Unknown"

def sanitize(text):
    if not isinstance(text, str):
        return str(text)
    return re.sub(r'[^a-zA-Z0-9\-_.]+', '_', text.strip())

def construct_filename(fields: dict, format_str: str) -> str:
    return format_str.format(**{k: sanitize(fields.get(k, "")) for k in fields})

def extract_bim360_issues_fixed(input_pdf_path):
    from .bim360_parser import extract_bim360_issues
    return extract_bim360_issues(input_pdf_path)

def extract_acc_build_issues(input_pdf_path):
    from .acc_parser import extract_acc_build_issues
    return extract_acc_build_issues(input_pdf_path)
