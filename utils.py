import re
import io
import zipfile
from PyPDF2 import PdfReader, PdfWriter

def extract_entries_from_pdf(file):
    pdf = PdfReader(file)
    doc = pdf.pages
    segments = []

    for i, page in enumerate(doc):
        text = page.extract_text()
        if not text:
            continue

        # Detect format
        if "Issue #" in text or re.search(r"Issue\s*#?\d+", text):
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

        issue_id_match = re.search(r"Issue\s*#?(\d+)", text)
        location_match = re.search(r"Location\s*:\s*(.+?)\n", text)
        equip_match = re.search(r"Equipment ID\s*:\s*(.+?)\n", text)

        issue_id = issue_id_match.group(1) if issue_id_match else f"{start+1}"
        location = location_match.group(1).strip() if location_match else "Unknown_Location"
        equip_id = equip_match.group(1).strip() if equip_match else "Unknown_Equip"

        filename = f"Issue_{issue_id}_{location.replace(' ', '_')}_{equip_id.replace(' ', '_')}.pdf"
        filename = filename.replace("/", "-")

        writer = PdfWriter()
        for i in range(start, end):
            writer.add_page(pdf.pages[i])

        output = io.BytesIO()
        writer.write(output)
        zip_archive.writestr(filename, output.getvalue())

        summary_data.append({
            "Issue ID": issue_id,
            "Location": location,
            "Equipment ID": equip_id,
            "Pages": f"{start+1}-{end}"
        })

    zip_archive.close()
    zip_buffer.seek(0)
    return summary_data, zip_buffer
