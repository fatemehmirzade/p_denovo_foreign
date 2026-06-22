"""
keeps only rows where len(sequence) >= 10.
"""

import csv
from pathlib import Path

INPUT_DIR  = Path("/Users/fateme/Desktop/test_metadata/Foreign_peptide/Removed_modifications")
OUTPUT_DIR = Path("/Users/fateme/Desktop/test_metadata/Foreign_peptide/Filtered_length (keep>9)")

SEQUENCE_COL = "sequence"
MIN_LENGTH   = 10


def process_file(input_path: Path, output_path: Path) -> tuple[int, int]:
    with open(input_path, encoding="utf-8", newline="") as fh:
        reader     = csv.DictReader(fh, delimiter="\t")
        fieldnames = reader.fieldnames or []
        rows       = list(reader)

    if SEQUENCE_COL not in fieldnames:
        print(f"  [WARN] No '{SEQUENCE_COL}' column in {input_path.name} — skipping.")
        return 0, 0

    kept = [row for row in rows if len(row[SEQUENCE_COL]) >= MIN_LENGTH]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(kept)

    return len(rows), len(kept)


def main():
    if not INPUT_DIR.exists():
        raise FileNotFoundError(f"Input dir not found: {INPUT_DIR}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    tsv_files = sorted(INPUT_DIR.glob("*.tsv"))
    if not tsv_files:
        print(f"No .tsv files found in {INPUT_DIR}")
        return

    print(f"found {len(tsv_files)} tsv files & keeping sequences with length >= {MIN_LENGTH}.\n")

    total_in = total_out = 0
    for tsv_path in tsv_files:
        out_path = OUTPUT_DIR / tsv_path.name
        n_total, n_kept = process_file(tsv_path, out_path)
        pct = (n_kept / n_total * 100) if n_total else 0
        print(f"  {tsv_path.name}: {n_kept}/{n_total} rows kept ({pct:.1f}%)")
        total_in  += n_total
        total_out += n_kept

    print(f"\nDone. {total_out}/{total_in} total rows kept.")
    print(f"Output saved to:\n  {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
