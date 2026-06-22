"""
examples:
  LFM[Oxidation]GK          -> LFMGK
  ATM[Oxidation]M[Oxidation]K -> ATMMK
  [Acetyl]-MEALK            -> MEALK
  LPC[Carbamidomethyl]GR    -> LPCGR
"""

import csv
import re
from pathlib import Path

INPUT_DIR  = Path("/Users/fateme/Desktop/test_metadata/Foreign_peptide/Score_filtered_tsv")
OUTPUT_DIR = Path("/Users/fateme/Desktop/test_metadata/Foreign_peptide/Removed_modifications")

SEQUENCE_COL = "sequence"


def clean_sequence(seq: str) -> str:
    """remove [modifications] and leftover hyphens from a peptide sequence"""
    seq = re.sub(r"\[.*?\]", "", seq)   
    seq = seq.strip("-")                 
    return seq


def process_file(input_path: Path, output_path: Path) -> tuple[int, int]:
    with open(input_path, encoding="utf-8", newline="") as fh:
        reader     = csv.DictReader(fh, delimiter="\t")
        fieldnames = reader.fieldnames or []
        rows       = list(reader)

    if SEQUENCE_COL not in fieldnames:
        print(f"  [WARN] No '{SEQUENCE_COL}' column in {input_path.name} — skipping.")
        return 0, 0

    modified = 0
    for row in rows:
        original = row[SEQUENCE_COL]
        cleaned  = clean_sequence(original)
        if cleaned != original:
            row[SEQUENCE_COL] = cleaned
            modified += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    return len(rows), modified


def main():
    if not INPUT_DIR.exists():
        raise FileNotFoundError(f"Input dir not found: {INPUT_DIR}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    tsv_files = sorted(INPUT_DIR.glob("*.tsv"))
    if not tsv_files:
        print(f"No .tsv files found in {INPUT_DIR}")
        return

    print(f"Found {len(tsv_files)} TSV file(s).\n")

    for tsv_path in tsv_files:
        out_path = OUTPUT_DIR / tsv_path.name
        total, modified = process_file(tsv_path, out_path)
        print(f"  {tsv_path.name}: {modified}/{total} sequences cleaned")

    print(f"\nDone. Output saved to:\n  {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
