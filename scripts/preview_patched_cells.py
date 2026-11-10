import json

with open("experiments/kaggle_smoke_test.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

for i in [2, 3, 5, 7, 8]:
    cell = nb["cells"][i]
    print(f"\n{'='*50}\nCELL {i} CODE PREVIEW\n{'='*50}")
    print("".join(cell["source"])[:800])

