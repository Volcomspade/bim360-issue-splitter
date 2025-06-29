import fitz  # PyMuPDF
import io
import zipfile
import pandas as pd
import re

def extract_entries_from_pdf(pdf_file, report_type="auto", filename_format="auto"):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()

    # Detect report type if needed
    if report_type == "auto":
        if re.search(r"ACC Build Issue Report", text, re.IGNORECASE) or re.search(r"#\d{2}", text):
            report_type = "acc"
        elif re.search(r"Issue ID", text) and re.search(r"Location Detail", text):
            report_type = "bim360"
        else:
            return None, None

    if report_type == "bim360":
        return extract_bim360_entries(doc, filename_format)
    elif report_type == "acc":
        return extract_acc_entries(doc, filename_format)
    else:
        return None, None

def extract_bim360_entries(doc, filename_format):
    text_pages = [page.get_text() for page in doc]
    segments = []

    for i, text in enumerate(text_pages):
        if "Issue ID" in text and "Location Detail" in text:
            segments.append({"start": i})

    for i in range(len(segments)):
        segments[i]["end"] = segments[i + 1]["start"] if i + 1 < len(segments) else len(doc)

    zip_buffer = io.BytesIO()
    zip_archive = zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED)
    summary = []

    for i, s in enumerate(segments):
        issue_id_match = re.search(r"Issue ID[:\s]+([^\n]+)", text_pages[s["start"]])
        location_match = re.search(r"Location Detail[:\s]+([^\n]+)", text_pages[s["start"]])
        issue_id = issue_id_match.group(1).strip() if issue_id_match else f"Issue_{i+1}"
        location = location_match.group(1).strip() if location_match else "Unknown"

        filename = f"{issue_id}_{location}".replace(" ", "_").replace("/", "-") + ".pdf"
        pdf_bytes = io.BytesIO()
        issue_doc = fitz.open()
        for j in range(s["start"], s["end"]):
            issue_doc.insert_pdf(doc, from_page=j, to_page=j)
        issue_doc.save(pdf_bytes)
        issue_doc.close()
        zip_archive.writestr(filename, pdf_bytes.getvalue())

        summary.append({"Issue ID": issue_id, "Location": location, "Pages": f"{s['start']+1}–{s['end']}"})

    zip_archive.close()
    zip_buffer.seek(0)
    return pd.DataFrame(summary), zip_buffer

def extract_acc_entries(doc, filename_format):
    text_pages = [page.get_text() for page in doc]
    segments = []

    for i, text in enumerate(text_pages):
        if re.match(r"#\d{2,}", text.strip().splitlines()[0]):
            segments.append({"start": i})

    for i in range(len(segments)):
        segments[i]["end"] = segments[i + 1]["start"] if i + 1 < len(segments) else len(doc)

    zip_buffer = io.BytesIO()
    zip_archive = zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED)
    summary = []

    for i, s in enumerate(segments):
        first_line = text_pages[s["start"]].strip().splitlines()[0]
        issue_id = first_line.strip().lstrip("#").strip() or f"ACC_{i+1}"

        filename = f"{issue_id}.pdf"
        pdf_bytes = io.BytesIO()
        issue_doc = fitz.open()
        for j in range(s["start"], s["end"]):
            issue_doc.insert_pdf(doc, from_page=j, to_page=j)
        issue_doc.save(pdf_bytes)
        issue_doc.close()
        zip_archive.writestr(filename, pdf_bytes.getvalue())

        summary.append({"Issue ID": issue_id, "Location": "Unknown", "Pages": f"{s['start']+1}–{s['end']}"})

    zip_archive.close()
    zip_buffer.seek(0)
    return pd.DataFrame(summary), zip_buffer
