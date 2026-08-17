import csv
from pathlib import Path

INPUT_DIR    = Path("/Users/fateme/Desktop/test_metadata/Foreign_peptide/Merged_file_datasets")
TSV_OUT_DIR  = Path("/Users/fateme/Desktop/test_metadata/Foreign_peptide/only_sequence_tsv")
FASTA_OUT_DIR = Path("/Users/fateme/Desktop/test_metadata/Foreign_peptide/only_sequence_fasta")

TSV_OUT_DIR.mkdir(parents=True, exist_ok=True)
FASTA_OUT_DIR.mkdir(parents=True, exist_ok=True)

tsv_files = sorted(INPUT_DIR.glob("*.tsv"))
if not tsv_files:
    print(f"No .tsv files found in {INPUT_DIR}")
    exit()

print(f"Found {len(tsv_files)} TSV file(s).\n")

total_seqs = 0

for tsv_path in tsv_files:
    dataset_id = tsv_path.stem   

    #read sequences
    with open(tsv_path, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        if "sequence" not in (reader.fieldnames or []):
            print(f"  [WARN] No 'sequence' column in {tsv_path.name} — skipping.")
            continue
        sequences = [row["sequence"] for row in reader if row["sequence"].strip()]

    # write sequence-only TSV
    tsv_out = TSV_OUT_DIR / tsv_path.name
    with open(tsv_out, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerow(["sequence"])
        for seq in sequences:
            writer.writerow([seq])

    #write FASTA
    fasta_out = FASTA_OUT_DIR / f"{dataset_id}.fasta"
    with open(fasta_out, "w", encoding="utf-8") as fh:
        for i, seq in enumerate(sequences, 1):
            fh.write(f">{dataset_id}_{i}\n{seq}\n")

    total_seqs += len(sequences)
    print(f"  {dataset_id}: {len(sequences):,} sequences → TSV + FASTA")

print(f"\nDone.")
print(f"  Total sequences : {total_seqs:,}")
print(f"  TSV output      : {TSV_OUT_DIR}")
print(f"  FASTA output    : {FASTA_OUT_DIR}")
