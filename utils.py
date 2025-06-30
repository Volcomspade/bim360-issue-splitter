
def detect_report_type(file_path):
    if "BIM" in file_path:
        return "BIM 360"
    elif "ACC" in file_path:
        return "ACC Build"
    return "Unknown"

def extract_bim360_issues(input_path):
    return ["bim_issue_001.pdf"]

def extract_acc_build_issues(input_path):
    return ["acc_issue_001.pdf"]
