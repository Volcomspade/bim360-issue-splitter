
import fitz
import re
from pathlib import Path

def sanitize(text):
    if not isinstance(text, str):
        return "NA"
    return re.sub(r"[^a-zA-Z0-9_\-]+", "_", text.strip())

def construct_filename(fields: dict, format_str: str) -> str:
    return format_str.format(**{k: sanitize(fields.get(k, "")) for k in re.findall(r"{(.*?)}", format_str)})

def detect_report_type(pdf_path):
    doc = fitz.open(pdf_path)
    first_page_text = doc[0].get_text()
    return first_page_text

def process_uploaded_file(pdf_path, detected_type, filename_format, output_dir):
    doc = fitz.open(pdf_path)
    issue_starts = []
    summary = []

    for page_num in range(len(doc)):
        text = doc[page_num].get_text()
        match = re.search(r"#(\d+):", text)
        if match:
            issue_id = match.group(1)
            issue_starts.append((int(issue_id), page_num))

    issue_starts.sort(key=lambda x: x[1])

    for idx, (issue_id, start_page) in enumerate(issue_starts):
        end_page = issue_starts[idx + 1][1] - 1 if idx + 1 < len(issue_starts) else len(doc) - 1
        issue_doc = fitz.open()
        for i in range(start_page, end_page + 1):
            issue_doc.insert_pdf(doc, from_page=i, to_page=i)

        text = doc[start_page].get_text()
        fields = {
            "IssueID": issue_id,
            "Issue ID": f"#{issue_id}",
            "Location": re.search(r"Location\s*\n(.*?)\n", text),
            "Location Detail": re.search(r"Location details\s*\n(.*?)\n", text),
            "Equipment ID": re.search(r"Equipment ID\s*\n(.*?)\n", text)
        }

        for k, v in fields.items():
            if hasattr(v, 'group'):
                fields[k] = v.group(1).strip()
            elif isinstance(v, str):
                fields[k] = v.strip()
            else:
                fields[k] = "NA"

        filename = construct_filename(fields, filename_format) + ".pdf"
        issue_doc.save(output_dir / filename)
        issue_doc.close()
        summary.append(fields)

    return detected_type, summary
