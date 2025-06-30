
import streamlit as st
from utils import detect_report_type, extract_bim360_issues_fixed, extract_acc_build_issues
from pathlib import Path

st.set_page_config(page_title="Issue Report Splitter", layout="centered")
st.title("📄 Issue Report Splitter")
st.caption("Upload a BIM 360 or ACC Build issue report PDF to split each issue into its own file.")

uploaded_file = st.file_uploader("Choose a PDF report", type=["pdf"])
filename_format = []
detected_type = None

if uploaded_file:
    input_path = Path("input.pdf")
    with open(input_path, "wb") as f:
        f.write(uploaded_file.read())

    with st.spinner("Analyzing report..."):
        try:
            detected_type = detect_report_type(input_path)
        except Exception as e:
            st.error(f"Error during detection: {e}")

    st.success(f"Detected Report Type: {detected_type}" if detected_type else "Unknown report format")

    field_options = []
    if detected_type == "BIM 360":
        field_options = ["Issue ID", "Location", "Location Detail", "Equipment ID"]
    elif detected_type == "ACC Build":
        field_options = ["Issue #", "Title", "Location", "Status"]

    filename_format = st.multiselect(
        "Choose fields for filename (drag to reorder):",
        options=field_options,
        default=field_options[:2] if field_options else [],
    )

    if st.button("Split Report"):
        with st.spinner("Splitting report..."):
            try:
                if detected_type == "BIM 360":
                    files = extract_bim360_issues_fixed(input_path, filename_format)
                elif detected_type == "ACC Build":
                    files = extract_acc_build_issues(input_path, filename_format)
                else:
                    raise ValueError("Unsupported or undetected report type.")

                if not files:
                    st.warning("No issues found to export.")
                else:
                    from zipfile import ZipFile
                    from io import BytesIO

                    zip_buffer = BytesIO()
                    with ZipFile(zip_buffer, "w") as zip_file:
                        for f in files:
                            zip_file.write(f, arcname=f.name)

                    st.download_button(
                        "📦 Download Split Issues",
                        zip_buffer.getvalue(),
                        file_name="Split_Issues.zip",
                        mime="application/zip",
                    )
                    st.success(f"{len(files)} issues split successfully.")
            except Exception as e:
                st.error(f"Error while processing report: {e}")
