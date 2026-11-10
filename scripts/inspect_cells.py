import json

with open('experiments/kaggle_smoke_test.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

cells = nb['cells']
print(f"Total cells: {len(cells)}")
for i, cell in enumerate(cells):
    cell_type = cell['cell_type']
    src = ''.join(cell['source'])
    first_line = src.strip().split('\n')[0] if src.strip() else 'EMPTY'
    print(f"Cell {i} ({cell_type}, {len(cell['source'])} lines): {first_line[:80]}")

