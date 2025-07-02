
import fitz  # PyMuPDF
import re

def detect_report_type(pdf_path):
    doc = fitz.open(pdf_path)
    first_page = doc[0].get_text()
    if "Issue ID" in first_page and "Location" in first_page:
        return "bim360"
    return "unknown"

def extract_issues_bim360(pdf_path):
    doc = fitz.open(pdf_path)
    issues = []
    toc_pages = 2  # Skip cover + TOC

    i = toc_pages
    while i < len(doc):
        page_text = doc[i].get_text()
        match = re.search(r"Issue ID\s*([\w-]+)", page_text)
        if match:
            issue_id = match.group(1)
            issue_pages = [doc[i]]
            j = i + 1
            while j < len(doc) and not re.search(r"Issue ID\s*([\w-]+)", doc[j].get_text()):
                issue_pages.append(doc[j])
                j += 1
            issues.append({
                "id": issue_id,
                "pages": issue_pages,
                "Location": extract_field("Location", page_text),
                "LocationDetail": extract_field("Location Detail", page_text),
                "EquipmentID": extract_field("Equipment ID", page_text),
            })
            i = j
        else:
            i += 1
    return issues

def extract_field(label, text):
    pattern = rf"{label}\s*[:\-]?\s*(.*)"
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip().splitlines()[0]
    return ""

def build_filename_bim360(issue, fields):
    values = [issue.get(field, "NA").replace("/", "-").strip() for field in fields]
    return "_".join(values)

def save_issue_pdfs(pages, filename, folder):
    pdf_path = f"{folder}/{filename}.pdf"
    new_doc = fitz.open()
    for page in pages:
        new_doc.insert_pdf(page.parent, from_page=page.number, to_page=page.number)
    new_doc.save(pdf_path)
    new_doc.close()
