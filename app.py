
import streamlit as st
import datetime
from utils import detect_report_type, extract_issues_bim360, build_filename_bim360, save_issue_pdfs
import os
import shutil

st.set_page_config(page_title="📄 Issue Report Splitter", layout="wide")
st.title("📄 Issue Report Splitter")

st.markdown("Upload a BIM 360 Issue Report PDF and split it into individual issue files with custom filenames.")

uploaded_file = st.file_uploader("Upload BIM 360 Issue Report PDF", type=["pdf"])

filename_options = ["IssueID", "Location", "LocationDetail", "EquipmentID"]
default_order = ["IssueID", "Location"]

filename_fields = st.multiselect(
    "Filename fields (choose order)",
    options=filename_options,
    default=default_order,
)

output_dir = "split_issues"
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
zip_filename = f"Issue Report - {timestamp}.zip"

if uploaded_file:
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.read())

    with st.spinner("Detecting report type..."):
        report_type = detect_report_type("temp.pdf")

    if report_type != "bim360":
        st.error("Only BIM 360 reports are supported in this version.")
    else:
        with st.spinner("Extracting BIM 360 issues..."):
            issues = extract_issues_bim360("temp.pdf")

        if not issues:
            st.error("No issues found.")
        else:
            with st.spinner("Saving PDFs..."):
                shutil.rmtree(output_dir, ignore_errors=True)
                os.makedirs(output_dir, exist_ok=True)
                for issue in issues:
                    filename = build_filename_bim360(issue, filename_fields)
                    save_issue_pdfs(issue["pages"], filename, output_dir)

                shutil.make_archive(zip_filename.replace(".zip", ""), 'zip', output_dir)

            st.success(f"Saved {len(issues)} issues!")
            with open(zip_filename, "rb") as f:
                st.download_button("Download ZIP", f, file_name=zip_filename)
