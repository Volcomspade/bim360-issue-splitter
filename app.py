
import streamlit as st
from utils import detect_report_type, extract_bim360_issues_fixed, extract_acc_build_issues
from pathlib import Path
import zipfile
import io

st.title("📄 Issue Report Splitter")
st.write("Upload a BIM 360 or ACC Build issue report PDF to split each issue into its own file.")

uploaded_file = st.file_uploader("Choose a PDF report", type="pdf")

if uploaded_file:
    input_path = Path("temp_report.pdf")
    with open(input_path, "wb") as f:
        f.write(uploaded_file.getvalue())

    # Detect report type
    import fitz
    doc = fitz.open(str(input_path))
    first_page_text = doc[0].get_text()
    detected_type = detect_report_type(first_page_text)

    st.success(f"Detected Report Type: {detected_type}")

    # Let user select filename format
    filename_fields = ["Issue ID", "Location", "Location Detail", "Equipment ID"]
    selected_fields = st.multiselect("Choose fields for filename (drag to reorder):", filename_fields, default=filename_fields[:2])

    if st.button("Split Report"):
        if detected_type == "BIM 360":
            files = extract_bim360_issues_fixed(input_path)
        elif detected_type == "ACC Build":
            files = extract_acc_build_issues(input_path)
        else:
            st.error("Unknown report type. Please verify your PDF.")
            files = []

        # Create a ZIP of files
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            for name, file_bytes in files.items():
                zipf.writestr(name, file_bytes)
        zip_buffer.seek(0)
        st.download_button("⬇️ Download Split Issues", zip_buffer, file_name="Issues.zip")
