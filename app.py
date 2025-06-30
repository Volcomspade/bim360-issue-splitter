import streamlit as st
from utils import (
    detect_report_type_from_pdf,
    extract_bim360_issues_fixed,
    extract_acc_build_issues
)
import os
from pathlib import Path
import shutil
from zipfile import ZipFile

st.set_page_config(page_title="Issue Splitter", layout="centered")
st.title("🧩 BIM 360 / ACC Build Issue Splitter")

uploaded_file = st.file_uploader("Upload a BIM 360 or ACC Build issue report PDF", type=["pdf"])

if uploaded_file:
    input_path = f"/mnt/data/input_{uploaded_file.name}"
    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    report_type = detect_report_type_from_pdf(input_path)
    st.info(f"Detected report type: **{report_type}**")

    out_dir = "/mnt/data/split_output"
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    if report_type == "BIM 360":
        files = extract_bim360_issues_fixed(input_path)
    elif report_type == "ACC Build":
        files = extract_acc_build_issues(input_path)
    else:
        st.error("Could not detect a valid report type. Make sure the report is BIM 360 or ACC Build.")
        files = []

    if files:
        zip_path = "/mnt/data/Split_Issues.zip"
        with ZipFile(zip_path, "w") as zipf:
            for file in files:
                zipf.write(file, arcname=os.path.basename(file))
        st.success(f"✅ Split into {len(files)} issues.")
        with open(zip_path, "rb") as f:
            st.download_button("📦 Download ZIP", f, file_name="Split_Issues.zip", mime="application/zip")
    else:
        st.warning("No issues found.")
