import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 5)

file_paths = [
    '/Users/fateme/Desktop/test_metadata/Foreign_peptide/Filtered_length (keep>9)/cluster_ident_2.tsv',
    '/Users/fateme/Desktop/test_metadata/Foreign_peptide/Filtered_length (keep>9)/cluster_ident_n.tsv',
]

output_file = open('terminus_analysis_results.txt', 'w')

def print_and_save(text=""):
    """Print to console AND save to file"""
    print(text)
    output_file.write(text + '\n')

print_and_save("Loading Casanovo predictions...")
all_sequences = []

#load both files and combine
for file_path in file_paths:
    try:
        df = pd.read_csv(file_path, sep='\t')
        all_sequences.extend(df['sequence'].tolist())
        print_and_save(f"- Loaded {len(df):,} peptides from {Path(file_path).name}")
    except FileNotFoundError:
        print_and_save(f"⚠ File not found: {file_path}")
    except Exception as e:
        print_and_save(f"⚠ Error: {e}")

total = len(all_sequences)
print_and_save(f"\nTotal peptides: {total:,}\n")

#extract N-terminus (first AA) and C-terminus (last AA)
n_termini = [seq[0] for seq in all_sequences]
c_termini = [seq[-1] for seq in all_sequences]

#count frequencies
from collections import Counter
n_term_counts = Counter(n_termini)
c_term_counts = Counter(c_termini)

#sort by frequency
n_term_counts = dict(sorted(n_term_counts.items(), key=lambda x: x[1], reverse=True))
c_term_counts = dict(sorted(c_term_counts.items(), key=lambda x: x[1], reverse=True))

#print statistics
print_and_save("=" * 60)
print_and_save("C-TERMINAL AMINO ACIDS (END OF PEPTIDES)")
print_and_save("=" * 60)
print_and_save(f"{'AA':<5} {'Count':<10} {'%':<10}")
print_and_save("-" * 25)
for aa, count in c_term_counts.items():
    pct = (count / total) * 100
    print_and_save(f"{aa:<5} {count:<10,} {pct:>6.2f}%")

print_and_save(f"\nK or R at C-terminus: {(c_term_counts.get('K', 0) + c_term_counts.get('R', 0)) / total * 100:.2f}%")

print_and_save("\n" + "=" * 60)
print_and_save("N-TERMINAL AMINO ACIDS (START OF PEPTIDES)")
print_and_save("=" * 60)
print_and_save(f"{'AA':<5} {'Count':<10} {'%':<10}")
print_and_save("-" * 25)
for aa, count in n_term_counts.items():
    pct = (count / total) * 100
    print_and_save(f"{aa:<5} {count:<10,} {pct:>6.2f}%")

#visualizations
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

#C-terminus plot
ax1 = axes[0]
aas_c = list(c_term_counts.keys())
counts_c = list(c_term_counts.values())
colors_c = ['#63c5b5' if aa in ['K', 'R'] else '#6da7de' for aa in aas_c]
ax1.bar(aas_c, counts_c, color=colors_c, alpha=0.8, edgecolor='black', linewidth=1.5)
ax1.set_xlabel('Amino Acid', fontsize=12, fontweight='bold')
ax1.set_ylabel('Count', fontsize=12, fontweight='bold')
ax1.set_title('C-Terminal Amino Acids (End of Peptides)\nTeal = Expected for Trypsin (K/R)', 
              fontsize=13, fontweight='bold')
ax1.grid(axis='y', alpha=0.3)

max_count = max(counts_c)
if max_count > 100000:
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))

#N-terminus plot
ax2 = axes[1]
aas_n = list(n_term_counts.keys())
counts_n = list(n_term_counts.values())
ax2.bar(aas_n, counts_n, color='#eb861e', alpha=0.8, edgecolor='black', linewidth=1.5)
ax2.set_xlabel('Amino Acid', fontsize=12, fontweight='bold')
ax2.set_ylabel('Count', fontsize=12, fontweight='bold')
ax2.set_title('N-Terminal Amino Acids (Start of Peptides)', fontsize=13, fontweight='bold')
ax2.grid(axis='y', alpha=0.3)

max_count = max(counts_n)
if max_count > 100000:
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))

plt.tight_layout()
plt.savefig('terminus_exploration.png', dpi=300, bbox_inches='tight')
print_and_save("\n- Saved plot: terminus_exploration.png")
plt.show()

print_and_save("\n" + "=" * 60)
print_and_save("INTERPRETATION")
print_and_save("=" * 60)
kr_pct = (c_term_counts.get('K', 0) + c_term_counts.get('R', 0)) / total * 100
print_and_save(f"\nK/R at C-terminus: {kr_pct:.2f}%")
if kr_pct > 80:
    print_and_save(" High K/R suggests trypsin digestion (expected)")
elif kr_pct > 60:
    print_and_save("Mostly K/R, consistent with trypsin")
else:
    print_and_save("Lower K/R than expected for trypsin")
    print_and_save("  Could indicate mixed enzymes or prediction issues")

print_and_save(f"\nOther notable C-termini:")
for aa, count in list(c_term_counts.items())[1:6]:  
    if aa not in ['K', 'R']:
        pct = (count / total) * 100
        print_and_save(f"  {aa}: {pct:.2f}% ({count:,})")

output_file.close()
print(f"\n- Saved results to: terminus_analysis_results.txt")
