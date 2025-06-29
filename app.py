
import streamlit as st
from datetime import datetime
import pandas as pd
from utils import extract_entries_from_pdf

st.set_page_config(page_title="Issue Report Splitter", layout="centered")

st.markdown("## 📄 Issue Report Splitter")
st.write("Upload a BIM 360 or ACC Build issue report PDF to split each issue into its own file.")

uploaded_file = st.file_uploader("Choose a PDF report", type="pdf")

if uploaded_file:
    with st.spinner("Processing..."):
        summary_data, zip_buffer = extract_entries_from_pdf(uploaded_file)

    if not summary_data or not zip_buffer:
        st.error("❌ No valid entries found. Check the report type or file contents.")
    else:
        now = datetime.now().strftime("%Y-%m-%d")
        zip_filename = f"Issue_Report_{now}.zip"
        st.success(f"✅ {len(summary_data)} issues extracted!")
        st.download_button(
            label="📥 Download ZIP",
            data=zip_buffer,
            file_name=zip_filename,
            mime="application/zip"
        )
        st.markdown("### 🧾 Summary")
        st.dataframe(pd.DataFrame(summary_data))
