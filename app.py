import streamlit as st
import tempfile
from pathlib import Path
from utils import process_uploaded_file, get_filename_fields

st.set_page_config(page_title="Issue Report Splitter", layout="centered")

st.title("📄 Issue Report Splitter")
st.markdown("Upload a BIM 360 or ACC Build issue report PDF to split each issue into its own file.")

uploaded_file = st.file_uploader("Choose a PDF report", type=["pdf"])
if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = Path(tmp.name)

    detected_type, filename_fields, preview_data = process_uploaded_file(tmp_path, detect_only=True)

    st.success(f"Detected Report Type: {detected_type}" if detected_type != "Unknown" else "Detected Report Type: Unknown")

    field_order = []
    if detected_type in ["BIM 360", "ACC Build"]:
        field_options = get_filename_fields(detected_type)
        selected_fields = st.multiselect("Choose fields for filename (drag to reorder):", options=field_options, default=field_options)
        if selected_fields:
            field_order = selected_fields

    if st.button("Split Report") and field_order:
        _, zip_path = process_uploaded_file(tmp_path, detected_type=detected_type, filename_fields=field_order)
        if zip_path and zip_path.exists():
            with open(zip_path, "rb") as f:
                st.download_button("📦 Download Split Issues", f.read(), file_name=zip_path.name)
        else:
            st.error("Something went wrong while splitting the report.")