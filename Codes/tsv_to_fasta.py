import csv
from pathlib import Path

INPUT_DIR  = Path("/Users/fateme/Desktop/test_metadata/Foreign_peptide/only_sequence_tsv")
OUTPUT_DIR = Path("/Users/fateme/Desktop/test_metadata/Foreign_peptide/only_sequence_fasta")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

tsv_files = sorted(INPUT_DIR.glob("*.tsv"))
if not tsv_files:
    print(f"No .tsv files found in {INPUT_DIR}")
    exit()

print(f"Found {len(tsv_files)} TSV file(s).\n")

total_seqs = 0

for tsv_path in tsv_files:
    dataset_id = tsv_path.stem 

    #read sequences
    sequences = []
    with open(tsv_path, encoding="utf-8-sig", newline="") as fh:
        first_line = fh.readline().strip()
        #check if first line is a header
        if first_line.lower() == "sequence":
            for line in fh:
                seq = line.strip()
                if seq:
                    sequences.append(seq)
        else:
           
            if first_line:
                sequences.append(first_line)
            for line in fh:
                seq = line.strip()
                if seq:
                    sequences.append(seq)

    if not sequences:
        print(f"  [WARN] No sequences found in {tsv_path.name} — skipping.")
        continue

    #write FASTA
    fasta_out = OUTPUT_DIR / f"{dataset_id}.fasta"
    with open(fasta_out, "w", encoding="utf-8") as fh:
        for i, seq in enumerate(sequences, 1):
            fh.write(f">{dataset_id}|pep_{i}\n{seq}\n")

    total_seqs += len(sequences)
    print(f"  {dataset_id}.fasta : {len(sequences):,} sequences")

print(f"\nDone.")
print(f"  Total sequences : {total_seqs:,}")
print(f"  Output saved to : {OUTPUT_DIR}")
