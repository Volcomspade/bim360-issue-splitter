
from pathlib import Path
import fitz  # PyMuPDF
import re

def detect_report_type(pdf_path):
    with fitz.open(pdf_path) as doc:
        first_page = doc[0].get_text()
    if "#01:" in first_page or "#1:" in first_page:
        return "ACC Build"
    elif "Issue ID" in first_page and "Location" in first_page:
        return "BIM 360"
    return "Unknown"

def extract_bim360_issues_fixed(pdf_path, filename_fields):
    return extract_issues(pdf_path, filename_fields, type="bim360")

def extract_acc_build_issues(pdf_path, filename_fields):
    return extract_issues(pdf_path, filename_fields, type="acc")

def extract_issues(pdf_path, filename_fields, type="bim360"):
    doc = fitz.open(pdf_path)
    issue_starts = []
    for i, page in enumerate(doc):
        text = page.get_text()
        if type == "bim360" and "Issue ID:" in text:
            issue_starts.append(i)
        elif type == "acc" and re.search(r"#\d{2,3}:", text):
            issue_starts.append(i)

    issue_starts.append(len(doc))
    issues = []
    output_files = []

    for idx in range(len(issue_starts) - 1):
        start, end = issue_starts[idx], issue_starts[idx+1]
        issue_doc = fitz.open()
        for i in range(start, end):
            issue_doc.insert_pdf(doc, from_page=i, to_page=i)
        text = doc[start].get_text()
        fields = extract_fields(text, type)
        filename = build_filename(fields, filename_fields)
        output_file = Path(f"issue_exports/{filename}.pdf")
        output_file.parent.mkdir(exist_ok=True)
        issue_doc.save(output_file)
        output_files.append(output_file)
    return output_files

def extract_fields(text, type):
    fields = {}
    if type == "bim360":
        fields["Issue ID"] = extract_val(text, r"Issue ID: *(.*)")
        fields["Location"] = extract_val(text, r"Location: *(.*)")
        fields["Location Detail"] = extract_val(text, r"Location Detail: *(.*)")
        fields["Equipment ID"] = extract_val(text, r"Equipment ID: *(.*)")
    elif type == "acc":
        fields["Issue #"] = extract_val(text, r"#(\d+):")
        fields["Title"] = extract_val(text, r"#\d+: *(.*)")
        fields["Location"] = extract_val(text, r"Location *(.*)")
        fields["Status"] = extract_val(text, r"Status *(.*)")
    return fields

def extract_val(text, pattern):
    match = re.search(pattern, text)
    return match.group(1).strip() if match else "NA"

def build_filename(fields, selected_order):
    parts = [sanitize(fields.get(k, "NA")) for k in selected_order]
    return "_".join(parts)

def sanitize(text):
    return re.sub(r"[^a-zA-Z0-9\-_]+", "_", text.strip())[:100]
