import fitz
import os
import re
import io
import zipfile
from datetime import datetime
from pathlib import Path

def construct_filename(fields: dict, format_str: str):
    return format_str.format(**{k: sanitize(fields.get(k, "")) for k in fields})

def sanitize(text):
    return re.sub(r'[^a-zA-Z0-9_\-]+', '_', text.strip())

def detect_report_type(first_page_text):
    if "#1:" in first_page_text or "#01:" in first_page_text:
        return "ACC Build"
    elif "Issue ID" in first_page_text:
        return "BIM 360"
    return "Unknown"

def extract_toc_from_acc(doc):
    toc_text = doc[1].get_text()
    pattern = re.compile(r"#(\d+):\s+(.+?)\.+\s+(\d+)")
    matches = pattern.findall(toc_text)
    toc_entries = []
    for i, (issue_id, title, start_page) in enumerate(matches):
        start_page = int(start_page)
        end_page = int(matches[i + 1][2]) - 1 if i + 1 < len(matches) else len(doc) - 1
        toc_entries.append({
            "IssueID": issue_id,
            "Title": title.strip(),
            "StartPage": start_page,
            "EndPage": end_page
        })
    return toc_entries

def extract_metadata_from_bim(page_text):
    data = {
        "IssueID": "",
        "Title": "",
        "Location": "",
        "LocationDetail": "",
        "EquipmentID": "",
        "Status": ""
    }
    patterns = {
        "IssueID": r"Issue ID\s*([\d]+)",
        "Location": r"Location\s*([\w\- ]+)",
        "LocationDetail": r"Location Detail\s*([\w\- ]+)",
        "EquipmentID": r"Equipment ID\s*([\w\-]+)",
        "Status": r"Status\s*([\w ]+)"
    }
    for key, pat in patterns.items():
        match = re.search(pat, page_text)
        if match:
            data[key] = match.group(1).strip()
    return data

def split_bim360_pdf(doc, filename_format, output_dir):
    issue_starts = []
    for i, page in enumerate(doc):
        text = page.get_text()
        if "Issue ID" in text:
            issue_starts.append((i, extract_metadata_from_bim(text)))
    issue_starts.append((len(doc), None))  # add end

    summary = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for i in range(len(issue_starts) - 1):
        start, metadata = issue_starts[i]
        end = issue_starts[i + 1][0] - 1
        issue_doc = fitz.open()
        for j in range(start, end + 1):
            issue_doc.insert_pdf(doc, from_page=j, to_page=j)
        filename = construct_filename(metadata, filename_format) + ".pdf"
        issue_doc.save(output_dir / filename)
        issue_doc.close()
        summary.append({**metadata, "StartPage": start, "EndPage": end})
    return summary

def split_acc_build_pdf(doc, filename_format, output_dir):
    toc_entries = extract_toc_from_acc(doc)
    summary = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for entry in toc_entries:
        issue_doc = fitz.open()
        for i in range(entry["StartPage"], entry["EndPage"] + 1):
            issue_doc.insert_pdf(doc, from_page=i, to_page=i)
        filename = construct_filename(entry, filename_format) + ".pdf"
        issue_doc.save(output_dir / filename)
        issue_doc.close()
        summary.append(entry)
    return summary

def process_uploaded_file(file_bytes, report_type, filename_format):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    first_page_text = doc[0].get_text()
    detected_type = detect_report_type(first_page_text) if report_type == "Auto Detect" else report_type

    output_dir = Path("/tmp/split_issues")
    if output_dir.exists():
        for f in output_dir.glob("*.pdf"):
            f.unlink()
    output_dir.mkdir(parents=True, exist_ok=True)

    if detected_type == "BIM 360":
        summary = split_bim360_pdf(doc, filename_format, output_dir)
    elif detected_type == "ACC Build":
        summary = split_acc_build_pdf(doc, filename_format, output_dir)
    else:
        return "Unknown", [], None

    # Create zip
    zip_path = f"/tmp/Issue_Report_{datetime.now().strftime('%Y%m%d%H%M%S')}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in output_dir.glob("*.pdf"):
            zipf.write(file, arcname=file.name)

    return detected_type, summary, zip_path