from typing import Dict, Any, List
from app.utils.cocktail_db import get_cocktail_db
from app.services.llm_service import get_llm_service
from app.models.schemas import (
    CocktailMixOutput,
    BaseCocktail,
    CocktailIngredient,
    SemanticAnalysisOutput
)
import json
import logging

logger = logging.getLogger(__name__)


class CocktailAgent:
    """鸡尾酒调配Agent - 根据语义分析结果选择并微调鸡尾酒"""
    
    def __init__(self):
        self.cocktail_db = get_cocktail_db()
        self.llm_service = get_llm_service()
        # 推荐历史记录（session-based，key为session_id，value为鸡尾酒名称列表）
        self._recommendation_history: Dict[str, List[str]] = {}
    
    def mix_cocktail(
        self,
        semantic_output: SemanticAnalysisOutput,
        session_id: Optional[str] = None
    ) -> CocktailMixOutput:
        """
        根据语义分析结果调配鸡尾酒
        
        Args:
            semantic_output: 语义分析Agent的输出
        
        Returns:
            CocktailMixOutput: 鸡尾酒调配结果
        """
        try:
            # 获取推荐历史（对已推荐的鸡尾酒降权）
            used_cocktails = None
            if session_id and session_id in self._recommendation_history:
                used_cocktails = self._recommendation_history[session_id][-10:]  # 最近10次推荐
            
            # 步骤1：基础匹配（使用改进的推荐算法，支持多样性和灵活权重）
            best_matches = self.cocktail_db.find_best_match(
                energy=semantic_output.energy,
                tension=semantic_output.tension,
                control=semantic_output.control,
                needs=semantic_output.needs,
                top_k=1,
                energy_weight=1.0,  # 默认权重，可根据需要调整
                tension_weight=1.0,
                control_weight=1.0,
                need_weight=1.5,  # 降低需求匹配权重（从2.5降到1.5）
                diversity_bonus=0.4,  # 增加多样性奖励（从0.35提高到0.4）
                used_cocktails=used_cocktails,  # 传入已使用的鸡尾酒列表以降低权重
                enable_randomization=True,  # 启用Top-K随机化
                random_seed=None  # 不设置seed，确保每次随机
            )
            
            if not best_matches:
                raise Exception("未能找到匹配的鸡尾酒")
            
            base_cocktail_data = best_matches[0]['cocktail']
            selected_cocktail_name = base_cocktail_data.get('Name', '')
            
            # 更新推荐历史
            if session_id:
                if session_id not in self._recommendation_history:
                    self._recommendation_history[session_id] = []
                self._recommendation_history[session_id].append(selected_cocktail_name)
                # 只保留最近20次推荐记录
                if len(self._recommendation_history[session_id]) > 20:
                    self._recommendation_history[session_id] = self._recommendation_history[session_id][-20:]
            
            base_cocktail = BaseCocktail(
                name=selected_cocktail_name,
                recipe=base_cocktail_data.get('Recipe', ''),
                description=base_cocktail_data.get('Description', '')
            )
            
            # 步骤2：创意微调
            customization_result = self._customize_cocktail(
                base_cocktail=base_cocktail,
                semantic_output=semantic_output
            )
            
            return CocktailMixOutput(
                base_cocktail=base_cocktail,
                customized_recipe=customization_result.get('customized_recipe', base_cocktail.recipe),
                customized_description=customization_result.get('customized_description', base_cocktail.description),
                adjustment_rationale=customization_result.get('adjustment_rationale', ''),
                ingredients=customization_result.get('ingredients', [])
            )
        except Exception as e:
            logger.error(f"鸡尾酒调配失败: {str(e)}")
            # 返回基础鸡尾酒，不进行微调
            fallback_cocktail = BaseCocktail(
                name="Classic Cocktail",
                recipe="Base spirit + Modifier",
                description="A classic cocktail"
            )
            return CocktailMixOutput(
                base_cocktail=fallback_cocktail,
                customized_recipe=fallback_cocktail.recipe,
                customized_description=fallback_cocktail.description,
                adjustment_rationale="使用基础配方",
                ingredients=[]
            )
    
    def _customize_cocktail(
        self,
        base_cocktail: BaseCocktail,
        semantic_output: SemanticAnalysisOutput
    ) -> Dict[str, Any]:
        """
        创意微调鸡尾酒
        
        Args:
            base_cocktail: 基础鸡尾酒
            semantic_output: 语义分析输出
        
        Returns:
            微调结果字典
        """
        try:
            # 搜索合适的微调原料
            modifier_ingredients = self.cocktail_db.search_ingredients_by_needs(
                needs=semantic_output.needs,
                subtle_emotions=semantic_output.subtle_emotions,
                category="Modifier"
            )[:3]  # 取前3个
            
            fruit_ingredients = self.cocktail_db.search_ingredients_by_needs(
                needs=semantic_output.needs,
                subtle_emotions=semantic_output.subtle_emotions,
                category="Fruit / Juice"
            )[:2]
            
            spice_ingredients = self.cocktail_db.search_ingredients_by_needs(
                needs=semantic_output.needs,
                subtle_emotions=semantic_output.subtle_emotions,
                category="Spice / Botanical"
            )[:2]
            
            # 构建prompt进行GPT-4微调建议
            prompt = self._build_customization_prompt(
                base_cocktail=base_cocktail,
                semantic_output=semantic_output,
                modifier_ingredients=modifier_ingredients,
                fruit_ingredients=fruit_ingredients,
                spice_ingredients=spice_ingredients
            )
            
            response = self.llm_service.generate_sync(
                prompt=prompt,
                max_tokens=1500,
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            
            customization_result = json.loads(response)
            
            # 构建ingredients列表
            ingredients = []
            for ing in customization_result.get('ingredients', []):
                ingredients.append(CocktailIngredient(
                    name=ing.get('name', ''),
                    category=ing.get('category', ''),
                    amount=ing.get('amount', '')
                ))
            
            return {
                'customized_recipe': customization_result.get('customized_recipe', ''),
                'customized_description': customization_result.get('customized_description', ''),
                'adjustment_rationale': customization_result.get('adjustment_rationale', ''),
                'ingredients': ingredients
            }
        except Exception as e:
            logger.error(f"创意微调失败: {str(e)}")
            # 返回基础配方
            return {
                'customized_recipe': base_cocktail.recipe,
                'customized_description': base_cocktail.description,
                'adjustment_rationale': '保持原配方',
                'ingredients': []
            }
    
    def _build_customization_prompt(
        self,
        base_cocktail: BaseCocktail,
        semantic_output: SemanticAnalysisOutput,
        modifier_ingredients: List[Dict[str, Any]],
        fruit_ingredients: List[Dict[str, Any]],
        spice_ingredients: List[Dict[str, Any]]
    ) -> str:
        """构建微调的prompt"""
        
        modifier_names = [ing.get('Name', '') for ing in modifier_ingredients]
        fruit_names = [ing.get('Name', '') for ing in fruit_ingredients]
        spice_names = [ing.get('Name', '') for ing in spice_ingredients]
        
        prompt = f"""你是一位资深的调酒师。请根据用户的情感需求，对基础鸡尾酒进行创意微调。

基础鸡尾酒信息：
- 名称：{base_cocktail.name}
- 配方：{base_cocktail.recipe}
- 描述：{base_cocktail.description}

用户情感分析：
- 能量：{semantic_output.energy}/5
- 紧张度：{semantic_output.tension}/5
- 控制感：{semantic_output.control}/5
- 情感需求：{', '.join(semantic_output.needs)}
- 细微情感：{', '.join(semantic_output.subtle_emotions)}
- 语调：{semantic_output.tone}
- 主题：{', '.join(semantic_output.themes)}

可选微调原料：
- 调味剂（Modifier）：{', '.join(modifier_names) if modifier_names else '无'}
- 水果/果汁（Fruit/Juice）：{', '.join(fruit_names) if fruit_names else '无'}
- 香料/植物（Spice/Botanical）：{', '.join(spice_names) if spice_names else '无'}

请输出JSON格式的微调方案：
{{
  "customized_recipe": "微调后的完整配方（如：Base Spirit 60ml + Modifier 20ml + Fruit/Juice 15ml）",
  "customized_description": "微调后的鸡尾酒描述（中文，50字以内）",
  "adjustment_rationale": "微调理由说明（中文，说明为什么这样调整，如何体现用户的情感需求）",
  "ingredients": [
    {{"name": "原料名", "category": "类别", "amount": "用量"}},
    ...
  ]
}}

注意：
- 配方要符合鸡尾酒调配逻辑
- 可以根据情感需求适当添加或替换原料
- 如果不需要大幅调整，可以保持原配方，但需要说明理由
"""
        return prompt
