
import streamlit as st
import tempfile
import datetime
from utils import detect_report_type, extract_bim_issues, extract_acc_issues, split_pdf_by_issues

st.set_page_config(page_title="Issue Report Splitter", layout="wide")
st.title("📄 Issue Report Splitter")

uploaded_file = st.file_uploader("Upload your Issue Report PDF", type=["pdf"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        pdf_path = tmp.name

    report_type = detect_report_type(pdf_path)
    st.success(f"Detected Report Type: **{report_type}**")

    if report_type == "BIM 360":
        filename_format = st.selectbox("Filename format", [
            "Issue_{IssueID}",
            "BIM360_{IssueID}",
        ])
        doc, issue_ranges = extract_bim_issues(pdf_path)

    elif report_type == "ACC Build":
        filename_format = st.selectbox("Filename format", [
            "Issue_{IssueID}",
            "ACC_{IssueID}",
        ])
        doc, issue_ranges = extract_acc_issues(pdf_path)

    else:
        st.error("Unknown report format.")
        st.stop()

    if st.button("Split Issues"):
        with st.spinner("Splitting issues..."):
            summary_df, zip_buffer = split_pdf_by_issues(doc, issue_ranges, filename_format)
            date_str = datetime.date.today().isoformat()
            zip_filename = f"Issue Report - {date_str}.zip"
            st.download_button("Download ZIP", zip_buffer.getvalue(), file_name=zip_filename, mime="application/zip")
            st.dataframe(summary_df)
