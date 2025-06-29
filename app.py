
import streamlit as st
from datetime import datetime
from utils import (
    detect_report_type,
    extract_bim360_entries,
    extract_acc_build_entries,
    get_filename_formats
)
import io
import zipfile

st.set_page_config(page_title="Issue Report Splitter", layout="centered")
st.title("📄 Issue Report Splitter")
st.markdown("Upload a BIM 360 or ACC Build issue report PDF to split each issue into its own file.")

uploaded_file = st.file_uploader("Choose a PDF report", type="pdf")

if uploaded_file:
    with st.spinner("Detecting report type..."):
        uploaded_bytes = uploaded_file.read()
        report_type = detect_report_type(uploaded_bytes)
    
    if report_type:
        st.success(f"Detected Report Type: {report_type}")
        format_options = get_filename_formats(report_type)
        filename_format = st.selectbox("Choose filename format", format_options)

        if st.button("Split Report"):
            with st.spinner("Processing and splitting the report..."):
                if report_type == "BIM 360":
                    summary_data, zip_buffer = extract_bim360_entries(uploaded_bytes, filename_format)
                else:
                    summary_data, zip_buffer = extract_acc_build_entries(uploaded_bytes, filename_format)
            
            if summary_data and zip_buffer:
                st.success(f"✅ {len(summary_data)} issues extracted!")
                st.download_button(
                    label="📁 Download ZIP",
                    data=zip_buffer.getvalue(),
                    file_name="split_issues.zip",
                    mime="application/zip"
                )
                st.subheader("🗂️ Summary")
                st.dataframe(summary_data)
            else:
                st.error("⚠️ No valid entries found. Check the report type or file contents.")
    else:
        st.error("❌ Could not determine report type. Make sure this is a valid BIM 360 or ACC Build issue report.")
