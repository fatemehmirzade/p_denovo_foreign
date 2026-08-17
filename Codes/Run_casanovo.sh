#!/bin/bash
#SBATCH --job-name=casanovo_gleams
#SBATCH --partition=seven_days
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=100G
#SBATCH --time=168:00:00
#SBATCH --output=casanovo_%j.out
#SBATCH --error=casanovo_%j.err

#job info
echo "=========================================="
echo "Job started at: $(date)"
echo "Running on node: $(hostname)"
echo "Job ID: $SLURM_JOB_ID"
echo "=========================================="

cd /mnt/data/fmirzadehsarcheshme/gleams_unannotated

#conda
eval "$($HOME/miniconda3/bin/conda shell.bash hook)"

#casanovo environment
conda activate casanovo_env

#setup
echo "Casanovo version:"
pip show casanovo | grep Version

echo "GPU info:"
nvidia-smi

#Casanovo on cluster_ident_2_unannotated.mgf
echo "=========================================="
echo "Processing cluster_ident_2_unannotated.mgf..."
echo "Started at: $(date)"
echo "=========================================="

casanovo sequence cluster_ident_2_unannotated.mgf \
    --model casanovo_v5_0_0.ckpt \
    --output_dir .

echo "Finished cluster_ident_2 at: $(date)"

#Casanovo on cluster_ident_n_unannotated.mgf
echo "=========================================="
echo "Processing cluster_ident_n_unannotated.mgf..."
echo "Started at: $(date)"
echo "=========================================="

casanovo sequence cluster_ident_n_unannotated.mgf \
    --model casanovo_v5_0_0.ckpt \
    --output_dir .

echo "=========================================="
echo "Job completed at: $(date)"
echo "=========================================="
