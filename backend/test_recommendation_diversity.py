"""
测试鸡尾酒推荐算法的多样性
设计10个不同的参数配置，测试推荐算法的多样性
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.cocktail_db import get_cocktail_db
import json

def test_recommendation_diversity():
    """测试推荐算法的多样性"""
    
    db = get_cocktail_db()
    
    # 设计10个不同的测试配置
    test_configs = [
        {
            "name": "高能量低紧张（兴奋但不焦虑）",
            "energy": 5,
            "tension": 2,
            "control": 3,
            "needs": ["excitement", "confidence", "energy"],
            "energy_weight": 1.2,  # 更重视Energy匹配
            "tension_weight": 0.8,
            "control_weight": 1.0,
            "need_weight": 2.5,
            "diversity_bonus": 0.25  # 增大多样性奖励
        },
        {
            "name": "低能量高紧张（疲惫且焦虑）",
            "energy": 2,
            "tension": 5,
            "control": 2,
            "needs": ["relaxation", "comfort", "calm"],
            "energy_weight": 1.0,
            "tension_weight": 1.2,  # 更重视Tension匹配
            "control_weight": 0.8,
            "need_weight": 2.5,
            "diversity_bonus": 0.25  # 增大多样性奖励
        },
        {
            "name": "高控制低能量（冷静但疲惫）",
            "energy": 2,
            "tension": 3,
            "control": 5,
            "needs": ["focus", "clarity", "peace"],
            "energy_weight": 0.8,
            "tension_weight": 1.0,
            "control_weight": 1.2,  # 更重视Control匹配
            "need_weight": 2.5,
            "diversity_bonus": 0.25  # 增大多样性奖励
        },
        {
            "name": "平衡型（中等水平）",
            "energy": 3,
            "tension": 3,
            "control": 3,
            "needs": ["balance", "harmony", "stability"],
            "energy_weight": 1.0,
            "tension_weight": 1.0,
            "control_weight": 1.0,
            "need_weight": 2.5,
            "diversity_bonus": 0.30  # 更大多样性（平衡型需要更多样化）
        },
        {
            "name": "高能量高紧张（极度兴奋）",
            "energy": 5,
            "tension": 5,
            "control": 2,
            "needs": ["intensity", "thrill", "adventure"],
            "energy_weight": 1.1,
            "tension_weight": 1.1,
            "control_weight": 0.9,
            "need_weight": 2.8,  # 更重视需求匹配
            "diversity_bonus": 0.25  # 增大多样性奖励
        },
        {
            "name": "低能量低紧张（放松平静）",
            "energy": 2,
            "tension": 2,
            "control": 4,
            "needs": ["ease", "comfort", "relaxation"],
            "energy_weight": 1.0,
            "tension_weight": 1.0,
            "control_weight": 1.1,
            "need_weight": 2.5,
            "diversity_bonus": 0.28  # 增大多样性奖励
        },
        {
            "name": "中等能量高控制（稳健）",
            "energy": 3,
            "tension": 3,
            "control": 5,
            "needs": ["discipline", "authority", "precision"],
            "energy_weight": 1.0,
            "tension_weight": 1.0,
            "control_weight": 1.3,  # 更重视Control
            "need_weight": 2.5,
            "diversity_bonus": 0.25  # 增大多样性奖励
        },
        {
            "name": "高能量中等控制（活力四射）",
            "energy": 5,
            "tension": 3,
            "control": 3,
            "needs": ["vitality", "enthusiasm", "joy"],
            "energy_weight": 1.3,  # 更重视Energy
            "tension_weight": 0.9,
            "control_weight": 1.0,
            "need_weight": 2.5,
            "diversity_bonus": 0.30  # 更大多样性（活力型需要更多样化）
        },
        {
            "name": "低能量高控制（冷静内敛）",
            "energy": 2,
            "tension": 2,
            "control": 5,
            "needs": ["introspection", "calm", "wisdom"],
            "energy_weight": 0.8,
            "tension_weight": 0.8,
            "control_weight": 1.4,  # 非常重视Control
            "need_weight": 2.5,
            "diversity_bonus": 0.25  # 增大多样性奖励
        },
        {
            "name": "极端不平衡（高能量低控制）",
            "energy": 5,
            "tension": 4,
            "control": 2,
            "needs": ["freedom", "spontaneity", "rebellion"],
            "energy_weight": 1.2,
            "tension_weight": 1.1,
            "control_weight": 0.7,  # 不太重视Control
            "need_weight": 2.8,  # 更重视需求匹配
            "diversity_bonus": 0.30  # 更大多样性（极端情况需要更多样化）
        },
    ]
    
    print("=" * 80)
    print("鸡尾酒推荐算法多样性测试")
    print("=" * 80)
    print()
    
    all_recommended = []
    results = []
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n测试配置 {i}: {config['name']}")
        print("-" * 80)
        print(f"参数: Energy={config['energy']}, Tension={config['tension']}, Control={config['control']}")
        print(f"需求: {', '.join(config['needs'])}")
        print(f"权重: Energy={config['energy_weight']}, Tension={config['tension_weight']}, Control={config['control_weight']}, Need={config['need_weight']}")
        print(f"多样性奖励: {config['diversity_bonus']}")
        print()
        
        # 测试不同的top_k值（1, 3, 5）
        for top_k in [1, 3, 5]:
            matches = db.find_best_match(
                energy=config['energy'],
                tension=config['tension'],
                control=config['control'],
                needs=config['needs'],
                top_k=top_k,
                energy_weight=config['energy_weight'],
                tension_weight=config['tension_weight'],
                control_weight=config['control_weight'],
                need_weight=config['need_weight'],
                diversity_bonus=config['diversity_bonus'],
                used_cocktails=all_recommended if config['diversity_bonus'] > 0 else None,
                enable_randomization=True,
                random_seed=42  # 使用固定种子以便重现
            )
            
            recommended_names = [m['cocktail']['Name'] for m in matches]
            all_recommended.extend(recommended_names)
            
            print(f"  推荐 Top-{top_k}:")
            for j, match in enumerate(matches, 1):
                cocktail = match['cocktail']
                print(f"    {j}. {cocktail['Name']} (分数: {match['score']:.3f})")
                print(f"       维度: Energy={cocktail.get('Energy', 3)}, Tension={cocktail.get('Tension', 3)}, Control={cocktail.get('Control', 3)}")
                print(f"       需求: {', '.join(cocktail.get('Need', []))}")
                print(f"       差异: Energy±{match['energy_diff']}, Tension±{match['tension_diff']}, Control±{match['control_diff']}")
            
            results.append({
                'config': config['name'],
                'top_k': top_k,
                'recommended': recommended_names,
                'scores': [m['score'] for m in matches]
            })
        
        print()
    
    # 统计多样性
    print("=" * 80)
    print("多样性统计")
    print("=" * 80)
    
    all_unique = list(set(all_recommended))
    print(f"\n总共推荐了 {len(all_recommended)} 个鸡尾酒（包含重复）")
    print(f"共涉及 {len(all_unique)} 种不同的鸡尾酒")
    print(f"多样性比例: {len(all_unique) / len(all_recommended) * 100:.1f}%")
    
    # 统计每种鸡尾酒被推荐的次数
    from collections import Counter
    counter = Counter(all_recommended)
    print(f"\n最常被推荐的鸡尾酒（Top 10）:")
    for name, count in counter.most_common(10):
        print(f"  {name}: {count} 次")
    
    # 统计每个配置推荐的唯一性
    print(f"\n每个配置的推荐唯一性:")
    for i, config in enumerate(test_configs, 1):
        # 找到这个配置的所有推荐
        config_recommendations = []
        for result in results:
            if result['config'] == config['name']:
                config_recommendations.extend(result['recommended'])
        
        unique_count = len(set(config_recommendations))
        total_count = len(config_recommendations)
        uniqueness = unique_count / total_count * 100 if total_count > 0 else 0
        
        print(f"  {i}. {config['name']}: {unique_count}/{total_count} 唯一 ({uniqueness:.1f}%)")
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)

if __name__ == "__main__":
    test_recommendation_diversity()
