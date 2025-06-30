import streamlit as st
from utils import detect_report_type, extract_bim360_issues, extract_acc_issues, generate_filename
import zipfile
import os
import tempfile

st.set_page_config(page_title="Issue Report Splitter", layout="centered")

st.title("📄 Issue Report Splitter")

uploaded_file = st.file_uploader("Upload a PDF Report", type=["pdf"])
filename_format = None
field_order = []

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        temp_path = tmp_file.name

    report_type = detect_report_type(temp_path)
    st.success(f"Detected Report Type: {report_type}")

    # Show filename format options
    if report_type == "BIM 360":
        fields = ["IssueID", "Location", "LocationDetail", "EquipmentID"]
    elif report_type == "ACC Build":
        fields = ["Issue#", "Location", "Title", "Status"]
    else:
        fields = []

    if fields:
        filename_format = st.multiselect("Choose filename fields", fields, default=fields[:2])
        order = st.text_input("Enter display order (comma-separated)", ",".join(map(str, range(1, len(filename_format)+1))))
        try:
            indices = [int(i.strip()) - 1 for i in order.split(",")]
            field_order = [filename_format[i] for i in indices if 0 <= i < len(filename_format)]
        except:
            st.warning("⚠️ Invalid order format. Using default.")

    if st.button("Split and Download"):
        with tempfile.TemporaryDirectory() as output_dir:
            if report_type == "BIM 360":
                files = extract_bim360_issues(temp_path, output_dir, field_order)
            elif report_type == "ACC Build":
                files = extract_acc_issues(temp_path, output_dir, field_order)
            else:
                st.error("Unsupported report type.")
                st.stop()

            zip_path = os.path.join(output_dir, "issues.zip")
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for file in files:
                    zipf.write(file, os.path.basename(file))

            with open(zip_path, "rb") as f:
                st.download_button("📦 Download ZIP", f, file_name="issue_reports.zip")
