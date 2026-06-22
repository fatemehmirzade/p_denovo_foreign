import csv
from pathlib import Path

INPUT_DIR  = Path("/Users/fateme/Desktop/test_metadata/Foreign_peptide/Casanovo_tsv")
OUTPUT_DIR = Path("/Users/fateme/Desktop/test_metadata/Foreign_peptide/Score_filtered_tsv")

SCORE_COL  = "search_engine_score[1]"


def score_passes(value: str) -> bool:
    """return true if the score meets the filter criteria"""
    try:
        score = float(value)
    except (ValueError, TypeError):
        return False  # skip nulls / non-numeric values

    return score >= 0.6 or (-0.4 <= score <= 0.0)


def filter_file(input_path: Path, output_path: Path) -> tuple[int, int]:
    with open(input_path, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")

        if SCORE_COL not in (reader.fieldnames or []):
            print(f"  [WARN] Column '{SCORE_COL}' not found in {input_path.name} — skipping.")
            return 0, 0

        rows = list(reader)
        kept = [r for r in rows if score_passes(r[SCORE_COL])]

    if kept:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=reader.fieldnames, delimiter="\t")
            writer.writeheader()
            writer.writerows(kept)
    else:
        print(f"  [INFO] No rows passed filter in {input_path.name} — output file not created.")

    return len(rows), len(kept)


def main():
    if not INPUT_DIR.exists():
        raise FileNotFoundError(f"Input directory not found: {INPUT_DIR}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    tsv_files = sorted(INPUT_DIR.glob("*.tsv"))

    if not tsv_files:
        print(f"No .tsv files found in {INPUT_DIR}")
        return

    print(f"Filter: score >= 0.6  OR  -0.4 <= score <= 0.0")
    print(f"Found {len(tsv_files)} TSV file(s) in:\n  {INPUT_DIR}\n")

    total_in = total_out = 0

    for tsv_path in tsv_files:
        output_path = OUTPUT_DIR / tsv_path.name
        n_total, n_kept = filter_file(tsv_path, output_path)
        pct = (n_kept / n_total * 100) if n_total else 0
        print(f"  {tsv_path.name}: {n_kept}/{n_total} rows kept ({pct:.1f}%)")
        total_in  += n_total
        total_out += n_kept

    print(f"\nDone. {total_out}/{total_in} total rows kept across {len(tsv_files)} file(s)")
    print(f"Output saved to:\n  {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
