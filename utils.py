
import io
import fitz
import zipfile
import pandas as pd
from collections import defaultdict

def detect_report_type(pdf_path):
    """Detect whether the report is BIM 360 or ACC Build."""
    with fitz.open(pdf_path) as doc:
        for i in range(min(5, len(doc))):
            text = doc[i].get_text()
            if "#1:" in text or any(line.strip().startswith("#") for line in text.splitlines()):
                return "ACC Build"
            elif "Issue Report" in text and "ID 000" in text:
                return "BIM 360"
    return "Unknown"

def extract_bim_issues(pdf_path):
    doc = fitz.open(pdf_path)
    issue_starts = []
    for i, page in enumerate(doc):
        text = page.get_text()
        if "Issue Report" in text:
            lines = text.splitlines()
            for line in lines:
                if "ID 000" in line:
                    issue_id = line.strip().split("ID ")[1].strip()
                    issue_starts.append((i, issue_id))
                    break
    issue_ranges = [(start, issue_starts[i+1][0] if i+1 < len(issue_starts) else len(doc), issue_id)
                    for i, (start, issue_id) in enumerate(issue_starts)]
    return doc, issue_ranges

def extract_acc_issues(pdf_path):
    doc = fitz.open(pdf_path)
    start_offset = 0
    for i, page in enumerate(doc):
        if any(line.strip().startswith("#") and ":" in line for line in page.get_text().splitlines()):
            start_offset = i
            break
    issue_starts = []
    for i in range(start_offset, len(doc)):
        lines = doc[i].get_text().splitlines()
        for line in lines:
            if line.strip().startswith("#") and ":" in line:
                issue_id = line.strip().split(":")[0].replace("#", "").strip()
                issue_starts.append((i, issue_id))
                break
    issue_ranges = [(start, issue_starts[i+1][0] if i+1 < len(issue_starts) else len(doc), issue_id)
                    for i, (start, issue_id) in enumerate(issue_starts)]
    return doc, issue_ranges

def split_pdf_by_issues(doc, issue_ranges, filename_format):
    zip_buffer = io.BytesIO()
    summary = []
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for start, end, issue_id in issue_ranges:
            issue_doc = fitz.open()
            issue_doc.insert_pdf(doc, from_page=start, to_page=end-1)
            buffer = io.BytesIO()
            issue_doc.save(buffer)
            issue_doc.close()
            filename = filename_format.replace("{IssueID}", issue_id)
            zip_file.writestr(f"{filename}.pdf", buffer.getvalue())
            summary.append({"Issue ID": issue_id, "Pages": f"{start+1}-{end}"})
    return pd.DataFrame(summary), zip_buffer
