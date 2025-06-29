import streamlit as st
import fitz  # PyMuPDF
import zipfile
import io
import re
import datetime

st.set_page_config(page_title="Issue Report Splitter", page_icon="📄", layout="centered")

st.markdown("""
    <div style='text-align: center; padding-top: 10px;'>
        <h1 style='color: #2c3e50;'>📄 Issue Report Splitter</h1>
        <p style='font-size: 17px; color: #555;'>Quickly split BIM 360 or ACC Build issue reports into individual PDFs with custom filenames.</p>
    </div>
    <hr>
""", unsafe_allow_html=True)

st.sidebar.header("Options")
auto_detect = st.sidebar.checkbox("Auto-detect report type", value=True)

report_type = None
if not auto_detect:
    report_type = st.sidebar.radio("Select issue report type:", ["BIM 360", "ACC Build"])

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

def detect_report_type(first_page_text):
    if re.search(r"#\d+:", first_page_text):
        return "ACC Build"
    elif re.search(r"ID\s+\d+.*Location Detail", first_page_text):
        return "BIM 360"
    return None

def extract_entries_from_pdf(uploaded_pdf):
    doc = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")
    segments = []

    first_page_text = doc[0].get_text()
    detected_type = detect_report_type(first_page_text) if auto_detect else report_type

    if not detected_type:
        st.warning("Could not detect report type. Please switch off auto-detect and choose manually.")
        return None

    for i in range(len(doc)):
        text = doc[i].get_text()
        lines = text.splitlines()

        if detected_type == "ACC Build":
            header_match = re.match(r"^#(\d+):", lines[0].strip()) if lines else None
            if header_match:
                issue_id = header_match.group(1)
                status = next((re.search(r"Status\s+(\w+)", l).group(1) for l in lines if re.search(r"Status\s+(\w+)", l)), "Unknown")
                location = next((re.search(r"Location\s+(.*)", l).group(1).replace(".", "_") for l in lines if l.startswith("Location")), "Unknown")
                equipment = next((re.search(r"Equipment ID\s+(\S+)", l).group(1) for l in lines if re.search(r"Equipment ID\s+(\S+)", l)), "NA")
                segments.append({
                    "entry_id": issue_id,
                    "location": location,
                    "status": status,
                    "equipment_id": equipment,
                    "start": i
                })

        elif detected_type == "BIM 360":
            if "ID" in text and "Location Detail" in text:
                id_match = re.search(r"ID\s+0*(\d+)", text)
                loc_match = re.search(r"Location Detail\s+(T\d{1,3}\.BESS\.\d+)", text, re.IGNORECASE)
                status_match = re.search(r"Status\s+(\w+)", text)
                equip_match = re.search(r"Equipment ID\s+(\S+)", text, re.IGNORECASE)

                if id_match and loc_match:
                    segments.append({
                        "entry_id": id_match.group(1),
                        "location": loc_match.group(1).replace(".", "_"),
                        "status": status_match.group(1) if status_match else "Unknown",
                        "equipment_id": equip_match.group(1) if equip_match else "NA",
                        "start": i
                    })

    if not segments:
        st.warning("No entries matched your selected or detected report type.")
        return None

    for idx in range(len(segments)):
        segments[idx]["end"] = segments[idx + 1]["start"] if idx + 1 < len(segments) else len(doc)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for seg in segments:
            entry_doc = fitz.open()
            entry_doc.insert_pdf(doc, from_page=seg["start"], to_page=seg["end"] - 1)
            pdf_bytes = entry_doc.write()
            entry_doc.close()

            if format_choice == "IssueID_Location":
                filename = f"Issue_{seg['entry_id']}_{seg['location']}.pdf"
            elif format_choice == "EquipmentID_IssueID_Status":
                filename = f"{seg['equipment_id']}_Issue_{seg['entry_id']}_{seg['status']}.pdf"
            elif format_choice == "Status_EquipmentID_Location":
                filename = f"{seg['status']}_{seg['equipment_id']}_{seg['location']}.pdf"
            elif format_choice == "Custom":
                filename = custom_format.format(
                    IssueID=seg['entry_id'],
                    Location=seg['location'],
                    Status=seg['status'],
                    EquipmentID=seg['equipment_id']
                ) + ".pdf"
            else:
                filename = f"Issue_{seg['entry_id']}_{seg['location']}.pdf"

            zipf.writestr(filename, pdf_bytes)

    return zip_buffer

st.markdown("""
    <div style='background-color: #f9f9f9; padding: 20px; border-radius: 10px;'>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Choose your BIM 360 or ACC Build issue report PDF", type="pdf")

st.markdown("""</div>""", unsafe_allow_html=True)

if uploaded_file:
    with st.spinner("🔄 Splitting entries and processing your file..."):
        zip_file = extract_entries_from_pdf(uploaded_file)
        if zip_file:
            st.success("✅ Done! Download your ZIP below.")

            today_str = datetime.datetime.today().strftime("%Y-%m-%d")
            zip_name = f"Issue Report - {today_str}.zip"

            st.download_button(
                label="📦 Download Split Reports ZIP",
                data=zip_file.getvalue(),
                file_name=zip_name,
                mime="application/zip",
                use_container_width=True
            )

st.markdown("""
    <br><hr>
    <div style='text-align: center; color: #888;'>
        <p style='font-size: 13px;'>Built for QA & Field Engineers • Streamlined PDF tools for BIM 360 / ACC Build</p>
    </div>
""", unsafe_allow_html=True)
