import pandas as pd
from pathlib import Path

DIR_2   = Path("/Users/fateme/Desktop/test_metadata/Foreign_peptide/Dataset_tsv/cluster_ident_2_unannotated_data")
DIR_N   = Path("/Users/fateme/Desktop/test_metadata/Foreign_peptide/Dataset_tsv/cluster_ident_n_unannotated_data")
OUT_DIR = Path("/Users/fateme/Desktop/test_metadata/Foreign_peptide/Dataset_tsv/Merged_file_datasets")

OUT_DIR.mkdir(parents=True, exist_ok=True)

#collect all unique TSV filenames across both folders
all_names = set()
for folder in [DIR_2, DIR_N]:
    if folder.exists():
        all_names.update(f.name for f in folder.glob("*.tsv"))
    else:
        print(f"[WARN] Folder not found: {folder}")

if not all_names:
    print("No TSV files found in either folder.")
    exit()

print(f"Found {len(all_names)} unique dataset file(s) across both folders.\n")

only_in_2   = 0
only_in_n   = 0
in_both     = 0
total_rows  = 0

for name in sorted(all_names):
    path_2 = DIR_2 / name
    path_n = DIR_N / name

    dfs = []
    sources = []

    if path_2.exists():
        df2 = pd.read_csv(path_2, sep="\t")
        dfs.append(df2)
        sources.append("_2")

    if path_n.exists():
        dfn = pd.read_csv(path_n, sep="\t")
        dfs.append(dfn)
        sources.append("_n")

    #track source stats
    if len(sources) == 2:
        in_both += 1
    elif sources == ["_2"]:
        only_in_2 += 1
    else:
        only_in_n += 1

    merged = pd.concat(dfs, ignore_index=True)
    out_path = OUT_DIR / name
    merged.to_csv(out_path, sep="\t", index=False)

    total_rows += len(merged)
    row_counts = " + ".join(str(len(d)) for d in dfs)
    print(f"  {name}: {row_counts} = {len(merged)} rows  (from: {', '.join(sources)})")

print(f"  Done.")
print(f"  Total datasets merged : {len(all_names)}")
print(f"  In both _2 and _n     : {in_both}")
print(f"  Only in _2            : {only_in_2}")
print(f"  Only in _n            : {only_in_n}")
print(f"  Total rows across all : {total_rows:,}")
print(f"  Output saved to       : {OUT_DIR}")
