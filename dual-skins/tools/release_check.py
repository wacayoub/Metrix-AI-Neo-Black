"""Single local verification cycle. Never communicates with the receiver."""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args, log=None):
    result = subprocess.run([sys.executable, "-X", "utf8", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    output = result.stdout + result.stderr
    if log:
        log.write_text(output, encoding="utf-8")
    if result.returncode:
        print(output)
        raise SystemExit(result.returncode)
    if log is None:
        print(output.strip())
    return output


def hashes():
    manifest = json.loads((ROOT / "dist/manifest.json").read_text(encoding="utf-8"))
    return {item["file"]: hashlib.sha256((ROOT / "dist" / item["file"]).read_bytes()).hexdigest() for item in manifest["packages"] + [manifest["source"]]}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    run("tools/fetch_pinned_sources.py", "--check")
    run("tools/generate_skins.py")
    run("tools/render_previews.py")
    tests = run("-m", "unittest", "discover", "-s", "tests", "-v", log=reports / "tests.txt")
    print(tests[tests.rfind("----------------------------------------------------------------------"):].strip())
    run("tools/validate.py")
    shutil.copyfile(ROOT / "build/static-report.json", reports / "static-report.json")
    run("tools/build_ipk.py")
    run("tools/check_ipk.py")
    shutil.copyfile(ROOT / "build/ipk-report.json", reports / "ipk-report.json")
    # The source bundle now includes the reports. Compare two builds of that state.
    run("tools/build_ipk.py")
    first = hashes()
    run("tools/build_ipk.py")
    assert hashes() == first, "Build is not reproducible for these fixed inputs"
    run("tools/check_ipk.py")
    approval = json.loads((reports / "visual-validation.json").read_text(encoding="utf-8"))
    report = {"result": "PASS", "receiver_status": "NOT_INSTALLED", "reproducible_packages_and_source": True, "artifacts": first, "hardware_tests": "NOT_PERFORMED", "user_visual_approval": approval["overall_status"], "approved_reference_comparison": "USER_PREVIEW_APPROVAL_HARDWARE_NOT_COMPARED"}
    (ROOT / "dist/BUILD_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Build reproducible confirmé : 4 IPK et ZIP sources. NOT_INSTALLED.")


if __name__ == "__main__":
    main()
