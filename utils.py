
import fitz
import re
import os
import shutil
from pathlib import Path
from zipfile import ZipFile

def sanitize(text):
    if isinstance(text, int):
        text = str(text)
    return re.sub(r"[^a-zA-Z0-9\-_.]", "_", text.strip())

def detect_report_type(first_page_text):
    if "Location Detail" in first_page_text or "Attached images for ID" in first_page_text or "#00" in first_page_text:
        return "BIM 360"
    if "Issue detail" in first_page_text and "Standard fields" in first_page_text:
        return "ACC Build"
    return "Unknown"

def get_filename_fields(report_type):
    if report_type == "BIM 360":
        return ["Issue ID", "Location", "Location Detail", "Equipment ID"]
    elif report_type == "ACC Build":
        return ["Issue ID", "Location", "Location Detail", "Equipment ID"]
    return []

def construct_filename(fields: dict, format_fields: list):
    parts = [sanitize(fields.get(k, "")) for k in format_fields]
    return "_".join(filter(None, parts)) or "Unnamed"

def process_uploaded_file(pdf_path, detect_only=False, detected_type=None, filename_fields=None):
    doc = fitz.open(pdf_path)
    first_page_text = doc[0].get_text()
    report_type = detect_report_type(first_page_text)
    if detect_only:
        return report_type, get_filename_fields(report_type), None

    if not detected_type:
        return "Unknown", [], None

    output_dir = Path(tempfile.mkdtemp())
    issues = []

    if detected_type == "BIM 360":
        pattern = re.compile(r"Attached images for ID (\d{6})")
        issue_pages = {}
        for page_num in range(len(doc)):
            text = doc[page_num].get_text()
            match = pattern.search(text)
            if match:
                issue_id = match.group(1)
                if issue_id not in issue_pages:
                    issue_pages[issue_id] = []
                issue_pages[issue_id].append(page_num)

        for issue_id, pages in issue_pages.items():
            issue_doc = fitz.open()
            for p in pages:
                issue_doc.insert_pdf(doc, from_page=p, to_page=p)
            fields = {
                "Issue ID": issue_id,
                "Location": extract_field(doc[pages[0]].get_text(), "Location:"),
                "Location Detail": extract_field(doc[pages[0]].get_text(), "Location Detail:"),
                "Equipment ID": extract_field(doc[pages[0]].get_text(), "Equipment ID:")
            }
            filename = construct_filename(fields, filename_fields) + ".pdf"
            issue_doc.save(output_dir / filename)
            issue_doc.close()
            issues.append(filename)

    elif detected_type == "ACC Build":
        toc = []
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for b in blocks:
                for l in b.get("lines", []):
                    for s in l.get("spans", []):
                        text = s.get("text", "")
                        if text.startswith("#") and "Page" not in text:
                            match = re.match(r"#(\d+): (.+?)\s*\.\.\.", text)
                            if match:
                                toc.append((int(match.group(1)), match.group(2)))
        starts = [i for _, i in enumerate(doc) if any(str(j) in i.get_text() for j, _ in toc)]
        starts.append(len(doc))
        for idx, (issue_num, title) in enumerate(toc):
            start = starts[idx]
            end = starts[idx+1] - 1
            issue_doc = fitz.open()
            issue_doc.insert_pdf(doc, from_page=start, to_page=end)
            text = doc[start].get_text()
            fields = {
                "Issue ID": str(issue_num),
                "Location": extract_field(text, "Location"),
                "Location Detail": extract_field(text, "Location details"),
                "Equipment ID": extract_field(text, "Equipment ID")
            }
            filename = construct_filename(fields, filename_fields) + ".pdf"
            issue_doc.save(output_dir / filename)
            issue_doc.close()
            issues.append(filename)

    zip_path = output_dir.with_suffix(".zip")
    with ZipFile(zip_path, "w") as zipf:
        for f in output_dir.iterdir():
            zipf.write(f, arcname=f.name)
    shutil.rmtree(output_dir)
    return detected_type, zip_path

def extract_field(text, field_name):
    pattern = rf"{re.escape(field_name)}\s*(.*)"
    match = re.search(pattern, text)
    if match:
        return match.group(1).splitlines()[0].strip()
    return ""
