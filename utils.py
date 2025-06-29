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

        # Match both BIM 360 ("Issue #123") and ACC Build ("#123") formats
        if re.search(r"(Issue\s*#?\d+|#\d{2,})", text):
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

        # Extract issue ID
        issue_id_match = re.search(r"(Issue\s*#?|#)(\d+)", text)
        issue_id = issue_id_match.group(2) if issue_id_match else f"page_{start+1}"

        # Extract location
        location_match = re.search(r"Location\s*:(.*?)\n", text)
        location = location_match.group(1).strip().replace("/", "-") if location_match else "Unknown"

        # Create issue PDF
        writer = PdfWriter()
        for i in range(start, end):
            writer.add_page(doc[i])
        temp_buf = io.BytesIO()
        writer.write(temp_buf)
        temp_buf.seek(0)

        filename = f"Issue_{issue_id}_{location}.pdf"
        zip_archive.writestr(filename, temp_buf.read())

        summary_data.append({
            "Issue ID": issue_id,
            "Location": location,
            "Pages": f"{start+1}–{end}"
        })

    zip_archive.close()
    zip_buffer.seek(0)
    return summary_data, zip_buffer
