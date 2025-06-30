
import streamlit as st
from pathlib import Path
from utils import process_uploaded_file, detect_report_type
import zipfile

st.set_page_config(page_title="Issue Report Splitter")

st.title("📄 Issue Report Splitter")
st.write("Upload a BIM 360 or ACC Build issue report PDF to split each issue into its own file.")

uploaded_file = st.file_uploader("Choose a PDF report", type=["pdf"])
if uploaded_file:
    input_pdf_path = Path(f"/tmp/{uploaded_file.name}")
    with open(input_pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    first_page_text = detect_report_type(input_pdf_path)
    detected_type, summary = "Unknown", []

    if "#1:" in first_page_text or "#01:" in first_page_text:
        detected_type = "ACC Build"
    elif "Issue ID:" in first_page_text:
        detected_type = "BIM 360"

    st.success(f"Detected Report Type: {detected_type}")

    filename_fields = []
    if detected_type == "BIM 360":
        filename_fields = ["IssueID", "Location", "LocationDetail", "EquipmentID"]
    elif detected_type == "ACC Build":
        filename_fields = ["Issue ID", "Location", "Location Detail", "Equipment ID"]

    selected_fields = st.multiselect(
        "Choose fields for filename (drag to reorder):",
        filename_fields,
        default=filename_fields[:2]
    )

    if st.button("Split Report"):
        output_dir = Path("/tmp/split_issues")
        output_dir.mkdir(parents=True, exist_ok=True)

        filename_format = "_".join(["{" + field + "}" for field in selected_fields])
        detected_type, summary = process_uploaded_file(
            input_pdf_path, detected_type, filename_format, output_dir
        )

        if summary:
            zip_path = Path("/tmp/split_issues.zip")
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for pdf_file in output_dir.glob("*.pdf"):
                    zipf.write(pdf_file, arcname=pdf_file.name)

            with open(zip_path, "rb") as f:
                st.download_button("⬇️ Download Split Issues", f, file_name="split_issues.zip")

        else:
            st.error("No issues were extracted or split. Please check your PDF formatting.")
