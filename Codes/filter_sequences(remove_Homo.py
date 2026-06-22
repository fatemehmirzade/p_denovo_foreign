import os
import glob

tsv_dir = "/Users/fateme/Desktop/test_metadata/Foreign_peptide/only_sequence_tsv"
txt_dir = "/Users/fateme/Desktop/test_metadata/Foreign_peptide/Human_match"
out_dir = "/Users/fateme/Desktop/test_metadata/Foreign_peptide/Filtered_tsv_Human"

os.makedirs(out_dir, exist_ok=True)

txt_files = {}
for f in glob.glob(os.path.join(txt_dir, "*_human_matches.txt")):
    msv_id = os.path.basename(f).replace("_human_matches.txt", "")
    txt_files[msv_id] = f

for tsv_path in glob.glob(os.path.join(tsv_dir, "*.tsv")):
    msv_id = os.path.basename(tsv_path).replace(".tsv", "")

    if msv_id not in txt_files:
        print(f"No human_matches file for {msv_id}, copying TSV as-is.")
        with open(tsv_path, "r") as fin, open(os.path.join(out_dir, f"{msv_id}.tsv"), "w") as fout:
            fout.write(fin.read())
        continue

    with open(txt_files[msv_id], "r") as f:
        seqs_to_remove = set(line.strip() for line in f if line.strip())

    with open(tsv_path, "r") as fin:
        lines = fin.readlines()

    filtered = []
    removed_count = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        seq = stripped.split("\t")[0]
        if seq in seqs_to_remove:
            removed_count += 1
        else:
            filtered.append(line)

    out_path = os.path.join(out_dir, f"{msv_id}.tsv")
    with open(out_path, "w") as fout:
        fout.writelines(filtered)

    print(f"{msv_id}: {len(lines)} -> {len(filtered)} sequences ({removed_count} removed)")

print("\nDone! Filtered files saved to:", out_dir)
