import fitz  # PyMuPDF
import re
import zipfile
from io import BytesIO

def split_bim360_report(pdf_file, filename_format="{IssueID}_{Location}_{LocationDetail}_{EquipmentID}"):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    output_files = []
    summary = []

    page = 2  # Skip cover and TOC
    while page < len(doc):
        text = doc[page].get_text()
        lines = text.splitlines()

        issue_id = None
        location = None
        location_detail = None
        equipment_id = "NoEquipment"

        for idx, line in enumerate(lines):
            if line.startswith("ID ") and len(line.strip().split()) == 2:
                issue_id = line.strip().split()[1]
            if "Location" in line and idx + 1 < len(lines):
                location = lines[idx + 1].strip()
            if "Location Detail" in line and idx + 1 < len(lines):
                location_detail = lines[idx + 1].strip()
            if "Equipment" in line or "LTR" in line:
                eq_match = re.search(r'\b([A-Z0-9\-]{6,})\b', line)
                if eq_match:
                    equipment_id = eq_match.group(1)

        if issue_id:
            start_page = page
            end_page = page
            while end_page + 1 < len(doc):
                next_text = doc[end_page + 1].get_text()
                if f"ID {issue_id}" in next_text:
                    end_page += 1
                else:
                    break

            split_doc = fitz.open()
            for i in range(start_page, end_page + 1):
                split_doc.insert_pdf(doc, from_page=i, to_page=i)

            buffer = BytesIO()
            split_doc.save(buffer)

            safe_location = (location or "NoLocation").replace(">", "").replace(":", "").replace("/", "").strip()
            safe_detail = (location_detail or "NoDetail").replace(">", "").replace(":", "").replace("/", "").strip()

            filename = filename_format.format(
                IssueID=issue_id,
                Location=safe_location,
                LocationDetail=safe_detail,
                EquipmentID=equipment_id
            ).strip() + ".pdf"

            output_files.append((filename, buffer))
            summary.append({
                "Issue ID": issue_id,
                "Location": location or "N/A",
                "Location Detail": location_detail or "N/A",
                "Equipment ID": equipment_id,
                "Pages": f"{start_page+1}-{end_page+1}"
            })

            page = end_page + 1
        else:
            page += 1

    return output_files, summary