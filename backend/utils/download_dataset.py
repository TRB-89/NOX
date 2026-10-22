"""
NØX - Dataset Download Utility
Downloads the official UNSW-NB15 training and testing CSV sets into backend/data/raw/
"""

import os
import sys
import urllib.request
from pathlib import Path

# Primary mirror hosted from repository containing exact official UNSW-NB15 benchmark splits
DATASET_URLS = {
    "UNSW_NB15_training-set.csv": [
        "https://raw.githubusercontent.com/Nir-J/ML-Projects/master/UNSW-Network_Packet_Classification/UNSW_NB15_training-set.csv",
        "https://media.githubusercontent.com/media/vincent-123/NIDS-UNSW-NB15/master/UNSW_NB15_training-set.csv",
    ],
    "UNSW_NB15_testing-set.csv": [
        "https://raw.githubusercontent.com/Nir-J/ML-Projects/master/UNSW-Network_Packet_Classification/UNSW_NB15_testing-set.csv",
        "https://media.githubusercontent.com/media/vincent-123/NIDS-UNSW-NB15/master/UNSW_NB15_testing-set.csv",
    ],
}


def download_file(url_list: list[str], destination_path: Path) -> bool:
    """Download a file with fallback URLs and progress logging."""
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = destination_path.with_suffix(".tmp")

    for url in url_list:
        try:
            print(f"[*] Attempting download from: {url}")
            headers = {"User-Agent": "NOX-NIDS/1.0 (Cybersecurity ML Research Pipeline)"}
            request = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(request, timeout=60) as response, open(temp_path, "wb") as out_file:
                total_length = response.headers.get("content-length")
                total_bytes = int(total_length) if total_length else None
                downloaded = 0
                chunk_size = 1024 * 1024  # 1 MB chunks

                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    if total_bytes:
                        pct = (downloaded / total_bytes) * 100
                        mb = downloaded / (1024 * 1024)
                        total_mb = total_bytes / (1024 * 1024)
                        print(f"\r    -> Progress: {mb:.1f} MB / {total_mb:.1f} MB ({pct:.1f}%)", end="", flush=True)
                    else:
                        mb = downloaded / (1024 * 1024)
                        print(f"\r    -> Downloaded: {mb:.1f} MB", end="", flush=True)

            print()
            # Atomically replace destination
            if temp_path.exists():
                if destination_path.exists():
                    destination_path.unlink()
                temp_path.rename(destination_path)
            print(f"[+] Successfully saved to: {destination_path} ({destination_path.stat().st_size / (1024*1024):.2f} MB)")
            return True
        except Exception as e:
            print(f"\n[!] Failed to download from {url}: {e}")
            if temp_path.exists():
                temp_path.unlink()

    return False


def ensure_raw_datasets(raw_dir: Path | str | None = None) -> tuple[bool, str]:
    """
    Checks if raw UNSW-NB15 files exist; if not, attempts automatic download.
    Returns (success_status, status_message).
    """
    if raw_dir is None:
        raw_dir = Path(__file__).resolve().parent.parent / "data" / "raw"
    else:
        raw_dir = Path(raw_dir)

    raw_dir.mkdir(parents=True, exist_ok=True)
    all_present = True
    missing_files = []

    for filename in DATASET_URLS:
        target_path = raw_dir / filename
        if not target_path.exists() or target_path.stat().st_size < 1000:
            missing_files.append(filename)
            all_present = False

    if not missing_files:
        return True, "All required UNSW-NB15 raw CSV files are present."

    print(f"[!] The following raw dataset files are missing in '{raw_dir}':")
    for f in missing_files:
        print(f"    - {f}")

    print("[*] Initiating automatic download of official UNSW-NB15 dataset splits...")
    download_success = True
    for filename in missing_files:
        success = download_file(DATASET_URLS[filename], raw_dir / filename)
        if not success:
            download_success = False

    if download_success:
        return True, "All raw datasets were successfully downloaded and verified."
    else:
        manual_msg = (
            "\n" + "=" * 70 + "\n"
            "MANUAL DOWNLOAD INSTRUCTIONS:\n"
            "1. Visit the official UNSW-NB15 dataset portal:\n"
            "   https://research.unsw.edu.au/projects/unsw-nb15-dataset\n"
            "   or Kaggle: https://www.kaggle.com/datasets/mrwellsdavid/unsw-nb15\n"
            "2. Download the following two files:\n"
            "   - UNSW_NB15_training-set.csv\n"
            "   - UNSW_NB15_testing-set.csv\n"
            f"3. Place both CSV files directly into the directory:\n"
            f"   {raw_dir.resolve()}\n"
            + "=" * 70
        )
        return False, manual_msg


if __name__ == "__main__":
    success, message = ensure_raw_datasets()
    print(message)
    sys.exit(0 if success else 1)
