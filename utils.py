import re
import io
import zipfile
from PyPDF2 import PdfReader, PdfWriter

def extract_entries_from_pdf(file_path):
    reader = PdfReader(file_path)
    pages = reader.pages

    # Auto-detect report format
    first_text = pages[0].extract_text() or ""
    is_bim360 = "Issue #" in first_text or "Location Detail:" in first_text
    is_acc_build = re.search(r"#\d{2,}", first_text) and "Location:" in first_text

    segments = []

    for i, p in enumerate(pages):
        text = p.extract_text()
        if not text:
            continue

        if is_bim360:
            if "Issue #" in text or "Location Detail:" in text:
                segments.append({"start": i, "text": text})
        elif is_acc_build:
            if re.search(r"#\d{2,}", text) and "Location:" in text:
                segments.append({"start": i, "text": text})

    if not segments:
        return None, None

    # Define end pages
    for idx in range(len(segments)):
        segments[idx]["end"] = segments[idx + 1]["start"] if idx + 1 < len(pages) else len(pages)

    zip_buffer = io.BytesIO()
    zipf = zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED)
    summary = []

    for seg in segments:
        txt = seg["text"]
        start, end = seg["start"], seg["end"]

        id_match = re.search(r"Issue\s*#?(\d+)", txt) or re.search(r"#(\d+)", txt)
        loc_match = re.search(r"Location(?: Detail)?:\s*(.+)", txt)
        equip_match = re.search(r"Equipment ID:\s*(.+)", txt)

        issue_id = id_match.group(1).strip() if id_match else f"{start+1}"
        location = loc_match.group(1).strip().replace(" ", "_") if loc_match else ""
        equipment = equip_match.group(1).strip() if equip_match else ""

        filename = f"Issue_{issue_id}"
        if location:
            filename += f"_{location}"
        filename += ".pdf"

        writer = PdfWriter()
        for page_num in range(start, end):
            writer.add_page(pages[page_num])

        tmp = io.BytesIO()
        writer.write(tmp)
        zipf.writestr(filename, tmp.getvalue())

        summary.append({
            "file_name": filename,
            "issue_id": issue_id,
            "location": location,
            "equipment_id": equipment
        })

    zipf.close()
    zip_buffer.seek(0)
    return zip_buffer, summary
