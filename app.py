import streamlit as st
from datetime import datetime
from utils import extract_entries_from_pdf

st.set_page_config(page_title="Issue Report Splitter", layout="centered")

# Theme toggle
theme = st.toggle("🌗 Toggle Dark Mode", value=True)
if theme:
    st.markdown(
        """
        <style>
        body { background-color: #0e1117; color: white; }
        .stDataFrame { background-color: #1c1f26; }
        </style>
        """,
        unsafe_allow_html=True
    )

st.title("📄 Issue Report Splitter")
st.write("Quickly split BIM 360 or ACC Build issue reports into individual PDFs with custom filenames.")

uploaded_file = st.file_uploader("Choose your BIM 360 or ACC Build issue report PDF", type="pdf")

if uploaded_file:
    with st.spinner("Processing PDF..."):
        zip_buffer, summary_data = extract_entries_from_pdf(uploaded_file)

    if summary_data is None or zip_buffer is None:
        st.error("⚠️ No valid entries found. Check the report type or file contents.")
    else:
        st.success(f"✅ Found {len(summary_data)} issues!")
        st.download_button(
            label="📦 Download ZIP of Issues",
            data=zip_buffer.getvalue(),
            file_name="split_issues.zip",
            mime="application/zip"
        )

        st.subheader("📋 Summary")
        st.dataframe(summary_data)
