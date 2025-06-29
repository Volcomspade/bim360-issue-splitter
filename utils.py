import io
import re
import zipfile
from PyPDF2 import PdfReader, PdfWriter


def extract_entries_from_pdf(file, format_choice="Custom", custom_format="{IssueID}_{LocationDetail}"):
    pdf = PdfReader(file)
    doc = pdf.pages
    segments = []

    for i, page in enumerate(doc):
        text = page.extract_text()
        if not text:
            continue

        # Detect segment starts by ID pattern (BIM 360 and ACC Build)
        if re.search(r"Issue\s+#?\d+", text) or re.search(r"#\d+", text):
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

        # Extract Issue ID and Location info (handle both formats)
        issue_id_match = re.search(r"Issue\s+#?(\d+)|#(\d+)", text)
        location_match = re.search(r"Location\s*:\s*(.+?)\n", text)

        issue_id = issue_id_match.group(1) if issue_id_match and issue_id_match.group(1) else issue_id_match.group(2) if issue_id_match else "Unknown"
        location = location_match.group(1).strip() if location_match else "Unknown"

        # Format filename with user-defined format
        try:
            filename = custom_format.format(IssueID=issue_id, LocationDetail=location)
        except KeyError:
            filename = f"Issue_{issue_id or 'Unknown'}"

        writer = PdfWriter()
        for i in range(start, end):
            writer.add_page(doc[i])

        pdf_bytes = io.BytesIO()
        writer.write(pdf_bytes)
        pdf_bytes.seek(0)

        zip_archive.writestr(f"{filename}.pdf", pdf_bytes.read())

        summary_data.append({
            "Issue ID": issue_id,
            "Location": location,
            "Pages": f"{start + 1}–{end}"
        })

    zip_archive.close()
    zip_buffer.seek(0)
    return summary_data, zip_buffer
