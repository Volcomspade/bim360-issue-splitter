import streamlit as st
from utils import process_uploaded_file, split_bim360_pdf, split_acc_build_pdf, construct_filename
from datetime import datetime
from pathlib import Path
import shutil

st.set_page_config(page_title="Issue Report Splitter", layout="centered")

st.title("📄 Issue Report Splitter")

uploaded_file = st.file_uploader("Upload a BIM 360 or ACC Build Issue Report (PDF)", type="pdf")

report_type = st.selectbox("Report Type (auto-detect preferred):", ["Auto Detect", "BIM 360", "ACC Build"])

field_options = {
    "Issue ID": "IssueID",
    "Title": "Title",
    "Location": "Location",
    "Location Detail": "LocationDetail",
    "Equipment ID": "EquipmentID",
    "Status": "Status"
}

selected_fields = st.multiselect(
    "Choose fields for filename (drag to reorder):",
    options=list(field_options.keys()),
    default=["Issue ID", "Location", "Location Detail"]
)
filename_format = "_".join([field_options[f] for f in selected_fields])

if uploaded_file:
    with st.spinner("Processing file..."):
        report_bytes = uploaded_file.read()
        detected_type, summary, zip_path = process_uploaded_file(report_bytes, report_type, filename_format)

    st.success(f"Processed as {detected_type} report. Found {len(summary)} issues.")
    for item in summary:
        st.text(f"Issue {item['IssueID']} — Pages {item['StartPage'] + 1} to {item['EndPage'] + 1}")

    st.download_button("📦 Download Split Issues", zip_path, file_name=f"Issue Report - {datetime.now().date()}.zip")