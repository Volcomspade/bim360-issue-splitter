
import io
import re
from PyPDF2 import PdfReader, PdfWriter
from zipfile import ZipFile
from datetime import datetime

def detect_report_type(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages[:3]:
        text += page.extract_text() or ""
    if "BIM 360" in text:
        return "BIM 360"
    elif re.search(r"Issue\s+#\d+", text):
        return "ACC Build"
    return None

def get_available_fields(report_type):
    if report_type == "BIM 360":
        return ["IssueID", "Location", "LocationDetail", "EquipmentID"]
    else:
        return ["IssueNumber", "Description", "Status"]

def extract_bim360_issues(file):
    reader = PdfReader(file)
    issues = []
    issue_data = {}
    current_id = None

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        match = re.search(r"Issue ID[:\s]+(\d+)", text)
        if match:
            if issue_data:
                issues.append(issue_data)
            current_id = match.group(1)
            issue_data = {
                "IssueID": current_id,
                "Location": extract_field("Location", text),
                "LocationDetail": extract_field("Location Detail", text),
                "EquipmentID": extract_field("Equipment ID", text),
                "pages": [i]
            }
        elif issue_data:
            issue_data["pages"].append(i)
    if issue_data:
        issues.append(issue_data)
    return issues

def extract_acc_build_issues(file):
    reader = PdfReader(file)
    text = ""
    toc_end = 0
    for i, page in enumerate(reader.pages[:5]):
        text += page.extract_text() or ""
        if "Table of Contents" in text:
            toc_end = i + 1
    issues = []
    last_index = toc_end
    for i in range(toc_end, len(reader.pages)):
        page = reader.pages[i]
        content = page.extract_text()
        match = re.search(r"Issue\s+#(\d+)", content)
        if match:
            if last_index != i:
                issues[-1]["pages"] = list(range(last_index, i))
            issues.append({
                "IssueNumber": match.group(1),
                "Description": extract_field("Description", content),
                "Status": extract_field("Status", content),
                "pages": []
            })
            last_index = i
    if issues:
        issues[-1]["pages"] = list(range(last_index, len(reader.pages)))
    return issues

def extract_field(field, text):
    match = re.search(fr"{field}[:\s]+(.+?)(\n|$)", text)
    return match.group(1).strip().replace(" ", "_") if match else "Unknown"

def zip_issue_pdfs(issues, fields, report_type):
    zip_buffer = io.BytesIO()
    zip_file = ZipFile(zip_buffer, "w")

    for issue in issues:
        writer = PdfWriter()
        filename_parts = []
        for f in fields:
            filename_parts.append(issue.get(f, "Unknown"))
        filename = "_".join(filename_parts) + ".pdf"

        for p in issue["pages"]:
            writer.add_page(PdfReader(issue['pages'][0].pdf).pages[p])
        pdf_buffer = io.BytesIO()
        writer.write(pdf_buffer)
        zip_file.writestr(filename, pdf_buffer.getvalue())

    zip_file.close()
    zip_buffer.seek(0)
    return zip_buffer
