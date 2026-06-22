
import csv
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

FILTERED_TSV_DIR = Path("/Users/fateme/Desktop/test_metadata/Foreign_peptide/Filtered_length (keep>9)")
MGF_DIR          = Path("/Users/fateme/Desktop/test_metadata/Foreign_peptide/Unannotated_mgfs")
OUTPUT_DIR       = Path("/Users/fateme/Desktop/test_metadata/Foreign_peptide/Dataset_tsv")

SPECTRA_REF_COL  = "spectra_ref"


def get_suffix(stem: str):
    parts = stem.rsplit("_", 1)
    return parts[1] if len(parts) == 2 else None


def find_mgf(suffix: str):
    candidate = MGF_DIR / f"cluster_ident_{suffix}_unannotated.mgf"
    if candidate.exists():
        return candidate
    target = f"cluster_ident_{suffix}_unannotated.mgf".lower()
    for f in MGF_DIR.glob("*.mgf"):
        if f.name.lower() == target:
            return f
    return None


def parse_spectrum_index(ref: str):
    """'ms_run[1]:index=8980834' -> 8980834"""
    m = re.search(r":index=(\d+)", ref)
    return int(m.group(1)) if m else None


def extract_msv_id(title: str):
    """'mzspec:MSV000078777:filename mzML:scan:12017' -> 'MSV000078777' returns None if not found"""
    m = re.search(r"(MSV\d+)", title)
    return m.group(1) if m else None


