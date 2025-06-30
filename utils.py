
import os
import re
import fitz  # PyMuPDF
from datetime import datetime
from PyPDF2 import PdfWriter
import tempfile

def detect_report_type(pdf_path):
    with fitz.open(pdf_path) as doc:
        text = ""
        for page in doc:
            text += page.get_text().lower()
            if len(text) > 1000:
                break
        if "autodesk bim 360" in text or "issue id" in text:
            return "BIM 360"
        elif "acc build" in text or "#01" in text:
            return "ACC Build"
    return "Unknown"

def generate_filename_options(report_type):
    if report_type == "BIM 360":
        return ["IssueID", "Location", "LocationDetail", "EquipmentID"]
    else:
        return ["IssueNumber", "Title", "Status", "Location", "Discipline"]

def extract_bim_issues(pdf_path):
    doc = fitz.open(pdf_path)
    issues = []
    current_issue = {"pages": [], "fields": {}}
    for i, page in enumerate(doc):
        text = page.get_text()
        match = re.search(r"Issue ID[:\s]+(\d+)", text)
        if match:
            if current_issue["pages"]:
                issues.append(current_issue)
            current_issue = {"pages": [i], "fields": {}}
            current_issue["fields"]["IssueID"] = match.group(1)
            location = re.search(r"Location[:\s]+(.+)", text)
            detail = re.search(r"Location Detail[:\s]+(.+)", text)
            equip = re.search(r"Equipment ID[:\s]+(.+)", text)
            if location:
                current_issue["fields"]["Location"] = location.group(1).strip().replace(" ", "_")
            if detail:
                current_issue["fields"]["LocationDetail"] = detail.group(1).strip().replace(" ", "_")
            if equip:
                current_issue["fields"]["EquipmentID"] = equip.group(1).strip().replace(" ", "_")
        else:
            current_issue["pages"].append(i)
    if current_issue["pages"]:
        issues.append(current_issue)
    return issues

def extract_acc_issues(pdf_path):
    doc = fitz.open(pdf_path)
    toc_end = 0
    toc_pattern = re.compile(r"#(\d{2})\s+(.*?)\s+(\d+)")
    toc_entries = []
    for i, page in enumerate(doc):
        text = page.get_text()
        lines = text.split("\n")
        for line in lines:
            m = toc_pattern.match(line)
            if m:
                issue_no, title, page_no = m.groups()
                toc_entries.append((issue_no, title.strip(), int(page_no)))
        if "Issue #" in text:
            toc_end = i
            break
    issues = []
    for idx, (issue_no, title, start_page) in enumerate(toc_entries):
        end_page = toc_entries[idx + 1][2] if idx + 1 < len(toc_entries) else len(doc)
        issue = {
            "pages": list(range(start_page - 1, end_page)),
            "fields": {
                "IssueNumber": issue_no,
                "Title": title.replace(" ", "_")
            }
        }
        issue["fields"]["Status"] = "Open"
        issue["fields"]["Location"] = "Unknown"
        issue["fields"]["Discipline"] = "General"
        issues.append(issue)
    return issues

def save_issue_pdfs(issues, output_dir, field_order):
    for issue in issues:
        writer = PdfWriter()
        filename_parts = []
        for key in field_order:
            val = issue["fields"].get(key, "NA")
            filename_parts.append(val)
        filename = "_".join(filename_parts) + ".pdf"
        temp_pdf_path = os.path.join(output_dir, filename)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            issue_doc = fitz.open()
            src = fitz.open()
            for page_num in issue["pages"]:
                src = fitz.open(issue["source"]) if "source" in issue else fitz.open()
                issue_doc.insert_pdf(src, from_page=page_num, to_page=page_num)
            issue_doc.save(temp_file.name)
            with open(temp_file.name, "rb") as f:
                writer.append(f)
            with open(temp_pdf_path, "wb") as f_out:
                writer.write(f_out)

def zip_output_folder(folder_path, prefix="Issue_Report"):
    zip_path = os.path.join(folder_path, f"{prefix}_{datetime.now().strftime('%Y%m%d')}.zip")
    from zipfile import ZipFile
    with ZipFile(zip_path, "w") as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".pdf"):
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, start=folder_path)
                    zipf.write(file_path, arcname)
    return zip_path
