from pdfminer.high_level import extract_text
from PyPDF2 import PdfReader, PdfWriter
import os

def detect_report_type(path):
    text = extract_text(path, maxpages=3)

    bim_keys = ["Issue ID", "Location Detail", "Equipment ID"]
    acc_keys = ["Issue detail", "Standard fields", "Autodesk® Construction Cloud™"]

    bim_score = sum(k in text for k in bim_keys)
    acc_score = sum(k in text for k in acc_keys)

    if bim_score > acc_score and bim_score >= 2:
        return "BIM 360"
    elif acc_score > bim_score and acc_score >= 2:
        return "ACC Build"
    return "Unknown"

def extract_bim360_issues(path, output_dir, order):
    reader = PdfReader(path)
    files = []
    issues = {}
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and "Issue ID:" in text:
            lines = text.splitlines()
            entry = {}
            for line in lines:
                if ":" in line:
                    k, v = line.split(":", 1)
                    entry[k.strip()] = v.strip()
            issue_id = entry.get("Issue ID")
            if issue_id:
                if issue_id not in issues:
                    issues[issue_id] = []
                issues[issue_id].append(i)

    for issue_id, pages in issues.items():
        writer = PdfWriter()
        for p in pages:
            writer.add_page(reader.pages[p])
        first_page = reader.pages[pages[0]].extract_text()
        name_parts = []
        keys = {"IssueID": "Issue ID", "Location": "Location", "LocationDetail": "Location Detail", "EquipmentID": "Equipment ID"}
        for field in order:
            val = ""
            for line in first_page.splitlines():
                if f"{keys[field]}:" in line:
                    val = line.split(":",1)[1].strip()
                    break
            name_parts.append(val)
        filename = "_".join(name_parts) + ".pdf"
        file_path = os.path.join(output_dir, filename)
        with open(file_path, "wb") as f:
            writer.write(f)
        files.append(file_path)
    return files

def extract_acc_issues(path, output_dir, order):
    reader = PdfReader(path)
    files = []
    issues = {}
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip().startswith("Issue detail"):
            issue_num = None
            for line in text.splitlines():
                if line.startswith("#"):
                    issue_num = line.split()[0][1:]
                    break
            if issue_num:
                issues[issue_num] = [i]
        elif issues and list(issues.values())[-1][-1] == i - 1:
            list(issues.values())[-1].append(i)

    for issue_id, pages in issues.items():
        writer = PdfWriter()
        for p in pages:
            writer.add_page(reader.pages[p])
        first_text = reader.pages[pages[0]].extract_text()
        name_parts = []
        keys = {"Issue#": "#", "Location": "Location", "Title": "Title", "Status": "Status"}
        for field in order:
            val = ""
            for line in first_text.splitlines():
                if keys[field] in line:
                    val = line.split(":",1)[-1].strip()
                    break
            name_parts.append(val)
        filename = "_".join(name_parts) + ".pdf"
        file_path = os.path.join(output_dir, filename)
        with open(file_path, "wb") as f:
            writer.write(f)
        files.append(file_path)
    return files
