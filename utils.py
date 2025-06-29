
import fitz  # PyMuPDF
import io
import pandas as pd
import zipfile

def detect_report_type(file_bytes):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    first_page_text = doc[0].get_text()
    if "Autodesk® Construction Cloud™" in first_page_text or "#01" in first_page_text:
        return "ACC Build"
    if "Issue Report" in first_page_text and "Location" in first_page_text:
        return "BIM 360"
    return None

def get_filename_formats(report_type):
    if report_type == "BIM 360":
        return ["{IssueID}_{Location}", "{Location}_{IssueID}", "{IssueID}"]
    elif report_type == "ACC Build":
        return ["#{IssueID}_{LocationDetail}", "{LocationDetail}_{IssueID}", "#{IssueID}"]
    return []

def extract_bim360_entries(file_bytes, filename_format):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    summary = []
    zip_buffer = io.BytesIO()
    zip_archive = zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED)

    for i, page in enumerate(doc):
        text = page.get_text()
        lines = text.split("
")
        issue_id = next((line for line in lines if line.strip().isdigit()), f"Issue{i+1}")
        location = next((line for line in lines if "." in line and len(line) < 30), "Unknown")
        filename = filename_format.format(IssueID=issue_id.strip(), Location=location.replace(" ", "_"))
        summary.append({"Issue ID": issue_id, "Location": location, "Pages": f"{i+1}–{i+1}"})
        pdf_bytes = io.BytesIO()
        issue_doc = fitz.open()
        issue_doc.insert_pdf(doc, from_page=i, to_page=i)
        issue_doc.save(pdf_bytes)
        issue_doc.close()
        zip_archive.writestr(f"{filename}.pdf", pdf_bytes.getvalue())

    zip_archive.close()
    return pd.DataFrame(summary), zip_buffer

def extract_acc_build_entries(file_bytes, filename_format):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    summary = []
    zip_buffer = io.BytesIO()
    zip_archive = zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED)

    segments = []
    for i, page in enumerate(doc):
        if "#0" in page.get_text():
            segments.append({"start": i})
    for idx in range(len(segments)):
        segments[idx]["end"] = segments[idx + 1]["start"] - 1 if idx + 1 < len(segments) else len(doc) - 1

    for seg in segments:
        start, end = seg["start"], seg["end"]
        text = doc[start].get_text()
        lines = text.split("
")
        issue_id = next((l for l in lines if l.strip().startswith("#")), "#Unknown").strip("#")
        location = next((l for l in lines if ">" in l or "-" in l), "Unknown")
        filename = filename_format.format(IssueID=issue_id.strip(), LocationDetail=location.replace(" ", "_"))
        summary.append({"Issue ID": issue_id, "Location": location, "Pages": f"{start+1}–{end+1}"})
        pdf_bytes = io.BytesIO()
        issue_doc = fitz.open()
        issue_doc.insert_pdf(doc, from_page=start, to_page=end)
        issue_doc.save(pdf_bytes)
        issue_doc.close()
        zip_archive.writestr(f"{filename}.pdf", pdf_bytes.getvalue())

    zip_archive.close()
    return pd.DataFrame(summary), zip_buffer
