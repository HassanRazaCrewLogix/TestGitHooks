import os
import sys
import xml.etree.ElementTree as ET
import subprocess
import shutil

PRODUCT_FLAVOR = "GeneralStaging"
PROJECT_ROOT = None
SDK_PATH = None

def main():
    if len(sys.argv) < 2 or not os.path.exists(sys.argv[1]):
        print("There is missing argument.")
        sys.exit(1)
    PROJECT_ROOT = sys.argv[1]
    # if "ANDROID_HOME" in os.environ:
    #     SDK_PATH = os.environ["ANDROID_HOME"]
    # elif "ANDROID_SDK_ROOT" in os.environ:
    #     SDK_PATH = os.environ["ANDROID_SDK_ROOT"]
    # else:
    #     print("Android SDK path not found.\nSet the SDK Path to ANDROID_HOME or ANDROID_SDK_ROOT environtment variable.")
    #     sys.exit(1)

    modules = {}

    for line in sys.stdin:
        line = line.strip()
        if line != '' and os.path.exists(line):
            module = line[len(PROJECT_ROOT):]
            while module[0] == os.sep:
                module = module[1:]
            folders = module.split(os.sep)
            if len(folders) == 1 or not os.path.exists(PROJECT_ROOT + "/" + folders[0] + "/build.gradle"):
                continue
            modules[folders[0]] = 1


    lint_results_dir = PROJECT_ROOT + "/build/lint"
    if os.path.exists(lint_results_dir):
        shutil.rmtree(lint_results_dir)
    os.makedirs(lint_results_dir)

    issues = {}
    for module in modules:
        issuesModule = issues[module] = {}
        gradlew = PROJECT_ROOT + "/gradlew"
        report_dir = PROJECT_ROOT + "/" + module + "/build/reports"
        report_filename = "lint-results" + (("-" + PRODUCT_FLAVOR[0].lower() + PRODUCT_FLAVOR[1:] ) if PRODUCT_FLAVOR is not None else "")
        report_xml = report_dir + "/" + report_filename + ".xml"
        report_html = report_dir + "/" + report_filename + ".html"
        # if os.path.exists(report):
        #     os.remove(report)
        cmd = gradlew + " " + module + ":lint" + PRODUCT_FLAVOR
        print(cmd)
        process = subprocess.Popen([gradlew, module + ":lint" + PRODUCT_FLAVOR])
        process.wait()
        if process.returncode != 0:
            print("Error: Lint failed on module " + module)
            sys.exit(1)
        
        print("Parsing: " + report_xml)
        if not os.path.exists(report_xml):
            print("Error: Lint result not found on module " + module)
            sys.exit(1)
        xml = ET.parse(report_xml)
        root = xml.getroot()
        for issue in root:
            severity = issue.attrib['severity']
            if severity not in issuesModule:
                issuesModule[severity] = 1
            else:
                issuesModule[severity] += 1
        shutil.copyfile(report_xml, lint_results_dir + "/" + module + "-" + report_filename + ".xml")
        shutil.copyfile(report_html, lint_results_dir + "/" + module + "-" + report_filename + ".html")

    print("Lint Result:")
    if len(issues) == 0:
        print("No changed module.")
    else:
        errors = 0
        fatals = 0
        for module in issues:
            issuesModule = issues[module]
            print(module)
            if len(issuesModule) != 0:
                print("Found issue(s):")
                issueStr = ""
                for sev in issuesModule:
                    issueStr += str(issuesModule[sev]) + " " + sev + "(s); "
                    if sev == "Error":
                        errors += issuesModule[sev]
                    elif sev == "Fatal":
                        fatals += issuesModule[sev]
                print(issueStr)
            else:
                print("No issue found.")
            print()
        
        if errors != 0 or fatals != 0:
            print("Error: Lint failed because there are some error or fatal issues found.")
            sys.exit(1)


if __name__ == "__main__":
    main()