def stream_collect_spectra(mgf_path: Path, needed_indices: set) -> dict:
    """stream through the MGF file line by line"""
    collected   = {}
    remaining   = set(needed_indices)
    current     = []
    current_title = ""
    inside      = False
    idx         = -1
    t0          = time.time()
    REPORT      = 500_000

    total_spectra = len(needed_indices)
    max_idx       = max(needed_indices) if needed_indices else 0

    print(f"    Streaming {mgf_path.name}  ({mgf_path.stat().st_size / 1e9:.1f} GB)")
    print(f"    Need {total_spectra:,} spectra | highest index = {max_idx:,}")

    with open(mgf_path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            stripped = line.rstrip("\n")
            upper    = stripped.strip().upper()

            if upper == "BEGIN IONS":
                current       = [stripped]
                current_title = ""
                inside        = True

            elif upper.startswith("TITLE=") and inside:
                current_title = stripped[6:]   #everything after "TITLE="
                current.append(stripped)

            elif upper == "END IONS" and inside:
                current.append(stripped)
                idx += 1

                if idx in remaining:
                    msv_id = extract_msv_id(current_title)
                    collected[idx] = {
                        "title" : current_title,
                        "msv_id": msv_id if msv_id else "UNKNOWN",
                        "lines" : list(current),
                    }
                    remaining.discard(idx)

                inside = False
                current = []

                if (idx + 1) % REPORT == 0:
                    found   = total_spectra - len(remaining)
                    elapsed = time.time() - t0
                    pct     = (idx + 1) / (max_idx + 1) * 100 if max_idx else 0
                    print(f"    ... {idx+1:,} scanned ({pct:.1f}%)  |  "
                          f"{found}/{total_spectra} matched  |  {elapsed:.0f}s",
                          flush=True)

                #early exit once all needed spectra found
                if not remaining:
                    print(f"    Early exit: all {total_spectra:,} spectra found "
                          f"after scanning {idx+1:,} spectra  ({time.time()-t0:.1f}s)")
                    break

            elif inside:
                current.append(stripped)

    #report any that were not found
    if remaining:
        print(f"    [WARN] {len(remaining)} indices not found in MGF: "
              f"{sorted(remaining)[:10]}{'...' if len(remaining) > 10 else ''}")

    return collected


def process_tsv(tsv_path: Path):
    stem   = tsv_path.stem
    suffix = get_suffix(stem)

    if not suffix:
        print(f"  [SKIP] Cannot determine suffix from '{stem}'")
        return

    mgf_path = find_mgf(suffix)
    if not mgf_path:
        print(f"  [SKIP] No MGF found for suffix '{suffix}'")
        return

    print(f"\n{'='*60}")
    print(f"  Processing : {tsv_path.name}")
    print(f"  MGF source : {mgf_path.name}")
    print(f"{'='*60}")

    with open(tsv_path, encoding="utf-8", newline="") as fh:
        reader     = csv.DictReader(fh, delimiter="\t")
        fieldnames = list(reader.fieldnames or [])
        rows       = list(reader)

    print(f"  TSV rows   : {len(rows):,}")

    #index_to_rows: { spectrum_index: [row, row, ...] }
    index_to_rows = defaultdict(list)
    skipped = 0
    for row in rows:
        idx = parse_spectrum_index(row.get(SPECTRA_REF_COL, ""))
        if idx is not None:
            index_to_rows[idx].append(row)
        else:
            skipped += 1

    needed_indices = set(index_to_rows.keys())
    print(f"  Unique spectrum indices : {len(needed_indices):,}")
    if skipped:
        print(f"  [WARN] {skipped} rows had unparseable spectra_ref — skipped")

    if not needed_indices:
        print("  No valid indices found — skipping file.")
        return

    collected = stream_collect_spectra(mgf_path, needed_indices)

    #group rows and spectra by MSV dataset ID
    #dataset_rows:     { msv_id: [row, ...] }
    #dataset_spectra:  { msv_id: [spectrum_dict, ...] }
    dataset_rows    = defaultdict(list)
    dataset_spectra = defaultdict(list)

    for spec_idx, spec in collected.items():
        msv_id = spec["msv_id"]
        dataset_spectra[msv_id].append(spec)
        for row in index_to_rows[spec_idx]:
            dataset_rows[msv_id].append(row)

    #rows which spectrum was not found in mgf
    found_indices = set(collected.keys())
    missing_indices = needed_indices - found_indices
    if missing_indices:
        for idx in missing_indices:
            for row in index_to_rows[idx]:
                dataset_rows["NOT_FOUND"].append(row)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_msv_ids = sorted(dataset_rows.keys())
    print(f"\n  Found {len(all_msv_ids)} dataset(s): {', '.join(all_msv_ids)}")
    print()

    for msv_id in all_msv_ids:
        msv_rows    = dataset_rows[msv_id]
        msv_spectra = dataset_spectra.get(msv_id, [])

        tsv_out = OUTPUT_DIR / f"{msv_id}.tsv"
        mgf_out = OUTPUT_DIR / f"{msv_id}_matched.mgf"

        #write TSV
        with open(tsv_out, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter="\t")
            writer.writeheader()
            writer.writerows(msv_rows)

        #write matched MGF
        with open(mgf_out, "w", encoding="utf-8") as fh:
            for spec in msv_spectra:
                fh.write("\n".join(spec["lines"]))
                fh.write("\n\n")

        print(f"  [{msv_id}]")
        print(f"    PSM rows : {len(msv_rows):,}")
        print(f"    Spectra  : {len(msv_spectra):,}")
        print(f"    TSV out  : {tsv_out.name}")
        print(f"    MGF out  : {mgf_out.name}")


def main():
    for d, label in [(FILTERED_TSV_DIR, "Input TSV dir"), (MGF_DIR, "MGF dir")]:
        if not d.exists():
            print(f"[ERROR] {label} not found: {d}")
            sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    tsv_files = sorted(FILTERED_TSV_DIR.glob("*.tsv"))
    if not tsv_files:
        print(f"No tsv files found in {FILTERED_TSV_DIR}")
        sys.exit(0)

    print(f"found {len(tsv_files)} TSV file(s) to process.")
    print(f"output directory: {OUTPUT_DIR}\n")

    t_global = time.time()
    for tsv_path in tsv_files:
        process_tsv(tsv_path)

    print(f"\n{'='*60}")
    print(f"all done in {time.time() - t_global:.1f}s")
    print(f"Output: {OUTPUT_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
