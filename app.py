# app.py - Streamlit app for splitting BIM 360 / ACC Build issue reports
import streamlit as st
from utils import extract_entries_from_pdf
from datetime import datetime
import base64

st.set_page_config(page_title="Issue Report Splitter", layout="wide")

# ----- Sidebar -----
st.sidebar.title("Options")
auto_detect = st.sidebar.checkbox("Auto-detect report type", value=True)

format_choice = st.sidebar.selectbox("Choose filename format:", [
    "IssueID_Location",
    "BuildID_Location",
    "Status_EquipmentID_Location",
    "Custom"
])

custom_format = st.sidebar.text_input("If Custom, use Python format keys:",
    "{IssueID}_{Location}_{Status}")

# ----- Main Title -----
st.markdown("""
    <h1 style='text-align: center;'>📄 Issue Report Splitter</h1>
    <p style='text-align: center;'>Quickly split BIM 360 or ACC Build issue reports into individual PDFs with custom filenames.</p>
""", unsafe_allow_html=True)

# ----- File Upload -----
uploaded_file = st.file_uploader("Choose your BIM 360 or ACC Build issue report PDF", type="pdf")

# ----- Process File -----
if uploaded_file:
    with st.spinner("🔄 Splitting entries and processing your file..."):
        try:
            zip_file, summary_data = extract_entries_from_pdf(
                uploaded_file,
                auto_detect=auto_detect,
                format_choice=format_choice,
                custom_format=custom_format
            )

            today_str = datetime.today().strftime("%Y-%m-%d")
            zip_name = f"Issue Report - {today_str}.zip"

            b64 = base64.b64encode(zip_file.getvalue()).decode()
            href = f'<a href="data:application/zip;base64,{b64}" download="{zip_name}">📦 Download Split Reports ZIP</a>'
            st.success("✅ Done! Download your ZIP below.")
            st.markdown(href, unsafe_allow_html=True)

            # ----- Summary Table -----
            st.markdown("""
                <h3 style='margin-top: 2em;'>📋 Summary of Split Reports</h3>
            """, unsafe_allow_html=True)
            st.dataframe(summary_data, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.stop()

# ----- Light/Dark Mode Toggle -----
st.markdown("""
    <style>
    body {
        transition: background 0.5s;
    }
    </style>
""", unsafe_allow_html=True)

# Footer
st.markdown("""
    <hr style='margin-top: 3em;'>
    <p style='text-align: center; font-size: 0.8em;'>Built for QA & Field Engineers • Streamlined PDF tools for BIM 360 / ACC Build</p>
""", unsafe_allow_html=True)
