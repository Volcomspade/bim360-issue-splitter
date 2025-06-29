import streamlit as st
import zipfile
from io import BytesIO
from datetime import datetime
import pandas as pd
from utils import split_bim360_report, split_acc_build_report

st.set_page_config(page_title="Issue Report Splitter", layout="wide")

st.title("📄 Issue Report Splitter")

uploaded_file = st.file_uploader("Upload an issue report PDF", type="pdf")

def detect_report_type(pdf_file):
    import fitz
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
        if "#1" in text:
            return "ACC Build"
        if "ID " in text:
            return "BIM 360"
    return "Unknown"

if uploaded_file:
    st.success("PDF uploaded.")

    # Rewind file for reading multiple times
    uploaded_file.seek(0)
    report_type = detect_report_type(uploaded_file)

    st.subheader(f"📑 Detected Report Type: `{report_type}`")

    filename_format = ""
    files = []
    summary = []

    if report_type == "BIM 360":
        available_fields = ["IssueID", "Location", "LocationDetail", "EquipmentID"]
    elif report_type == "ACC Build":
        available_fields = ["IssueNumber", "Location", "LocationDetail", "EquipmentID"]
    else:
        st.error("❌ Could not detect report type. Ensure it’s a valid issue report.")
        st.stop()

    chosen_fields = st.multiselect("Select fields to include in filename:", available_fields, default=available_fields)
    separator = st.selectbox("Choose separator:", ["_", "-", " "], index=0)

    if chosen_fields:
        filename_format = separator.join([f"{{{field}}}" for field in chosen_fields])
        st.markdown(f"**Filename format preview:** `{filename_format}.pdf`")

        if st.button("Split Report"):
            uploaded_file.seek(0)
            with st.spinner("Processing..."):
                if report_type == "BIM 360":
                    files, summary = split_bim360_report(uploaded_file, filename_format)
                else:
                    files, summary = split_acc_build_report(uploaded_file, filename_format)

                if not files:
                    st.error("❌ No issues found or failed to split.")
                else:
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w") as zipf:
                        for name, buffer in files:
                            zipf.writestr(name, buffer.getvalue())
                    zip_buffer.seek(0)

                    today = datetime.today().strftime("%Y-%m-%d")
                    st.download_button("📦 Download ZIP", zip_buffer, file_name=f"Issue Report - {today}.zip")

                    if summary:
                        st.subheader("📋 Summary Table")
                        st.dataframe(pd.DataFrame(summary))