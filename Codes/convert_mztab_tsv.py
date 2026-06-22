import os
import csv
from pathlib import Path


INPUT_DIR  = Path("/Users/fateme/Desktop/test_metadata/Foreign_peptide/Casanovo_outputs")
OUTPUT_DIR = Path("/Users/fateme/Desktop/test_metadata/Foreign_peptide/Casanovo_tsv")


def parse_mztab(filepath: Path) -> tuple[list[str], list[dict]]:
    """parse an mzTab file and return (headers, rows) for the PSM section"""
    psm_headers: list[str] = []
    psm_rows:    list[dict] = []

    with open(filepath, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")

            if not line.strip():
                continue

            prefix = line.split("\t", 1)[0].strip()

            if prefix == "PSH":
                parts = line.split("\t")
                psm_headers = parts[1:]          #drop the PSH tag

            elif prefix == "PSM":
                parts = line.split("\t")
                values = parts[1:]               #drop the PSM tag

                if psm_headers:
                    row = dict(zip(
                        psm_headers,
                        values + [""] * max(0, len(psm_headers) - len(values))
                    ))
                    psm_rows.append(row)

    return psm_headers, psm_rows


def convert_file(input_path: Path, output_path: Path) -> int:
    """convert a single mzTab file to TSV, returns number of PSM rows written"""
    headers, rows = parse_mztab(input_path)

    if not headers:
        print(f"  [WARN] No PSH/PSM section found in {input_path.name} — skipping.")
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=headers, delimiter="\t",
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


def main():
    if not INPUT_DIR.exists():
        raise FileNotFoundError(f"Input directory not found: {INPUT_DIR}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    mztab_files = sorted(INPUT_DIR.glob("*.mztab")) + sorted(INPUT_DIR.glob("*.mzTab"))

    if not mztab_files:
        print(f"No .mztab / .mzTab files found in {INPUT_DIR}")
        return

    print(f"Found {len(mztab_files)} mzTab file(s) in:\n  {INPUT_DIR}\n")

    total_rows = 0
    for mztab_path in mztab_files:
        tsv_name   = mztab_path.stem + ".tsv"
        output_path = OUTPUT_DIR / tsv_name

        print(f"  Converting: {mztab_path.name}  ->  {tsv_name}")
        n = convert_file(mztab_path, output_path)
        print(f"             {n} PSM rows written.")
        total_rows += n

    print(f"\nDone. {len(mztab_files)} file(s) converted, {total_rows} total PSM rows.")
    print(f"Output saved to:\n  {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
