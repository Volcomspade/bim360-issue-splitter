
import streamlit as st
import tempfile
import os
from datetime import datetime
from utils import detect_report_type, extract_bim_issues, extract_acc_issues, generate_filename_options, save_issue_pdfs, zip_output_folder

st.set_page_config(page_title="Issue Report Splitter", layout="centered")
st.title("📄 Issue Report Splitter")

uploaded_file = st.file_uploader("Upload an Issue Report PDF", type=["pdf"])

if uploaded_file:
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, uploaded_file.name)
        with open(input_path, "wb") as f:
            f.write(uploaded_file.read())

        # Detect report type
        report_type = detect_report_type(input_path)
        st.markdown(f"**Detected Report Type:** `{report_type}`")

        if report_type not in ["BIM 360", "ACC Build"]:
            st.error("❌ Could not detect report type. Please ensure it's a valid BIM 360 or ACC Build issue report.")
        else:
            filename_fields = generate_filename_options(report_type)
            selected_fields = st.multiselect("Select filename components (in order)", filename_fields, default=filename_fields)
            filename_order = st.text_input("Enter field order separated by commas", value=",".join(selected_fields))

            if st.button("🔍 Process Report"):
                ordered_fields = [f.strip() for f in filename_order.split(",") if f.strip() in filename_fields]
                output_dir = os.path.join(tmpdir, "output")
                os.makedirs(output_dir, exist_ok=True)

                try:
                    if report_type == "BIM 360":
                        issues = extract_bim_issues(input_path)
                    else:
                        issues = extract_acc_issues(input_path)

                    save_issue_pdfs(issues, output_dir, ordered_fields)
                    zip_path = zip_output_folder(output_dir, prefix="Issue_Report")
                    with open(zip_path, "rb") as f:
                        st.download_button(
                            label="📦 Download Split Reports ZIP",
                            data=f,
                            file_name=os.path.basename(zip_path),
                            mime="application/zip"
                        )
                except Exception as e:
                    st.error(f"❌ Error: {e}")
