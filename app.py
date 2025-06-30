
import streamlit as st
from utils import detect_report_type, extract_bim360_issues, extract_acc_build_issues

st.set_page_config(page_title="Issue Report Splitter")
st.title("🧾 Issue Report Splitter")

uploaded_file = st.file_uploader("Upload a BIM 360 or ACC Build Issue Report", type=["pdf"])
if uploaded_file:
    file_path = f"/tmp/{uploaded_file.name}"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())

    report_type = detect_report_type(file_path)
    st.success(f"Detected Report Type: {report_type}")
