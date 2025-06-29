import io
import zipfile
import re
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter

def extract_entries_from_pdf(file, auto_detect=True, format_choice="Custom", custom_format="{IssueID}_{Location}_{EquipmentID}"):
    pdf = PdfReader(file)
    doc = pdf.pages
    segments = []

    for i, page in enumerate(doc):
    text = page.extract_text()
    if not text:
        continue

   first_line = text.strip().splitlines()[0] if text.strip() else ""
    if "Issue #" in text or re.search(r"Issue\s+#?\d+", text) or re.match(r"^#\d+", first_line):
        segments.append({"start": i, "text": text})

    if not segments:
        return None, None

    for idx in range(len(segments)):
        segments[idx]["end"] = segments[idx + 1]["start"] if idx + 1 < len(doc) else len(doc)

    zip_buffer = io.BytesIO()
    zip_archive = zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED)

    summary_data = []

    for seg in segments:
        text = seg["text"]
        start, end = seg["start"], seg["end"]

        issue_id_match = re.search(r"Issue\s+#?(\d+)", text)
        location_match = re.search(r"Location\s+(.+?)(?:\n|$)", text)
        equip_id_match = re.search(r"Equipment ID\s+(.+?)(?:\n|$)", text)
        status_match = re.search(r"Status\s+(.+?)(?:\n|$)", text)

        issue_id = issue_id_match.group(1).strip() if issue_id_match else "Unknown"
        location = location_match.group(1).strip() if location_match else "Unknown"
        equipment_id = equip_id_match.group(1).strip() if equip_id_match else "Unknown"
        status = status_match.group(1).strip() if status_match else "Unknown"

        filename = custom_format.format(
            IssueID=issue_id,
            Location=location.replace(" ", "_"),
            EquipmentID=equipment_id,
            Status=status
        )

        writer = PdfWriter()
        for i in range(start, end):
            writer.add_page(doc[i])

        pdf_bytes = io.BytesIO()
        writer.write(pdf_bytes)
        pdf_bytes.seek(0)

        zip_archive.writestr(f"{filename}.pdf", pdf_bytes.read())

        summary_data.append({
            "Issue ID": issue_id,
            "Status": status,
            "Location": location,
            "Equipment ID": equipment_id
        })

    zip_archive.close()
    zip_buffer.seek(0)

    summary_df = pd.DataFrame(summary_data)
    return zip_buffer, summary_df
