
import streamlit as st
import datetime
from utils import extract_entries_from_pdf, extract_bim360_entries, extract_acc_build_entries

st.set_page_config(page_title="Issue Report Splitter", layout="centered")

st.title("📄 Issue Report Splitter")

uploaded_file = st.file_uploader("Upload a BIM 360 or ACC Build Issue Report PDF", type="pdf")

report_type = None
format_option = None
zip_buffer = None
summary_data = None

if uploaded_file:
    file_content = uploaded_file.read()
    uploaded_file.seek(0)

    # Peek to determine type
    sample_text = uploaded_file.getvalue().decode('latin1', errors='ignore')
    if "Issue #" in sample_text or "Location Detail" in sample_text:
        report_type = "BIM 360"
    elif "#0" in sample_text or "Equipment ID" in sample_text:
        report_type = "ACC Build"

    st.success(f"Detected Report Type: {report_type}")

    # Filename options based on type
    if report_type == "BIM 360":
        format_option = st.selectbox(
            "Choose filename format",
            ["Issue_{IssueID}_{LocationDetail}", "Issue_{IssueID}"]
        )
    elif report_type == "ACC Build":
        format_option = st.selectbox(
            "Choose filename format",
            ["#{IssueID}_{EquipmentID}_{LocationDetail}", "#{IssueID}_{LocationDetail}"]
        )

    if st.button("Split Report"):
        with st.spinner("Processing..."):
            uploaded_file.seek(0)
            if report_type == "BIM 360":
                summary_data, zip_buffer = extract_bim360_entries(uploaded_file)
            elif report_type == "ACC Build":
                summary_data, zip_buffer = extract_acc_build_entries(uploaded_file)
            else:
                st.error("Could not detect report type.")

        if summary_data:
            st.success("✅ Report split successfully.")
            st.dataframe(summary_data)

            today = datetime.datetime.now().strftime("%Y-%m-%d")
            st.download_button(
                label="📦 Download ZIP",
                data=zip_buffer,
                file_name=f"Issue Report - {today}.zip",
                mime="application/zip"
            )
        else:
            st.error("❌ No issues found. Please check the file format.")

