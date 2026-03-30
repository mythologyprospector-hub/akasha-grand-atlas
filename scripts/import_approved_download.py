import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

DOWNLOADS = pathlib.Path("/sdcard/Download")
TARGET = REPORTS / "approved-candidates.csv"


def find_latest_approved_file():
    matches = sorted(
        DOWNLOADS.glob("approved-candidates*.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return matches[0] if matches else None


def main():
    src = find_latest_approved_file()

    if not src:
        print("No approved-candidates CSV found in /sdcard/Download")
        sys.exit(1)

    if TARGET.exists():
        TARGET.unlink()

    shutil.move(src, TARGET)

    print(f"Moved: {src}")
    print(f"Into: {TARGET}")


if __name__ == "__main__":
    main()