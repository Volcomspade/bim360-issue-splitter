
import streamlit as st
from utils import process_uploaded_file, detect_report_type
from pathlib import Path

st.set_page_config(page_title="Issue Report Splitter", layout="centered")
st.title("📄 Issue Report Splitter")
st.caption("Upload a BIM 360 or ACC Build issue report PDF to split each issue into its own file.")

uploaded_file = st.file_uploader("Choose a PDF report", type="pdf")

if uploaded_file:
    file_path = Path("/tmp") / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())

    with open(file_path, "rb") as f:
        first_page_text = f.read(2048).decode("latin1", errors="ignore")

    report_type = detect_report_type(first_page_text)
    st.success(f"Detected Report Type: {report_type}")

    filename_options = []
    if report_type == "BIM 360":
        filename_options = ["Issue ID", "Location", "Location Detail", "Equipment ID"]
    elif report_type == "ACC Build":
        filename_options = ["Issue ID", "Location", "Serial Number"]

    selected_fields = st.multiselect(
        "Choose fields for filename (drag to reorder):", options=filename_options, default=filename_options
    )

    if st.button("Split Report"):
        with st.spinner("Processing..."):
            detected_type, summary, zip_path = process_uploaded_file(file_path, selected_fields)
            if zip_path:
                with open(zip_path, "rb") as f:
                    st.download_button("⬇️ Download Split Issues", f, file_name=f"Issues_{detected_type.replace(' ', '_')}.zip")
            else:
                st.error("Failed to process the uploaded PDF.")
