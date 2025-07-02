
import streamlit as st
from utils import detect_report_type, extract_bim_issues, format_bim_filename
from datetime import datetime
import tempfile
import shutil
import zipfile
import os

st.set_page_config(page_title="BIM 360 Issue Report Splitter", layout="centered")
st.title("📄 BIM 360 Issue Report Splitter")

uploaded_file = st.file_uploader("Upload a BIM 360 issue report PDF", type="pdf")

if uploaded_file:
    with tempfile.TemporaryDirectory() as tmpdirname:
        input_path = os.path.join(tmpdirname, uploaded_file.name)
        with open(input_path, "wb") as f:
            f.write(uploaded_file.read())

        report_type = detect_report_type(input_path)

        if report_type != "BIM 360":
            st.error("Only BIM 360 reports are supported in this version.")
        else:
            filename_format = st.selectbox("Filename Format", [
                "{IssueID}_{Location}",
                "{IssueID}_{Location}_{LocationDetail}",
                "{IssueID}_{Location}_{LocationDetail}_{EquipmentID}"
            ])
            if st.button("Split Report"):
                issues = extract_bim_issues(input_path)
                timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                zip_path = os.path.join(tmpdirname, f"Issue_Report_{timestamp}.zip")
                with zipfile.ZipFile(zip_path, "w") as zipf:
                    for issue in issues:
                        filename = format_bim_filename(issue, filename_format)
                        zipf.writestr(f"{filename}.pdf", issue["pdf"].getvalue())
                with open(zip_path, "rb") as f:
                    st.download_button("Download ZIP", f, file_name=f"Issue_Report_{timestamp}.zip")
