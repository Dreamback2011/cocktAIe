import json
from collections import defaultdict

# 读取JSON文件
with open('cocktails.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 按类别分组
categories = defaultdict(list)

for item in data:
    category = item.get('Category', 'Unknown')
    name = item.get('Name', '')
    if name:
        categories[category].append(name)

# 定义类别顺序
category_order = {
    'Base Spirit': 1,
    'Modifier': 2,
    'Fruit / Juice': 3,
    'Fruit': 4,
    'Spice / Botanical': 5,
    'Tea / Coffee': 6,
    'Fermentation': 7,
    'Fat / Texture': 8,
    'Umami / Saline': 9,
    'Cocktail': 10,
    'Top Bar Cocktail': 11
}

# 按类别顺序排序
sorted_categories = sorted(categories.items(), 
                          key=lambda x: (category_order.get(x[0], 99), x[0]))

# 输出结果到文件
output_lines = []
output_lines.append("=" * 60)
output_lines.append("Cocktail List by Category")
output_lines.append("=" * 60)
output_lines.append("")

for category, names in sorted_categories:
    output_lines.append(f"[{category}] ({len(names)} items)")
    output_lines.append("-" * 60)
    for name in sorted(names):  # Sort names within each category
        output_lines.append(f"  - {name}")
    output_lines.append("")

# Statistics
output_lines.append("=" * 60)
output_lines.append("Summary")
output_lines.append("=" * 60)
total = sum(len(names) for names in categories.values())
output_lines.append(f"Total: {total} items")
for category, names in sorted_categories:
    output_lines.append(f"  {category}: {len(names)} items")

# 写入文件
output_text = "\n".join(output_lines)
with open('cocktails_by_category.txt', 'w', encoding='utf-8') as f:
    f.write(output_text)

print("Output saved to cocktails_by_category.txt")
print(f"Total: {total} items across {len(categories)} categories")
