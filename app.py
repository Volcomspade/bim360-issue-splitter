
import streamlit as st
from utils import (
    detect_report_type,
    split_bim360_pdf,
    split_acc_build_pdf
)
from pathlib import Path

def main():
    st.title("Issue Report Splitter")

    uploaded_file = st.file_uploader("Upload a BIM 360 or ACC Build Issue Report (PDF)", type=["pdf"])
    if uploaded_file is not None:
        input_path = Path("temp") / uploaded_file.name
        input_path.parent.mkdir(parents=True, exist_ok=True)
        input_path.write_bytes(uploaded_file.read())

        detected_type = detect_report_type(input_path)

        if detected_type == "BIM 360":
            files = split_bim360_pdf(input_path, ["Issue ID", "Location", "Location Detail"], "output")
        elif detected_type == "ACC Build":
            files = split_acc_build_pdf(input_path, ["Issue ID", "Location", "Location Detail"], "output")
        else:
            st.error("Could not detect report type.")
            return

        st.success(f"Processed {len(files)} issues.")
        for file in files:
            st.download_button(label=f"Download {file.name}", data=file.read_bytes(), file_name=file.name)

if __name__ == "__main__":
    main()
