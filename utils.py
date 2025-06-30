
import fitz
import re
from pathlib import Path
from zipfile import ZipFile

def detect_report_type(text):
    text = str(text).strip()
    if "#01:" in text or "#1:" in text:
        return "ACC Build"
    elif "Issue detail" in text and "Location Detail" in text:
        return "BIM 360"
    return "Unknown"

def sanitize(text):
    if not isinstance(text, str):
        return "NA"
    return re.sub(r"[^a-zA-Z0-9_\-]+", "_", text.strip())

def construct_filename(fields: dict, format_order: list):
    parts = [sanitize(fields.get(field, "")) for field in format_order]
    return "_".join([part for part in parts if part])

def process_uploaded_file(file_path, filename_format):
    doc = fitz.open(file_path)
    first_page = doc[0].get_text("text")
    report_type = detect_report_type(first_page)

    output_dir = Path("/tmp/split_issues")
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = []
    for i in range(0, len(doc), 2):
        issue_text = doc[i].get_text("text")
        fields = {
            "Issue ID": f"#{i//2 + 1}",
            "Location": "UnknownLoc",
            "Location Detail": "NA",
            "Equipment ID": "NA",
            "Serial Number": "NA"
        }
        filename = construct_filename(fields, filename_format) + ".pdf"
        issue_doc = fitz.open()
        issue_doc.insert_pdf(doc, from_page=i, to_page=min(i+1, len(doc)-1))
        issue_doc.save(output_dir / filename)
        issue_doc.close()
        summary.append(filename)

    zip_path = output_dir.with_suffix(".zip")
    with ZipFile(zip_path, "w") as zipf:
        for f in output_dir.iterdir():
            zipf.write(f, arcname=f.name)

    return report_type, summary, zip_path
