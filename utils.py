from PyPDF2 import PdfReader, PdfWriter
import re
import io
import zipfile


def extract_entries_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    segments = []
    doc = list(reader.pages)

    # Determine report type by scanning first page
    first_page_text = doc[0].extract_text()
    is_acc = re.search(r"Issue\s+#?\d+", first_page_text)
    is_bim360 = re.search(r"^Issue ID:\s+\d+", first_page_text, re.MULTILINE)

    if is_acc:
        report_type = "acc"
    elif is_bim360:
        report_type = "bim360"
    else:
        return None, []  # No valid type detected

    # Parse page segments
    for i, page in enumerate(doc):
        text = page.extract_text()

        if report_type == "bim360":
            match = re.search(r"Issue ID:\s+(\d+)", text)
            if match:
                issue_id = match.group(1)
                location = re.search(r"Location Detail:\s+(.*)", text)
                status = re.search(r"Status:\s+(.*)", text)
                equipment = re.search(r"Equipment ID:\s+(.*)", text)
                segments.append({
                    "entry_id": issue_id,
                    "start": i,
                    "location": location.group(1).strip() if location else "Unknown",
                    "status": status.group(1).strip() if status else "Unknown",
                    "equipment_id": equipment.group(1).strip() if equipment else "None"
                })

        elif report_type == "acc":
            match = re.search(r"Issue\s+#?(\d+)", text)
            if match:
                issue_id = match.group(1)
                location = re.search(r"Location\s*\n(.*)", text)
                status = re.search(r"Status\s*\n(.*)", text)
                equipment = re.search(r"Equipment ID\s*\n(.*)", text)
                segments.append({
                    "entry_id": issue_id,
                    "start": i,
                    "location": location.group(1).strip() if location else "Unknown",
                    "status": status.group(1).strip() if status else "Unknown",
                    "equipment_id": equipment.group(1).strip() if equipment else "None"
                })

    # Set end page for each segment
    for idx in range(len(segments)):
        segments[idx]["end"] = segments[idx + 1]["start"] if idx + 1 < len(doc) else len(doc)

    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    zip_file = zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED)

    for seg in segments:
        writer = PdfWriter()
        for p in range(seg["start"], seg["end"]):
            writer.add_page(doc[p])

        # Filename format: Issue_###_Location.pdf
        clean_loc = seg["location"].replace(" ", "_").replace("/", "-")
        filename = f"Issue_{seg['entry_id']}_{clean_loc}.pdf"

        pdf_bytes = io.BytesIO()
        writer.write(pdf_bytes)
        pdf_bytes.seek(0)
        zip_file.writestr(filename, pdf_bytes.read())

    zip_file.close()
    zip_buffer.seek(0)

    return zip_buffer, segments
