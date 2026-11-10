import json

with open('experiments/kaggle_smoke_test.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

with open('reports/all_notebook_cells.py', 'w', encoding='utf-8') as out:
    for i, cell in enumerate(nb['cells']):
        out.write(f"\n{'='*40}\n# CELL {i} ({cell['cell_type']})\n{'='*40}\n")
        out.write(''.join(cell['source']))
        out.write('\n')

print("Wrote reports/all_notebook_cells.py successfully.")

