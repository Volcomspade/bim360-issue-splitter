import streamlit as st
import zipfile
from io import BytesIO
from utils import split_bim360_report
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Issue Report Splitter", layout="wide")

st.title("📄 Issue Report Splitter")

uploaded_file = st.file_uploader("Upload a BIM 360 issue report PDF", type="pdf")

if uploaded_file:
    st.success("PDF uploaded. Attempting to identify and parse issues...")

    filename_format = st.selectbox("Filename format:", [
        "{IssueID}_{Location}_{LocationDetail}_{EquipmentID}",
        "{IssueID}_{Location}",
        "{IssueID}"
    ])

    if st.button("Split Report"):
        with st.spinner("Processing..."):
            files, summary = split_bim360_report(uploaded_file, filename_format)

            if not files:
                st.error("No issues found or failed to split.")
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