import re
from PyPDF2 import PdfReader, PdfWriter
import io
import zipfile
import pandas as pd

def extract_entries_from_pdf(file):
    pdf = PdfReader(file)
    doc = pdf.pages
    segments = []

    # Step 1: Identify segments
    for i, page in enumerate(doc):
        text = page.extract_text()
        if not text:
            continue

        if "Issue #" in text or re.search(r"Issue\s+#?\d+", text):
            segments.append({"start": i, "text": text})
        elif re.match(r"#\d{3,}", text.splitlines()[0]):
            segments.append({"start": i, "text": text})

    if not segments:
        return None, None

    # Step 2: Assign end pages safely
    for idx in range(len(segments)):
        segments[idx]["end"] = segments[idx + 1]["start"] if idx + 1 < len(doc) else len(doc)

    zip_buffer = io.BytesIO()
    zip_archive = zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED)

    summary_data = []

    for seg in segments:
        text = seg["text"]
        start, end = seg["start"], seg["end"]

        # Try both BIM 360 and ACC Build patterns
        issue_id_match = (
            re.search(r"Issue\s+#?(\d+)", text) or
            re.match(r"#(\d+)", text.splitlines()[0])
        )
        location_match = (
            re.search(r"Location Detail\s*:\s*(.+)", text) or
            re.search(r"Location\s*:\s*(.+)", text)
        )

        issue_id = issue_id_match.group(1).strip() if issue_id_match else "Unknown"
        location = location_match.group(1).strip().replace(" ", "_") if location_match else "Unknown"

        filename = f"{issue_id}_{location}.pdf"

        writer = PdfWriter()
        for p in range(start, end):
            writer.add_page(doc[p])

        issue_buffer = io.BytesIO()
        writer.write(issue_buffer)
        zip_archive.writestr(filename, issue_buffer.getvalue())

        summary_data.append({
            "Issue ID": issue_id,
            "Location": location,
            "Pages": f"{start + 1}–{end}"
        })

    zip_archive.close()
    zip_buffer.seek(0)

    df = pd.DataFrame(summary_data)
    return df, zip_buffer
