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

st.markdown("## 📝 Issue Report Splitter")
st.caption("Quickly split BIM 360 or ACC Build issue reports into individual PDFs with custom filenames.")

uploaded_file = st.file_uploader("Choose your BIM 360 or ACC Build issue report PDF", type="pdf")

# Default format for filenames
format_choice = "Custom"
custom_format = "{IssueID}_{Location}_{EquipmentID}"

if uploaded_file:
    with st.spinner("🔄 Splitting entries and processing your file..."):
        try:
            zip_file, summary_data = extract_entries_from_pdf(
                uploaded_file,
                auto_detect=True,
                format_choice=format_choice,
                custom_format=custom_format
            )
        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.stop()

    if zip_file and hasattr(zip_file, "getvalue"):
        today_str = datetime.today().strftime("%Y-%m-%d")
        zip_name = f"Issue Report - {today_str}.zip"

        st.success("✅ Done! Download your ZIP below.")
        st.download_button(
            label="📂 Download Split Reports ZIP",
            data=zip_file.getvalue(),
            file_name=zip_name,
            mime="application/zip"
        )

        if summary_data is not None:
            st.markdown("### 📄 Summary of Split Reports")
            st.dataframe(summary_data)
    else:
        st.error("⚠️ No valid entries found. Check the report type or file contents.")
