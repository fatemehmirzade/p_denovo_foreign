#!/bin/bash
#SBATCH --job-name=unipept_taxonomy
#SBATCH --partition=seven_days
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=48:00:00
#SBATCH --output=/mnt/data/fmirzadehsarcheshme/Unipept_taxonomy_19_jun/logs/unipept_tax_%j.log
#SBATCH --error=/mnt/data/fmirzadehsarcheshme/Unipept_taxonomy_19_jun/logs/unipept_tax_%j.err
#SBATCH --constraint=asimov

set -uo pipefail

eval "$($HOME/miniconda3/bin/conda shell.bash hook)"
conda activate unipept_env

if ! command -v unipept &>/dev/null; then
    echo "ERROR: unipept command not found. Is the environment set up?"
    exit 1
fi

BASE_DIR="/mnt/data/fmirzadehsarcheshme/Unipept_taxonomy_19_jun"

INPUT_DIRS=(
    "${BASE_DIR}/moira_test"
    "${BASE_DIR}/only_sequence_tsv"
)
OUTPUT_DIRS=(
    "${BASE_DIR}/Unipept_results_19_june/moira_test"
    "${BASE_DIR}/Unipept_results_19_june/only_sequence_tsv"
)

MAX_RETRIES=3

total_processed=0
total_success=0
total_failed=0
total_skipped=0

echo "=========================================="
echo "  UNIPEPT TAXONOMY ANALYSIS (pept2lca)"
echo "=========================================="
echo "Started at : $(date)"
echo "Hostname   : $(hostname)"
echo "Node.js    : $(node --version 2>&1)"
echo "Unipept    : $(unipept --version 2>&1)"
echo ""

for folder_idx in "${!INPUT_DIRS[@]}"; do
    input_dir="${INPUT_DIRS[$folder_idx]}"
    output_dir="${OUTPUT_DIRS[$folder_idx]}"
    folder_name=$(basename "$input_dir")

    echo ""
    echo "=========================================="
    echo "  Folder: ${folder_name}"
    echo "=========================================="

    #check input folder exists and has tsv files
    if [ ! -d "$input_dir" ]; then
        echo "  ERROR: Input directory does not exist: ${input_dir}"
        echo "  Skipping this folder."
        continue
    fi

    file_count=$(find "$input_dir" -maxdepth 1 -name '*.tsv' -type f | wc -l)
    if [ "$file_count" -eq 0 ]; then
        echo "  WARNING: No .tsv files found in ${input_dir}"
        echo "  Skipping this folder."
        continue
    fi

    echo "  Found ${file_count} TSV file(s)"
    echo ""

    mkdir -p "$output_dir"

    file_num=0

    for tsv_file in "$input_dir"/*.tsv; do
        [ -f "$tsv_file" ] || continue

        dataset_name=$(basename "$tsv_file" .tsv)
        file_num=$((file_num + 1))
        total_processed=$((total_processed + 1))

        echo "  [${file_num}/${file_count}] ${dataset_name}"
        echo "    Started: $(date '+%Y-%m-%d %H:%M:%S')"

        #Unipept outputs csv
        output_file="${output_dir}/${dataset_name}_taxonomy.csv"

        #skip if output already exists and is non empty
        if [ -f "$output_file" ] && [ -s "$output_file" ]; then
            result_lines=$(($(wc -l < "$output_file") - 1))
            if [ "$result_lines" -gt 0 ]; then
                echo "    SKIP: Output already exists (${result_lines} results)"
                total_skipped=$((total_skipped + 1))
                total_success=$((total_success + 1))
                continue
            fi
        fi

        #count peptides in input
        peptide_count=$(wc -l < "$tsv_file")
        echo "    Peptides: ${peptide_count}"

        if [ "$peptide_count" -eq 0 ]; then
            echo "    WARNING: Empty input, skipping"
            total_failed=$((total_failed + 1))
            continue
        fi

        #run unipept pept2lca with retries
        run_ok=false
        for ((attempt = 1; attempt <= MAX_RETRIES; attempt++)); do
            echo "    Attempt ${attempt}/${MAX_RETRIES}..."

            if unipept pept2lca \
                --input "$tsv_file" \
                --output "$output_file" \
                --equate \
                --all 2>&1; then

                #verify output was created and has data
                if [ -f "$output_file" ] && [ -s "$output_file" ]; then
                    result_count=$(($(wc -l < "$output_file") - 1))
                    if [ "$result_count" -gt 0 ]; then
                        echo "    SUCCESS: ${result_count} taxonomic assignments from ${peptide_count} peptides"
                        run_ok=true
                        break
                    else
                        echo "    WARNING: Output file has header only, no data"
                        rm -f "$output_file"
                    fi
                else
                    echo "    WARNING: Output file missing or empty"
                    rm -f "$output_file"
                fi
            else
                echo "    WARNING: unipept command returned an error"
                rm -f "$output_file"
            fi

            if [ "$attempt" -lt "$MAX_RETRIES" ]; then
                wait_time=$((attempt * 15))
                echo "    Waiting ${wait_time}s before retry..."
                sleep "$wait_time"
            fi
        done

        if $run_ok; then
            total_success=$((total_success + 1))
        else
            echo "    FAILED after ${MAX_RETRIES} attempts"
            total_failed=$((total_failed + 1))
        fi

        echo "    Finished: $(date '+%Y-%m-%d %H:%M:%S')"

        #pause
        sleep 5
    done
done

echo ""
echo "=========================================="
echo "  SUMMARY"
echo "=========================================="
echo "Completed at : $(date)"
echo ""
echo "  Total files : ${total_processed}"
echo "  Successful  : ${total_success} (including ${total_skipped} skipped)"
echo "  Failed      : ${total_failed}"
echo ""

for folder_idx in "${!OUTPUT_DIRS[@]}"; do
    output_dir="${OUTPUT_DIRS[$folder_idx]}"
    folder_name=$(basename "${INPUT_DIRS[$folder_idx]}")
    out_count=$(find "$output_dir" -name '*_taxonomy.csv' -type f 2>/dev/null | wc -l)
    echo "  ${folder_name}: ${out_count} result file(s)"
    if [ "$out_count" -gt 0 ]; then
        du -sh "$output_dir" | awk '{print "    Size: "$1}'
    fi
done

echo ""
echo "=========================================="
