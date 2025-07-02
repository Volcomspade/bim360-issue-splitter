
from PyPDF2 import PdfReader, PdfWriter
import io
import re

def detect_report_type(filepath):
    reader = PdfReader(filepath)
    text = reader.pages[0].extract_text()
    if "Issue ID:" in text:
        return "BIM 360"
    return "Unknown"

def extract_bim_issues(filepath):
    reader = PdfReader(filepath)
    pages = reader.pages
    issues = []
    current_issue = {}
    buffer = PdfWriter()
    issue_id_pattern = re.compile(r"Issue ID: (\d+)")

    for i, page in enumerate(pages):
        text = page.extract_text()
        match = issue_id_pattern.search(text)
        if match:
            if current_issue:
                pdf_bytes = io.BytesIO()
                buffer.write(pdf_bytes)
                current_issue["pdf"] = pdf_bytes
                issues.append(current_issue)
                buffer = PdfWriter()
            current_issue = {
                "IssueID": match.group(1),
                "Location": extract_field(text, "Location:"),
                "LocationDetail": extract_field(text, "Location Detail:"),
                "EquipmentID": extract_field(text, "Equipment ID:")
            }
        if current_issue:
            buffer.add_page(page)

    if current_issue:
        pdf_bytes = io.BytesIO()
        buffer.write(pdf_bytes)
        current_issue["pdf"] = pdf_bytes
        issues.append(current_issue)

    return issues

def extract_field(text, label):
    try:
        value = text.split(label, 1)[1].split("\n")[0].strip()
        return re.sub(r'[\\/:*?"<>|]', "_", value)
    except:
        return "Unknown"

def format_bim_filename(issue, format_str):
    return format_str.format(
        IssueID=issue.get("IssueID", "NA"),
        Location=issue.get("Location", "NA"),
        LocationDetail=issue.get("LocationDetail", "NA"),
        EquipmentID=issue.get("EquipmentID", "NA")
    )
