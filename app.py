import streamlit as st
import fitz  # PyMuPDF
import zipfile
import io
import re
from pathlib import Path

def extract_issues_from_pdf(uploaded_pdf):
    doc = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")

    id_pattern = re.compile(r"ID\s+0*(\d+)")
    loc_pattern = re.compile(r"Location Detail\s+(T\d{1,3}\.BESS\.\d)", re.IGNORECASE)

    issue_segments = []
    for i in range(len(doc)):
        text = doc[i].get_text()
        id_match = id_pattern.search(text)
        loc_match = loc_pattern.search(text)

        if id_match and loc_match:
            issue_id = id_match.group(1)
            location = loc_match.group(1).replace(".", "_")
            issue_segments.append({"issue_id": issue_id, "location": location, "start": i})

    for idx, seg in enumerate(issue_segments):
        seg["end"] = issue_segments[idx + 1]["start"] if idx + 1 < len(issue_segments) else len(doc)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for seg in issue_segments:
            issue_doc = fitz.open()
            issue_doc.insert_pdf(doc, from_page=seg["start"], to_page=seg["end"] - 1)
            pdf_bytes = issue_doc.write()
            issue_doc.close()

            filename = f"Issue_{seg['issue_id']}_{seg['location']}.pdf"
            zipf.writestr(filename, pdf_bytes)

    return zip_buffer

st.title("BIM 360 Issue Splitter")
st.write("Upload your exported issue report PDF below. This tool will split each issue into its own PDF including images.")

uploaded_file = st.file_uploader("Choose a BIM 360 issue report PDF", type="pdf")

if uploaded_file:
    with st.spinner("Splitting issues, please wait..."):
        zip_file = extract_issues_from_pdf(uploaded_file)
        st.success("Done! Download your ZIP file below.")

        st.download_button(
            label="📦 Download Split Issues ZIP",
            data=zip_file.getvalue(),
            file_name="Split_Issues.zip",
            mime="application/zip"
        )
