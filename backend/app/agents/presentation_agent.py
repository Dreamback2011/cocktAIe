from typing import Dict, Any, List, Optional
from app.services.llm_service import get_llm_service
from app.services.image_service import get_image_service
from app.services.grok_image_service import get_grok_image_service
from app.services.dalle_image_service import get_dalle_image_service
from app.services.video_service import get_video_service
from app.models.schemas import PresentationOutput, CocktailMixOutput, SemanticAnalysisOutput
import asyncio
import logging

logger = logging.getLogger(__name__)


class PresentationAgent:
    """呈现Agent - 生成鸡尾酒相关的视觉内容和命名"""
    
    def __init__(self):
        self.llm_service = get_llm_service()
        # 延迟加载image和video服务，避免Python 3.14兼容性问题
        self._image_service = None
        self._grok_image_service = None
        self._dalle_image_service = None
        self._video_service = None
    
    @property
    def image_service(self):
        if self._image_service is None:
            try:
                self._image_service = get_image_service()
            except Exception as e:
                logger.warning(f"Replicate图像服务初始化失败: {str(e)}，将尝试其他图片服务")
                self._image_service = None
        return self._image_service
    
    @property
    def grok_image_service(self):
        """Grok图片生成服务"""
        if self._grok_image_service is None:
            try:
                self._grok_image_service = get_grok_image_service()
            except Exception as e:
                logger.warning(f"Grok图片服务初始化失败: {str(e)}")
                self._grok_image_service = None
        return self._grok_image_service
    
    @property
    def dalle_image_service(self):
        """DALL-E图片生成服务（优先使用）"""
        if self._dalle_image_service is None:
            try:
                self._dalle_image_service = get_dalle_image_service()
            except Exception as e:
                logger.warning(f"DALL-E图片服务初始化失败: {str(e)}")
                self._dalle_image_service = None
        return self._dalle_image_service
    
    @property
    def video_service(self):
        if self._video_service is None:
            try:
                self._video_service = get_video_service()
            except Exception as e:
                logger.warning(f"视频服务初始化失败: {str(e)}，将跳过视频生成")
                self._video_service = None
        return self._video_service
    
    def generate_presentation(
        self,
        semantic_output: SemanticAnalysisOutput,
        cocktail_output: CocktailMixOutput,
        progress_callback=None
    ) -> PresentationOutput:
        """
        生成呈现内容
        
        Args:
            semantic_output: 语义分析输出
            cocktail_output: 鸡尾酒调配输出
        
        Returns:
            PresentationOutput: 呈现结果
        """
        try:
            # 任务1：生成四字中文名（同步）
            if progress_callback:
                progress_callback({"step": "生成鸡尾酒名称", "progress": 65})
            cocktail_name, name_candidates = self._generate_cocktail_name(
                semantic_output=semantic_output,
                cocktail_output=cocktail_output
            )
            logger.info(f"生成鸡尾酒名称: {cocktail_name}")
            
            # 生成鸡尾酒图片
            cocktail_image_url = None
            # 检查是否有任何可用的图片服务
            has_image_service = (
                (self.dalle_image_service and self.dalle_image_service.available) or
                (self.grok_image_service and self.grok_image_service.available) or
                (self.image_service and self.image_service.client is not None)
            )
            
            if has_image_service:
                try:
                    if progress_callback:
                        progress_callback({"step": "正在生成鸡尾酒图片（可能需要15-20秒）...", "progress": 70})
                    logger.info("开始生成鸡尾酒图片...")
                    cocktail_image_url = self._generate_cocktail_image(
                        cocktail_name=cocktail_name,
                        cocktail_output=cocktail_output
                    )
                    if cocktail_image_url:
                        if progress_callback:
                            progress_callback({"step": "鸡尾酒图片生成完成", "progress": 72})
                        logger.info(f"鸡尾酒图片生成成功: {cocktail_image_url}")
                    else:
                        if progress_callback:
                            progress_callback({"step": "鸡尾酒图片生成失败，继续处理", "progress": 72})
                        logger.warning("鸡尾酒图片生成返回None")
                except Exception as e:
                    logger.warning(f"鸡尾酒图片生成失败: {str(e)}")
                    if progress_callback:
                        progress_callback({"step": "鸡尾酒图片生成失败，继续处理", "progress": 72})
            else:
                logger.info("图像服务不可用，跳过图片生成")
                if progress_callback:
                    progress_callback({"step": "跳过图片生成（服务不可用）", "progress": 72})
            
            # 生成最终呈现图片
            final_presentation_image_url = None
            if has_image_service:
                try:
                    if progress_callback:
                        progress_callback({"step": "正在生成最终呈现图片（可能需要15-20秒）...", "progress": 75})
                    logger.info("开始生成最终呈现图片...")
                    final_presentation_image_url = self._generate_final_presentation_image(
                        cocktail_name=cocktail_name,
                        cocktail_output=cocktail_output
                    )
                    if final_presentation_image_url:
                        if progress_callback:
                            progress_callback({"step": "最终呈现图片生成完成", "progress": 77})
                        logger.info(f"最终呈现图片生成成功: {final_presentation_image_url}")
                    else:
                        # 使用鸡尾酒图片作为备选
                        final_presentation_image_url = cocktail_image_url
                        if progress_callback:
                            progress_callback({"step": "使用备选图片", "progress": 77})
                        logger.info("最终呈现图片生成失败，使用鸡尾酒图片作为备选")
                except Exception as e:
                    logger.warning(f"最终呈现图片生成失败: {str(e)}")
                    # 使用鸡尾酒图片作为备选
                    final_presentation_image_url = cocktail_image_url
                    if progress_callback:
                        progress_callback({"step": "使用备选图片", "progress": 77})
            else:
                logger.info("图像服务不可用，跳过最终呈现图片生成")
            
            # 视频生成（可选，需要基础图片，如果失败不影响整体流程）
            # 注意：视频生成在图片生成之后，但在返回结果之前完成
            production_video_url = None
            if self.video_service and cocktail_image_url:
                try:
                    if progress_callback:
                        progress_callback({"step": "生成制作视频", "progress": 77})
                    logger.info(f"开始生成制作视频，基于图片: {cocktail_image_url}")
                    production_video_url = self._generate_production_video(
                        cocktail_name=cocktail_name,
                        cocktail_output=cocktail_output,
                        base_image_url=cocktail_image_url
                    )
                    if production_video_url:
                        logger.info(f"视频生成成功: {production_video_url}")
                        if progress_callback:
                            progress_callback({"step": "视频生成完成", "progress": 78})
                    else:
                        logger.info("视频生成返回None（跳过）")
                        if progress_callback:
                            progress_callback({"step": "跳过视频生成", "progress": 78})
                except Exception as e:
                    logger.warning(f"视频生成失败（可选功能）: {str(e)}")
                    # 视频生成失败不影响整体流程
                    if progress_callback:
                        progress_callback({"step": "视频生成跳过", "progress": 78})
            else:
                if not self.video_service:
                    logger.info("视频服务不可用，跳过视频生成")
                elif not cocktail_image_url:
                    logger.info("无基础图片，跳过视频生成")
                if progress_callback:
                    progress_callback({"step": "准备排版", "progress": 78})
            
            return PresentationOutput(
                cocktail_name=cocktail_name,
                name_candidates=name_candidates,
                production_video_url=production_video_url,
                cocktail_image_url=cocktail_image_url,
                final_presentation_image_url=final_presentation_image_url,
                user_response=semantic_output.response_text
            )
        except Exception as e:
            logger.error(f"呈现生成失败: {str(e)}")
            # 返回默认值
            import random
            fallbacks = ["夜雨初霁", "孤灯照影", "时光碎片", "浮生若梦", "烟火人间", "归途如虹"]
            return PresentationOutput(
                cocktail_name=random.choice(fallbacks),
                name_candidates=fallbacks[:5],
                production_video_url=None,
                cocktail_image_url=None,
                final_presentation_image_url=None,
                user_response=semantic_output.response_text
            )
    
    def _generate_cocktail_name(
        self,
        semantic_output: SemanticAnalysisOutput,
        cocktail_output: CocktailMixOutput
    ) -> tuple[str, List[str]]:
        """生成四字中文名"""
        try:
            prompt = f"""你是一位富有诗意的调酒师。请根据以下信息，为鸡尾酒创作一个四字中文名。

用户故事的情感：
- 情感需求：{', '.join(semantic_output.needs)}
- 细微情感：{', '.join(semantic_output.subtle_emotions)}
- 语调：{semantic_output.tone}
- 主题：{', '.join(semantic_output.themes)}

鸡尾酒信息：
- 名称：{cocktail_output.base_cocktail.name}
- 描述：{cocktail_output.customized_description}

重要要求（必须严格遵守）：
1. 四个字的中文名称
2. **绝对禁止使用"XX之酒"、"XX之饮"、"XX一杯"这类俗套格式！**
3. 禁止使用"心灵"、"情感"、"故事"这些被用烂的词
4. 具有极强的创意性和想象力，必须是前所未见的独特组合
5. 可以是诗意表达、文学隐喻、抽象概念、自然意象、哲学思考
6. 每个名称都要突破常规，具有强烈的个性和记忆点
7. 生成3-5个完全不同的创意候选名称

名称示例（参考风格，不要模仿）：
- "夜雨初霁" - 自然意象组合
- "孤灯照影" - 意境画面组合
- "时光碎片" - 抽象概念组合
- "浮生若梦" - 哲学思考组合

请以JSON格式输出：
{{
  "name": "选定的最佳名称",
  "candidates": ["候选名1", "候选名2", "候选名3", "候选名4", "候选名5"]
}}
"""
            response = self.llm_service.generate_sync(
                prompt=prompt,
                max_tokens=500,
                temperature=1.2,  # 使用更高的temperature（如果API支持），增强创意性
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response)
            name = result.get('name', '')
            candidates = result.get('candidates', [])
            
            # 验证名称，如果还是俗套名称则重新生成
            forbidden_patterns = ['之酒', '之饮', '一杯', '心灵', '情感', '故事']
            if any(pattern in name for pattern in forbidden_patterns):
                logger.warning(f"生成的名称 '{name}' 包含禁止模式，尝试使用候选名称")
                for candidate in candidates:
                    if not any(pattern in candidate for pattern in forbidden_patterns):
                        name = candidate
                        break
            
            # 如果还是没有合适的，生成随机备选
            if any(pattern in name for pattern in forbidden_patterns) or not name:
                import random
                fallbacks = ["夜雨初霁", "孤灯照影", "时光碎片", "浮生若梦", "烟火人间", "归途如虹"]
                name = random.choice(fallbacks)
                logger.warning(f"使用备选名称: {name}")
            
            return name, candidates
        except Exception as e:
            logger.error(f"名称生成失败: {str(e)}")
            import random
            fallbacks = ["夜雨初霁", "孤灯照影", "时光碎片", "浮生若梦", "烟火人间", "归途如虹"]
            return random.choice(fallbacks), fallbacks
    
    def _generate_production_video(
        self,
        cocktail_name: str,
        cocktail_output: CocktailMixOutput,
        base_image_url: str = None
    ) -> str:
        """生成制作动画视频"""
        if not self.video_service:
            return None
        try:
            prompt = f"A bartender's hands gracefully preparing a {cocktail_name} cocktail, mixing ingredients in a cocktail shaker, pouring into an elegant glass, cinematic lighting, smooth motion, professional bartending technique"
            
            # 使用Replicate Stable Video Diffusion生成视频
            # 需要基础图片URL，基于图片生成视频
            # 如果返回None，表示视频生成失败或不可用
            video_url = self.video_service.generate_video_sync(
                prompt=prompt,
                base_image_url=base_image_url
            )
            return video_url
        except Exception as e:
            logger.error(f"视频生成失败: {str(e)}")
            return None
    
    def _generate_cocktail_image(
        self,
        cocktail_name: str,
        cocktail_output: CocktailMixOutput
    ) -> Optional[str]:
        """生成鸡尾酒图片（优先级: DALL-E > Grok > Replicate）
        根据鸡尾酒的实际配方和特征生成真实的鸡尾酒照片
        """
        # 构建基于实际配方的详细提示词
        recipe = cocktail_output.customized_recipe
        description = cocktail_output.customized_description
        
        # 分析配方，提取关键视觉元素
        recipe_lower = recipe.lower()
        description_lower = description.lower()
        
        # 推断杯子类型
        glass_type = "elegant cocktail glass"
        if "martini" in recipe_lower or "martini" in description_lower:
            glass_type = "martini glass"
        elif "old fashioned" in recipe_lower or "rocks" in recipe_lower:
            glass_type = "old fashioned glass"
        elif "highball" in recipe_lower or "tall" in recipe_lower:
            glass_type = "highball glass"
        elif "champagne" in recipe_lower or "flute" in recipe_lower:
            glass_type = "champagne flute"
        
        # 根据配方详细分析鸡尾酒的颜色特征
        # 分析基础酒和调制剂的组合颜色
        base_colors = []
        modifier_colors = []
        
        # 基础酒颜色（按优先级匹配）
        if "dark rum" in recipe_lower:
            base_colors.append("deep golden amber")
        elif "rum" in recipe_lower:
            base_colors.append("golden amber or caramel")
        if "whiskey" in recipe_lower or "whisky" in recipe_lower or "bourbon" in recipe_lower or "scotch" in recipe_lower:
            base_colors.append("rich amber brown")
        if "gin" in recipe_lower:
            base_colors.append("crystal clear")
        if "vodka" in recipe_lower:
            base_colors.append("clear transparent")
        if "tequila" in recipe_lower:
            base_colors.append("crystal clear or pale golden")
        if "campari" in recipe_lower:
            base_colors.append("vibrant deep red")
        if "aperol" in recipe_lower:
            base_colors.append("vibrant orange-red")
        if "sweet vermouth" in recipe_lower:
            base_colors.append("amber red")
        elif "vermouth" in recipe_lower:
            base_colors.append("pale golden")
        
        # 调制剂颜色（可以多个）
        if "cola" in recipe_lower or "coca cola" in recipe_lower:
            modifier_colors.append("dark caramel brown")
        if "lemon" in recipe_lower or "lemon juice" in recipe_lower:
            modifier_colors.append("citrus yellow tint")
        if "lime" in recipe_lower or "lime juice" in recipe_lower:
            modifier_colors.append("citrus yellow-green tint")
        if "orange" in recipe_lower or "orange juice" in recipe_lower:
            modifier_colors.append("vibrant orange tint")
        if "cranberry" in recipe_lower or "cranberry juice" in recipe_lower:
            modifier_colors.append("deep red tint")
        if "grapefruit" in recipe_lower:
            modifier_colors.append("pink-red tint")
        if "sherry" in recipe_lower or "amontillado" in recipe_lower:
            modifier_colors.append("amber-golden depth")
        if "chocolate bitters" in recipe_lower or "chocolate" in recipe_lower or "cacao" in recipe_lower:
            modifier_colors.append("dark brown richness")
        if "tonic" in recipe_lower:
            modifier_colors.append("clear with subtle quinine yellow")
        if "bitters" in recipe_lower and "chocolate" not in recipe_lower:
            modifier_colors.append("aromatic brown depth")
        
        # 组合颜色描述（详细描述混合后的颜色）
        if base_colors and modifier_colors:
            # 多个调制剂时，描述组合效果
            if len(modifier_colors) > 1:
                modifiers = " and ".join(modifier_colors)
                color_desc = f"{base_colors[0]} mixed with {modifiers}, creating a rich and complex blended hue"
            else:
                color_desc = f"{base_colors[0]} mixed with {modifier_colors[0]}, creating a unique blended hue"
        elif base_colors:
            color_desc = base_colors[0]
            if "clear" in color_desc.lower() or "transparent" in color_desc.lower():
                color_desc += " with subtle natural tints"
        elif modifier_colors:
            if len(modifier_colors) > 1:
                color_desc = f"blended from {', '.join(modifier_colors)}, creating a vibrant mixture"
            else:
                color_desc = modifier_colors[0]
        else:
            # 如果无法识别，使用通用描述但强调颜色
            color_desc = "beautifully colored with rich natural tones"
        
        # 添加颜色深度和透明度描述
        if "cola" in recipe_lower or "dark rum" in recipe_lower or "chocolate" in recipe_lower:
            color_desc += " with rich, deep color depth and natural translucency"
        elif "clear" in color_desc.lower() or "transparent" in color_desc.lower():
            color_desc += " with subtle color tints and clarity"
        elif "vibrant" in color_desc.lower() or "red" in color_desc.lower() or "orange" in color_desc.lower():
            color_desc += " with bright color vibrancy"
        else:
            color_desc += " with natural color vibrancy and depth"
        
        # 推断装饰物
        garnish = ""
        if "lime" in recipe_lower:
            garnish = "with a fresh lime wheel or wedge"
        elif "lemon" in recipe_lower:
            garnish = "with a lemon twist or slice"
        elif "orange" in recipe_lower:
            garnish = "with an orange peel or slice"
        elif "mint" in recipe_lower:
            garnish = "with fresh mint leaves"
        elif "cherry" in recipe_lower:
            garnish = "with a maraschino cherry"
        
        # 构建详细的视觉描述提示词，以鸡尾酒为中心，手在后方
        # 推断高级酒杯类型
        premium_glass = "premium crystal glass"  # 默认高级水晶杯
        if "martini" in recipe_lower:
            premium_glass = "premium crystal martini glass"
        elif "old fashioned" in recipe_lower:
            premium_glass = "premium cut crystal old fashioned glass"
        elif "highball" in recipe_lower or "tall" in recipe_lower:
            premium_glass = "premium crystal highball glass with elegant design"
        elif "champagne" in recipe_lower or "flute" in recipe_lower:
            premium_glass = "premium crystal champagne flute"
        
        # 随机选择高级杯子类型（增加多样性）
        import random
        glass_styles = [
            "premium cut crystal glass with faceted edges",
            "sophisticated colored glass (amber, cobalt blue, or emerald green)",
            "premium borosilicate glass with elegant stem",
            "artisanal hand-blown glass with unique texture",
            "luxury crystal glass with intricate design patterns"
        ]
        if random.random() < 0.3:  # 30%概率使用有色玻璃
            premium_glass = random.choice(glass_styles)
        
        # 精简提示词，控制在1024字符以内
        accessories = f"straw, geometric ice cubes, decorative pick with {garnish.split()[-1] if garnish else 'fruit slices'}"
        
        prompt = f"""Premium {cocktail_name} cocktail, {color_desc}, in {premium_glass} on wooden bar. 
Bartender hands BEHIND glass, not blocking. Cocktail is center focus showing {color_desc} from recipe: {recipe}. 
Fresh drinkable beverage with realistic mixing. Accessories: {accessories}. 
Glass shows condensation, realistic bubbles. Hands visible in background, cocktail unobstructed. 
Professional food photography, soft lighting, shallow depth, photorealistic, 8k quality."""
        
        # 优先级1: 尝试DALL-E图片生成
        if self.dalle_image_service and self.dalle_image_service.available:
            try:
                logger.info("使用DALL-E图片生成服务生成鸡尾酒图片")
                image_url = self.dalle_image_service.generate_image_sync(prompt=prompt)
                if image_url:
                    return image_url
            except Exception as e:
                logger.warning(f"DALL-E图片生成失败: {str(e)}，尝试Grok")
        
        # 优先级2: 尝试Grok图片生成
        if self.grok_image_service and self.grok_image_service.available:
            try:
                logger.info("使用Grok图片生成服务生成鸡尾酒图片")
                image_url = self.grok_image_service.generate_image_sync(prompt=prompt, n=1)
                if image_url:
                    return image_url
            except Exception as e:
                logger.warning(f"Grok图片生成失败: {str(e)}，尝试Replicate")
        
        # 优先级3: 备选使用Replicate（如果可用）
        if self.image_service and self.image_service.client is not None:
            try:
                logger.info("使用Replicate图片生成服务生成鸡尾酒图片")
                image_url = self.image_service.generate_image_sync(
                    prompt=prompt,
                    width=1024,
                    height=1024
                )
                return image_url
            except Exception as e:
                logger.error(f"Replicate鸡尾酒图片生成失败: {str(e)}")
        
        logger.warning("所有图片生成服务都不可用，跳过鸡尾酒图片生成")
        return None
    
    def _generate_final_presentation_image(
        self,
        cocktail_name: str,
        cocktail_output: CocktailMixOutput
    ) -> Optional[str]:
        """生成最终呈现图片（酒保手部特写，优先级: DALL-E > Grok > Replicate）
        展示真实的鸡尾酒，而不是文字设计
        """
        recipe = cocktail_output.customized_recipe
        recipe_lower = recipe.lower()
        
        # 推断高级酒杯类型
        premium_glass = "premium crystal glass"
        if "martini" in recipe_lower:
            premium_glass = "premium crystal martini glass"
        elif "old fashioned" in recipe_lower:
            premium_glass = "premium cut crystal old fashioned glass"
        elif "highball" in recipe_lower or "tall" in recipe_lower:
            premium_glass = "premium crystal highball glass with elegant design"
        
        import random
        glass_styles = [
            "premium cut crystal glass with faceted edges",
            "sophisticated colored glass (amber, cobalt blue, or emerald green)",
            "premium borosilicate glass with elegant stem"
        ]
        if random.random() < 0.3:
            premium_glass = random.choice(glass_styles)
        
        # 推断装饰物
        garnish_desc = ""
        if "lime" in recipe_lower:
            garnish_desc = "lime wheel on decorative pick"
        elif "lemon" in recipe_lower:
            garnish_desc = "lemon twist and slice on decorative pick"
        elif "orange" in recipe_lower:
            garnish_desc = "orange slice and peel on decorative pick"
        elif "mint" in recipe_lower:
            garnish_desc = "fresh mint leaves and fruit slice on decorative pick"
        elif "cherry" in recipe_lower:
            garnish_desc = "maraschino cherry and citrus slice on decorative pick"
        else:
            garnish_desc = "elegant fruit slices on decorative cocktail pick"
        
        # 精简提示词，控制在1024字符以内
        accessories = f"thin straw, geometric ice, decorative pick with {garnish_desc.split('on')[0] if 'on' in garnish_desc else garnish_desc}"
        
        prompt = f"""Premium {cocktail_name} cocktail as central focus in {premium_glass} on wooden bar. 
Hands BEHIND glass, never blocking. Cocktail shows realistic color from recipe: {recipe}. 
Fresh drinkable beverage. Accessories: {accessories}. 
Glass shows luxury design. Hands in background create depth. 
Close-up, cocktail prominent. Warm lighting, shallow depth, professional food photography, photorealistic, 8k."""
        
        # 优先级1: 尝试DALL-E图片生成
        if self.dalle_image_service and self.dalle_image_service.available:
            try:
                logger.info("使用DALL-E图片生成服务生成最终呈现图片")
                image_url = self.dalle_image_service.generate_image_sync(prompt=prompt)
                if image_url:
                    return image_url
            except Exception as e:
                logger.warning(f"DALL-E图片生成失败: {str(e)}，尝试Grok")
        
        # 优先级2: 尝试Grok图片生成
        if self.grok_image_service and self.grok_image_service.available:
            try:
                logger.info("使用Grok图片生成服务生成最终呈现图片")
                image_url = self.grok_image_service.generate_image_sync(prompt=prompt, n=1)
                if image_url:
                    return image_url
            except Exception as e:
                logger.warning(f"Grok图片生成失败: {str(e)}，尝试Replicate")
        
        # 优先级3: 备选使用Replicate（如果可用）
        if self.image_service and self.image_service.client is not None:
            try:
                logger.info("使用Replicate图片生成服务生成最终呈现图片")
                image_url = self.image_service.generate_image_sync(
                    prompt=prompt,
                    width=1024,
                    height=1024
                )
                return image_url
            except Exception as e:
                logger.error(f"Replicate最终呈现图片生成失败: {str(e)}")
        
        logger.warning("所有图片生成服务都不可用，跳过最终呈现图片生成")
        return None
