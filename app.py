import streamlit as st
import fitz  # PyMuPDF
import zipfile
import io
import re
from pathlib import Path

st.set_page_config(page_title="BIM 360 Issue Splitter", page_icon="📄", layout="centered")

# --- Title and Header ---
st.markdown("""
    <h2 style='text-align: center; color: #333;'>📄 BIM 360 Issue Report Splitter</h2>
    <p style='text-align: center; font-size: 16px;'>Upload your BIM 360 PDF and download each issue as a separate file.</p>
""", unsafe_allow_html=True)

st.markdown("---")

# --- Filename Format Selection ---
st.sidebar.header("Filename Options")
format_choice = st.sidebar.selectbox("Choose filename format:", (
    "IssueID_Location",
    "EquipmentID_IssueID_Status",
    "Status_EquipmentID_Location",
    "Custom"
))

custom_format = ""
if format_choice == "Custom":
    custom_format = st.sidebar.text_input("Custom format using: {IssueID}, {Location}, {Status}, {EquipmentID}",
                                          "{Status}_{IssueID}_{Location}")

def extract_issues_from_pdf(uploaded_pdf):
    doc = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")

    id_pattern = re.compile(r"ID\s+0*(\d+)")
    loc_pattern = re.compile(r"Location Detail\s+(T\d{1,3}\.BESS\.\d)", re.IGNORECASE)
    status_pattern = re.compile(r"Status\s+(\w+)")
    equip_pattern = re.compile(r"Equipment ID\s+(\S+)", re.IGNORECASE)

    issue_segments = []
    for i in range(len(doc)):
        text = doc[i].get_text()
        id_match = id_pattern.search(text)
        loc_match = loc_pattern.search(text)

        if id_match and loc_match:
            issue_id = id_match.group(1)
            location = loc_match.group(1).replace(".", "_")
            status_match = status_pattern.search(text)
            equip_match = equip_pattern.search(text)

            status = status_match.group(1) if status_match else "Unknown"
            equip_id = equip_match.group(1) if equip_match else "NA"

            issue_segments.append({
                "issue_id": issue_id,
                "location": location,
                "status": status,
                "equipment_id": equip_id,
                "start": i
            })

    for idx, seg in enumerate(issue_segments):
        seg["end"] = issue_segments[idx + 1]["start"] if idx + 1 < len(issue_segments) else len(doc)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for seg in issue_segments:
            issue_doc = fitz.open()
            issue_doc.insert_pdf(doc, from_page=seg["start"], to_page=seg["end"] - 1)
            pdf_bytes = issue_doc.write()
            issue_doc.close()

            # Generate filename based on format
            if format_choice == "IssueID_Location":
                filename = f"Issue_{seg['issue_id']}_{seg['location']}.pdf"
            elif format_choice == "EquipmentID_IssueID_Status":
                filename = f"{seg['equipment_id']}_Issue_{seg['issue_id']}_{seg['status']}.pdf"
            elif format_choice == "Status_EquipmentID_Location":
                filename = f"{seg['status']}_{seg['equipment_id']}_{seg['location']}.pdf"
            elif format_choice == "Custom":
                filename = custom_format.format(
                    IssueID=seg['issue_id'],
                    Location=seg['location'],
                    Status=seg['status'],
                    EquipmentID=seg['equipment_id']
                ) + ".pdf"
            else:
                filename = f"Issue_{seg['issue_id']}_{seg['location']}.pdf"

            zipf.writestr(filename, pdf_bytes)

    return zip_buffer

# --- Upload Section ---
st.markdown("""
    <div style='background-color: #f9f9f9; padding: 20px; border-radius: 10px;'>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Choose your BIM 360 issue report PDF", type="pdf")

st.markdown("""</div>""", unsafe_allow_html=True)

if uploaded_file:
    with st.spinner("🔄 Splitting issues and processing your file..."):
        zip_file = extract_issues_from_pdf(uploaded_file)
        st.success("✅ Done! Download your ZIP below.")

        st.download_button(
            label="📦 Download All Split Issues",
            data=zip_file.getvalue(),
            file_name="Split_Issues.zip",
            mime="application/zip",
            use_container_width=True
        )

# --- Footer ---
st.markdown("""
    <br><hr>
    <p style='text-align: center; font-size: 13px;'>Made with ❤️ to speed up your QA documentation.</p>
""", unsafe_allow_html=True)

