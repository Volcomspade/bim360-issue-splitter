
import fitz  # PyMuPDF

def detect_report_type(pdf_path):
    with fitz.open(pdf_path) as doc:
        first_page_text = doc[0].get_text()
        if "#1:" in first_page_text or "#01:" in first_page_text:
            return "ACC Build"
        elif "Issue ID" in first_page_text and "Location Detail" in first_page_text:
            return "BIM 360"
    return "Unknown"

def split_bim360_pdf(pdf_path):
    with fitz.open(pdf_path) as doc:
        total_pages = len(doc)
        files = []
        for i in range(1, total_pages):
            page_text = doc[i].get_text()
            if "Issue ID" in page_text:
                issue_id = page_text.split("Issue ID")[1].split()[0]
                issue_doc = fitz.open()
                issue_doc.insert_pdf(doc, from_page=i, to_page=i)
                filename = f"Issue_{issue_id}.pdf"
                issue_doc.save(filename)
                issue_doc.close()
                files.append(filename)
        return files

def split_acc_build_pdf(pdf_path):
    with fitz.open(pdf_path) as doc:
        total_pages = len(doc)
        files = []
        for i in range(1, total_pages):
            page_text = doc[i].get_text()
            if "#1:" in page_text or "#01:" in page_text:
                issue_number = page_text.split("#")[1].split(":")[0]
                issue_doc = fitz.open()
                issue_doc.insert_pdf(doc, from_page=i, to_page=i)
                filename = f"Issue_{issue_number}.pdf"
                issue_doc.save(filename)
                issue_doc.close()
                files.append(filename)
        return files
