import json
import os
from typing import List, Dict, Any, Optional
from functools import lru_cache


class CocktailDB:
    """鸡尾酒数据库查询工具"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # 默认路径：项目根目录下的cocktails.json
            # 从backend/app/utils/向上到项目根目录
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            db_path = os.path.join(current_dir, "cocktails.json")
            # 如果不在backend目录下，尝试项目根目录
            if not os.path.exists(db_path):
                # 尝试从backend向上找项目根目录
                backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                project_root = os.path.dirname(backend_dir)
                db_path = os.path.join(project_root, "cocktails.json")
        self.db_path = db_path
        self._data = None
        self._cocktails_cache = None
        self._ingredients_cache = None
    
    @property
    def data(self) -> List[Dict[str, Any]]:
        """懒加载数据库数据"""
        if self._data is None:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
        return self._data
    
    @lru_cache(maxsize=1)
    def get_cocktails(self) -> List[Dict[str, Any]]:
        """获取所有Category为'Cocktail'或'Top Bar Cocktail'的条目"""
        if self._cocktails_cache is None:
            self._cocktails_cache = [
                item for item in self.data 
                if item.get('Category') in ['Cocktail', 'Top Bar Cocktail']
            ]
        return self._cocktails_cache
    
    @lru_cache(maxsize=1)
    def get_all_ingredients_by_category(self) -> Dict[str, List[Dict[str, Any]]]:
        """按类别获取所有原料"""
        if self._ingredients_cache is None:
            self._ingredients_cache = {}
            for item in self.data:
                category = item.get('Category', 'Unknown')
                if category != 'Cocktail' and category != 'Top Bar Cocktail':
                    if category not in self._ingredients_cache:
                        self._ingredients_cache[category] = []
                    self._ingredients_cache[category].append(item)
        return self._ingredients_cache
    
    def get_ingredients_by_category(self, category: str) -> List[Dict[str, Any]]:
        """获取指定类别的原料"""
        all_ingredients = self.get_all_ingredients_by_category()
        return all_ingredients.get(category, [])
    
    def calculate_match_score(
        self,
        target_energy: int,
        target_tension: int,
        target_control: int,
        target_needs: List[str],
        cocktail: Dict[str, Any],
        energy_weight: float = 1.0,
        tension_weight: float = 1.0,
        control_weight: float = 1.0,
        need_weight: float = 2.5,
        diversity_bonus: float = 0.0,
        used_cocktails: Optional[List[str]] = None
    ) -> float:
        """
        计算鸡尾酒与目标维度的匹配度（改进版，支持多样性和灵活权重）
        
        Args:
            target_energy: 目标Energy值 (1-5)
            target_tension: 目标Tension值 (1-5)
            target_control: 目标Control值 (1-5)
            target_needs: 目标需求列表
            cocktail: 候选鸡尾酒数据
            energy_weight: Energy维度权重（默认1.0）
            tension_weight: Tension维度权重（默认1.0）
            control_weight: Control维度权重（默认1.0）
            need_weight: 需求匹配权重（默认2.5，比维度更重要）
            diversity_bonus: 多样性奖励（用于未使用过的鸡尾酒，默认0.0）
            used_cocktails: 已使用的鸡尾酒名称列表（用于多样性计算）
        
        Returns:
            匹配度分数（越高越好）
        """
        cocktail_energy = cocktail.get('Energy', 3)
        cocktail_tension = cocktail.get('Tension', 3)
        cocktail_control = cocktail.get('Control', 3)
        cocktail_needs = cocktail.get('Need', [])
        cocktail_name = cocktail.get('Name', '')
        
        # 计算加权维度差异（使用平方差异，对大差异惩罚更重）
        energy_diff = abs(target_energy - cocktail_energy)
        tension_diff = abs(target_tension - cocktail_tension)
        control_diff = abs(target_control - cocktail_control)
        
        # 使用平方差异，使大差异惩罚更重
        weighted_dimension_score = (
            energy_weight * (1.0 - (energy_diff ** 2) / 16.0) +  # 最大差异4，平方后16
            tension_weight * (1.0 - (tension_diff ** 2) / 16.0) +
            control_weight * (1.0 - (control_diff ** 2) / 16.0)
        ) / (energy_weight + tension_weight + control_weight)  # 归一化
        
        # 计算需求匹配度（共同需求数量）
        target_needs_lower = [need.lower() for need in target_needs]
        cocktail_needs_lower = [need.lower() for need in cocktail_needs]
        need_matches = len(set(target_needs_lower) & set(cocktail_needs_lower))
        max_needs = max(len(target_needs), len(cocktail_needs), 1)
        need_match_ratio = need_matches / max_needs  # 需求匹配比例
        
        # 多样性奖励/惩罚：如果这个鸡尾酒没有被使用过，给予奖励；如果已使用过，应用降分惩罚
        diversity_score = 0.0
        if used_cocktails is not None:
            if cocktail_name not in used_cocktails:
                # 未使用过：给予奖励
                diversity_score = diversity_bonus
            else:
                # 已使用过：应用降分惩罚（降低30-50%的基础分数）
                # 根据使用频率调整惩罚程度
                usage_count = used_cocktails.count(cocktail_name)
                penalty_rate = min(0.5, 0.3 + usage_count * 0.1)  # 首次0.3，每次使用增加0.1，最多0.5
                # 注意：惩罚将在后面应用到base_score上，这里返回负值作为标记
                diversity_score = -penalty_rate
        
        # Top Bar Cocktail 权重加成
        category_bonus = 0.0
        if cocktail.get('Category') == 'Top Bar Cocktail':
            category_bonus = 0.15  # Top Bar Cocktail额外加成15%
        
        # 综合分数计算
        # 降低需求匹配权重，提高维度匹配权重（从40/60改为60/40）
        base_score = (
            weighted_dimension_score * 0.6 +  # 维度匹配占60%（提升）
            need_match_ratio * 0.4 * need_weight / 2.5  # 需求匹配占40%（降低）
        )
        
        # 反通用性惩罚：识别包含通用需求的鸡尾酒并降分
        COMMON_NEEDS = ["comfort", "relaxation", "casual fun", "ease", "approachability", "nostalgia"]
        universality_penalty = 1.0
        common_count = sum(1 for need in cocktail_needs_lower if need in COMMON_NEEDS)
        if common_count >= 2:
            universality_penalty = 0.75  # 包含2个以上通用需求，降25%
        elif common_count == 1:
            universality_penalty = 0.9   # 包含1个通用需求，降10%
        
        # 应用通用性惩罚
        base_score = base_score * universality_penalty
        
        # 处理多样性奖励/惩罚
        # 如果diversity_score为正，表示奖励（加 bonus）
        # 如果diversity_score为负，表示惩罚（乘以惩罚系数）
        if diversity_score > 0:
            # 多样性奖励：直接加在base_score上
            final_score = base_score + diversity_score + category_bonus
        elif diversity_score < 0:
            # 多样性惩罚：降低base_score（惩罚系数 = 1 - abs(diversity_score)）
            penalty_coefficient = 1.0 - abs(diversity_score)
            final_score = base_score * penalty_coefficient + category_bonus
        else:
            # 无多样性影响
            final_score = base_score + category_bonus
        
        return final_score
    
    def find_best_match(
        self,
        energy: int,
        tension: int,
        control: int,
        needs: List[str],
        top_k: int = 1,
        energy_weight: float = 1.0,
        tension_weight: float = 1.0,
        control_weight: float = 1.0,
        need_weight: float = 2.5,
        diversity_bonus: float = 0.0,
        used_cocktails: Optional[List[str]] = None,
        enable_randomization: bool = False,
        random_seed: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        根据维度查找最匹配的鸡尾酒（改进版，支持多样性和灵活权重）
        
        Args:
            energy: Energy维度 (1-5)
            tension: Tension维度 (1-5)
            control: Control维度 (1-5)
            needs: 需求列表
            top_k: 返回前k个结果
            energy_weight: Energy维度权重（默认1.0）
            tension_weight: Tension维度权重（默认1.0）
            control_weight: Control维度权重（默认1.0）
            need_weight: 需求匹配权重（默认2.5）
            diversity_bonus: 多样性奖励（默认0.0，范围0.0-0.5）
            used_cocktails: 已使用的鸡尾酒名称列表（用于多样性）
            enable_randomization: 是否在相近分数间随机化（默认False）
            random_seed: 随机种子（用于可重复性）
        
        Returns:
            匹配度最高的鸡尾酒列表，包含匹配度分数和详细信息
        """
        import random
        if random_seed is not None:
            random.seed(random_seed)
        
        cocktails = self.get_cocktails()
        
        scored_cocktails = []
        for cocktail in cocktails:
            score = self.calculate_match_score(
                target_energy=energy,
                target_tension=tension,
                target_control=control,
                target_needs=needs,
                cocktail=cocktail,
                energy_weight=energy_weight,
                tension_weight=tension_weight,
                control_weight=control_weight,
                need_weight=need_weight,
                diversity_bonus=diversity_bonus,
                used_cocktails=used_cocktails
            )
            
            scored_cocktails.append({
                'cocktail': cocktail,
                'score': score,
                'energy_diff': abs(energy - cocktail.get('Energy', 3)),
                'tension_diff': abs(tension - cocktail.get('Tension', 3)),
                'control_diff': abs(control - cocktail.get('Control', 3)),
                'name': cocktail.get('Name', '')
            })
        
        # 按分数降序排序
        scored_cocktails.sort(key=lambda x: x['score'], reverse=True)
        
        # 如果启用随机化，从Top-K候选中进行多样性加权随机选择
        if enable_randomization:
            # 计算Top候选数量（根据top_k动态调整，至少10个，最多30个）
            top_candidate_count = max(10, min(30, top_k * 5))
            top_candidates = scored_cocktails[:top_candidate_count]
            
            if len(top_candidates) <= top_k:
                # 候选数量不足，直接返回
                return top_candidates[:top_k]
            
            # 多样性加权随机选择：分数越高概率越大，但Top-K都有机会
            max_score = top_candidates[0]['score']
            min_score = top_candidates[-1]['score']
            score_range = max_score - min_score if max_score > min_score else 1.0
            
            # 计算每个候选的选择概率
            probabilities = []
            for candidate in top_candidates:
                # 基础概率（均匀分布）+ 分数加成（指数衰减）
                normalized_score = (candidate['score'] - min_score) / score_range if score_range > 0 else 0.5
                # 使用平方根衰减，让Top-K候选都有较高概率
                base_prob = 1.0 / len(top_candidates)  # 均匀分布基础
                score_bonus = 0.5 * (normalized_score ** 0.5)  # 平方根衰减，更平滑
                probabilities.append(base_prob + score_bonus)
            
            # 归一化概率
            total_prob = sum(probabilities)
            if total_prob > 0:
                probabilities = [p / total_prob for p in probabilities]
            else:
                # 如果总概率为0，使用均匀分布
                probabilities = [1.0 / len(top_candidates)] * len(top_candidates)
            
            # 从Top候选中进行加权随机选择（不重复）
            selected_results = []
            remaining_candidates = list(range(len(top_candidates)))
            remaining_probs = probabilities.copy()
            
            for _ in range(top_k):
                if not remaining_candidates:
                    break
                
                # 归一化剩余概率
                total_remaining = sum(remaining_probs)
                if total_remaining > 0:
                    remaining_probs = [p / total_remaining for p in remaining_probs]
                else:
                    remaining_probs = [1.0 / len(remaining_candidates)] * len(remaining_candidates)
                
                # 加权随机选择
                selected_idx = random.choices(remaining_candidates, weights=remaining_probs, k=1)[0]
                selected_results.append(top_candidates[selected_idx])
                
                # 从候选列表中移除已选择的
                removed_idx = remaining_candidates.index(selected_idx)
                remaining_candidates.pop(removed_idx)
                remaining_probs.pop(removed_idx)
            
            return selected_results
        else:
            # 返回前top_k个结果
            return scored_cocktails[:top_k]
    
    def get_cocktail_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称查找鸡尾酒"""
        for item in self.data:
            if item.get('Name') == name:
                return item
        return None
    
    def search_ingredients_by_needs(
        self,
        needs: List[str],
        subtle_emotions: List[str],
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        根据需求和情感搜索合适的原料
        
        Args:
            needs: 需求列表
            subtle_emotions: 细微情感列表
            category: 原料类别（可选），如'Modifier', 'Fruit/Juice'等
        
        Returns:
            匹配的原料列表
        """
        if category:
            ingredients = self.get_ingredients_by_category(category)
        else:
            all_ingredients = self.get_all_ingredients_by_category()
            ingredients = []
            for cat_ingredients in all_ingredients.values():
                ingredients.extend(cat_ingredients)
        
        # 简单的关键词匹配（可以后续优化为更复杂的语义匹配）
        needs_lower = [need.lower() for need in needs]
        emotions_lower = [emotion.lower() for emotion in subtle_emotions]
        keywords = needs_lower + emotions_lower
        
        matched_ingredients = []
        for ingredient in ingredients:
            ingredient_needs = ingredient.get('Need', [])
            ingredient_needs_lower = [n.lower() for n in ingredient_needs]
            ingredient_desc = ingredient.get('Description', '').lower()
            ingredient_name = ingredient.get('Name', '').lower()
            
            # 检查是否有匹配的关键词
            matches = 0
            for keyword in keywords:
                if any(keyword in need for need in ingredient_needs_lower):
                    matches += 2  # 需求匹配权重更高
                elif keyword in ingredient_desc or keyword in ingredient_name:
                    matches += 1
            
            if matches > 0:
                matched_ingredients.append({
                    'ingredient': ingredient,
                    'match_score': matches
                })
        
        # 按匹配度排序
        matched_ingredients.sort(key=lambda x: x['match_score'], reverse=True)
        
        return [item['ingredient'] for item in matched_ingredients[:10]]  # 返回前10个


# 全局数据库实例（单例模式）
_db_instance: Optional[CocktailDB] = None


def get_cocktail_db(db_path: Optional[str] = None) -> CocktailDB:
    """获取全局数据库实例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = CocktailDB(db_path)
    return _db_instance
