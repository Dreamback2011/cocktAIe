"""分析鸡尾酒分布，为推荐算法改进提供数据支持"""
import json
import os
from collections import Counter, defaultdict

# 读取数据
current_dir = os.path.dirname(os.path.dirname(__file__))
db_path = os.path.join(current_dir, "cocktails.json")

with open(db_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

cocktails = [x for x in data if x.get('Category') in ['Cocktail', 'Top Bar Cocktail']]

print("=" * 80)
print("鸡尾酒数据库分析".center(80))
print("=" * 80)
print(f"\n总鸡尾酒数: {len(cocktails)}")
print(f"  - Cocktail: {len([x for x in cocktails if x.get('Category') == 'Cocktail'])}")
print(f"  - Top Bar Cocktail: {len([x for x in cocktails if x.get('Category') == 'Top Bar Cocktail'])}")

# 分析需求分布
needs_freq = Counter()
for c in cocktails:
    for need in c.get('Need', []):
        needs_freq[need.lower()] += 1

print("\n最常见的需求（Top 10）:")
for need, freq in needs_freq.most_common(10):
    print(f"  {need}: {freq}次 ({freq/len(cocktails)*100:.1f}%)")

# 分析维度组合分布
etc_combos = Counter()
for c in cocktails:
    etc = (c.get('Energy', 3), c.get('Tension', 3), c.get('Control', 3))
    etc_combos[etc] += 1

print("\n最常见的维度组合（Top 5）:")
for combo, freq in etc_combos.most_common(5):
    print(f"  Energy={combo[0]}, Tension={combo[1]}, Control={combo[2]}: {freq}次 ({freq/len(cocktails)*100:.1f}%)")

# 分析Cuba Libre
cuba_libre = next((c for c in cocktails if c.get('Name') == 'Cuba Libre'), None)
if cuba_libre:
    print("\nCuba Libre分析:")
    print(f"  维度: Energy={cuba_libre.get('Energy')}, Tension={cuba_libre.get('Tension')}, Control={cuba_libre.get('Control')}")
    print(f"  需求: {', '.join(cuba_libre.get('Need', []))}")
    
    # 找出相同维度的鸡尾酒
    same_etc = [c for c in cocktails 
                if c.get('Energy') == cuba_libre.get('Energy') 
                and c.get('Tension') == cuba_libre.get('Tension') 
                and c.get('Control') == cuba_libre.get('Control')]
    print(f"  相同维度的鸡尾酒数量: {len(same_etc)}")
    print(f"  相同维度的鸡尾酒: {[c.get('Name') for c in same_etc[:10]]}")

# 分析通用需求
common_needs_list = ["comfort", "relaxation", "casual fun", "ease", "approachability", "nostalgia"]
universal_cocktails = []
for c in cocktails:
    needs = [n.lower() for n in c.get('Need', [])]
    common_count = sum(1 for need in needs if need in common_needs_list)
    if common_count >= 2:
        universal_cocktails.append((c.get('Name'), common_count))

print(f"\n通用型鸡尾酒（包含2个以上通用需求）: {len(universal_cocktails)}个")
if universal_cocktails:
    print("示例:")
    for name, count in sorted(universal_cocktails, key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {name}: {count}个通用需求")

print("\n" + "=" * 80)
