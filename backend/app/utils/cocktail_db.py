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
        """获取所有Category为'Cocktail'的条目"""
        if self._cocktails_cache is None:
            self._cocktails_cache = [
                item for item in self.data 
                if item.get('Category') == 'Cocktail'
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
        cocktail: Dict[str, Any]
    ) -> float:
        """
        计算鸡尾酒与目标维度的匹配度
        
        Args:
            target_energy: 目标Energy值 (1-5)
            target_tension: 目标Tension值 (1-5)
            target_control: 目标Control值 (1-5)
            target_needs: 目标需求列表
            cocktail: 候选鸡尾酒数据
        
        Returns:
            匹配度分数（越高越好）
        """
        cocktail_energy = cocktail.get('Energy', 3)
        cocktail_tension = cocktail.get('Tension', 3)
        cocktail_control = cocktail.get('Control', 3)
        cocktail_needs = cocktail.get('Need', [])
        
        # 计算维度差异（越小越好）
        energy_diff = abs(target_energy - cocktail_energy)
        tension_diff = abs(target_tension - cocktail_tension)
        control_diff = abs(target_control - cocktail_control)
        dimension_diff = energy_diff + tension_diff + control_diff
        
        # 计算需求匹配度（共同需求数量）
        # 转换为小写进行比较，提高匹配率
        target_needs_lower = [need.lower() for need in target_needs]
        cocktail_needs_lower = [need.lower() for need in cocktail_needs]
        need_matches = len(set(target_needs_lower) & set(cocktail_needs_lower))
        
        # 匹配度公式：需求匹配权重 × 匹配数 - 维度差异权重 × 差异
        # 需求匹配权重：2.0（更重要）
        # 维度差异权重：0.5
        need_weight = 2.0
        diff_weight = 0.5
        
        score = need_weight * need_matches - diff_weight * dimension_diff
        
        return score
    
    def find_best_match(
        self,
        energy: int,
        tension: int,
        control: int,
        needs: List[str],
        top_k: int = 1
    ) -> List[Dict[str, Any]]:
        """
        根据维度查找最匹配的鸡尾酒
        
        Args:
            energy: Energy维度 (1-5)
            tension: Tension维度 (1-5)
            control: Control维度 (1-5)
            needs: 需求列表
            top_k: 返回前k个结果
        
        Returns:
            匹配度最高的鸡尾酒列表，包含匹配度分数
        """
        cocktails = self.get_cocktails()
        
        scored_cocktails = []
        for cocktail in cocktails:
            score = self.calculate_match_score(
                energy, tension, control, needs, cocktail
            )
            scored_cocktails.append({
                'cocktail': cocktail,
                'score': score,
                'energy_diff': abs(energy - cocktail.get('Energy', 3)),
                'tension_diff': abs(tension - cocktail.get('Tension', 3)),
                'control_diff': abs(control - cocktail.get('Control', 3)),
            })
        
        # 按分数降序排序
        scored_cocktails.sort(key=lambda x: x['score'], reverse=True)
        
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
