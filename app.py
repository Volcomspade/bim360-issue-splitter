
import streamlit as st
from utils import (
    detect_report_type,
    extract_bim360_issues,
    extract_acc_build_issues,
    zip_issue_pdfs,
    get_available_fields
)
from datetime import datetime

st.set_page_config(page_title="Issue Report Splitter", layout="centered")
st.title("📄 Issue Report Splitter")

with st.sidebar:
    st.markdown("### Upload your issue report PDF")
    uploaded_file = st.file_uploader("Choose a PDF", type="pdf")
    st.markdown("---")
    st.markdown("Made for QA teams to split BIM 360 and ACC Build issue reports into separate files.")

if uploaded_file:
    report_type = detect_report_type(uploaded_file)

    if not report_type:
        st.error("⚠️ Could not detect report type. Please check the file and try again.")
    else:
        st.success(f"Detected: {report_type} Report")

        fields = get_available_fields(report_type)
        filename_fields = st.multiselect("Select fields for filename:", fields, default=fields[:2])
        field_order = st.text_input("Enter order (comma-separated):", value=",".join(filename_fields))

        if st.button("Split Report"):
            with st.spinner("Processing..."):
                if report_type == "BIM 360":
                    issues = extract_bim360_issues(uploaded_file)
                else:
                    issues = extract_acc_build_issues(uploaded_file)

                ordered_fields = [f.strip() for f in field_order.split(",") if f.strip() in fields]
                zip_file = zip_issue_pdfs(issues, ordered_fields, report_type)

                if zip_file:
                    today = datetime.today().strftime("%Y-%m-%d")
                    st.success("✅ Done! Download your split issue files below.")
                    st.download_button("📦 Download ZIP", zip_file.getvalue(), file_name=f"Issue Report - {today}.zip")
                else:
                    st.error("❌ No issues found or failed to generate files.")
