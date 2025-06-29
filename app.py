import streamlit as st
import fitz  # PyMuPDF
import zipfile
import io
import re

st.set_page_config(page_title="BIM 360 Issue Report Splitter", page_icon="📄", layout="centered")

# --- Title and Header ---
st.markdown("""
    <h2 style='text-align: center; color: #333;'>📄 BIM 360 Issue Report Splitter</h2>
    <p style='text-align: center; font-size: 16px;'>Split your BIM 360 Issue or Build reports into separate PDFs.</p>
""", unsafe_allow_html=True)

st.markdown("---")

# --- Report Type ---
report_type = st.sidebar.radio("Select report type:", ["Issue Report", "Build Report"])

# --- Filename Format Selection ---
st.sidebar.header("Filename Options")
format_choice = st.sidebar.selectbox("Choose filename format:", (
    "IssueID_Location" if report_type == "Issue Report" else "BuildID_Location",
    "EquipmentID_IssueID_Status" if report_type == "Issue Report" else "Status_BuildType_Location",
    "Status_EquipmentID_Location" if report_type == "Issue Report" else "Location_Status_BuildType",
    "Custom"
))

custom_format = ""
if format_choice == "Custom":
    placeholder_keys = "{IssueID}, {Location}, {Status}, {EquipmentID}" if report_type == "Issue Report" else "{BuildID}, {Location}, {Status}, {BuildType}"
    custom_format = st.sidebar.text_input(f"Custom format using: {placeholder_keys}",
                                          "{Status}_{IssueID}_{Location}" if report_type == "Issue Report" else "{BuildID}_{Location}_{Status}")

def extract_entries_from_pdf(uploaded_pdf):
    doc = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")
    segments = []

    for i in range(len(doc)):
        text = doc[i].get_text()

        if report_type == "Issue Report":
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

        else:
            if "Build Detail" in text and "Build Detail ID" in text:
                id_match = re.search(r"Build Detail ID\s+0*(\d+)", text)
                loc_match = re.search(r"Location\s+(T\d{1,3}\.BESS\.\d+)", text, re.IGNORECASE)
                status_match = re.search(r"Status\s+(\w+)", text)
                type_match = re.search(r"Build Type\s+([\w /&-]+)", text, re.IGNORECASE)

                if id_match and loc_match:
                    segments.append({
                        "entry_id": id_match.group(1),
                        "location": loc_match.group(1).replace(".", "_"),
                        "status": status_match.group(1) if status_match else "Unknown",
                        "build_type": type_match.group(1).replace(" ", "_") if type_match else "Unknown",
                        "start": i
                    })

    for idx in range(len(segments)):
        segments[idx]["end"] = segments[idx + 1]["start"] if idx + 1 < len(segments) else len(doc)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for seg in segments:
            entry_doc = fitz.open()
            entry_doc.insert_pdf(doc, from_page=seg["start"], to_page=seg["end"] - 1)
            pdf_bytes = entry_doc.write()
            entry_doc.close()

            if report_type == "Issue Report":
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
            else:
                if format_choice == "BuildID_Location":
                    filename = f"Build_{seg['entry_id']}_{seg['location']}.pdf"
                elif format_choice == "Status_BuildType_Location":
                    filename = f"{seg['status']}_{seg['build_type']}_{seg['location']}.pdf"
                elif format_choice == "Location_Status_BuildType":
                    filename = f"{seg['location']}_{seg['status']}_{seg['build_type']}.pdf"
                elif format_choice == "Custom":
                    filename = custom_format.format(
                        BuildID=seg['entry_id'],
                        Location=seg['location'],
                        Status=seg['status'],
                        BuildType=seg['build_type']
                    ) + ".pdf"
                else:
                    filename = f"Build_{seg['entry_id']}_{seg['location']}.pdf"

            zipf.writestr(filename, pdf_bytes)

    return zip_buffer

# --- Upload Section ---
st.markdown("""
    <div style='background-color: #f9f9f9; padding: 20px; border-radius: 10px;'>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Choose your BIM 360 report PDF", type="pdf")

st.markdown("""</div>""", unsafe_allow_html=True)

if uploaded_file:
    with st.spinner("🔄 Splitting entries and processing your file..."):
        zip_file = extract_entries_from_pdf(uploaded_file)
        st.success("✅ Done! Download your ZIP below.")

        st.download_button(
            label="📦 Download Split Reports ZIP",
            data=zip_file.getvalue(),
            file_name="Split_Reports.zip",
            mime="application/zip",
            use_container_width=True
        )

# --- Footer ---
st.markdown("""
    <br><hr>
    <p style='text-align: center; font-size: 13px;'>Made with ❤️ to speed up your QA and build documentation.</p>
""", unsafe_allow_html=True)
