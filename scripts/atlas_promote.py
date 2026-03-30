import subprocess
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

DOWNLOADS = pathlib.Path("/sdcard/Download")
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

APPROVED = REPORTS / "approved-candidates.csv"


def find_latest_download():
    files = sorted(
        DOWNLOADS.glob("approved-candidates*.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    return files[0] if files else None


def import_file():
    src = find_latest_download()

    if not src:
        print("No approved-candidates file found in /sdcard/Download")
        sys.exit(1)

    if APPROVED.exists():
        APPROVED.unlink()

    shutil.move(src, APPROVED)

    print(f"Moved approval file → {APPROVED}")


def run(cmd):
    print(f"\nRunning: {cmd}")
    subprocess.run(cmd, shell=True, check=True)


def main():

    print("\n=== Atlas Promote Pipeline ===\n")

    import_file()

    run("python scripts/promote_candidates.py --approved-file reports/approved-candidates.csv --write")

    run("python scripts/build_atlas.py")

    print("\nAtlas updated successfully.\n")

    print("Open:")
    print(f"{ROOT}/site/index.html\n")


if __name__ == "__main__":
    main()