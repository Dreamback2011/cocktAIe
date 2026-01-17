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
                progress_callback({
                    "step": "生成鸡尾酒名称",
                    "progress": 65,
                    "details": {
                        "text_generation": {"status": "in_progress", "progress": 30, "step": "生成名称中..."}
                    }
                })
            cocktail_name, name_candidates = self._generate_cocktail_name(
                semantic_output=semantic_output,
                cocktail_output=cocktail_output
            )
            logger.info(f"生成鸡尾酒名称: {cocktail_name}")
            if progress_callback:
                progress_callback({
                    "step": "鸡尾酒名称生成完成",
                    "progress": 67,
                    "details": {
                        "text_generation": {"status": "completed", "progress": 100, "step": "名称已生成", "result": cocktail_name}
                    }
                })
            
            # 只生成一张图片（使用最终呈现图片标准）
            cocktail_image_url = None
            final_presentation_image_url = None
            
            # 检查是否有任何可用的图片服务
            has_image_service = (
                (self.dalle_image_service and self.dalle_image_service.available) or
                (self.grok_image_service and self.grok_image_service.available) or
                (self.image_service and self.image_service.client is not None)
            )
            
            if has_image_service:
                try:
                    if progress_callback:
                        progress_callback({
                            "step": "正在生成鸡尾酒图片（可能需要15-20秒）...",
                            "progress": 70,
                            "details": {
                                "image_generation": {
                                    "status": "in_progress",
                                    "progress": 10,
                                    "step": "生成鸡尾酒图片中...",
                                    "cocktail_image": "in_progress",
                                    "final_image": "in_progress"  # 使用同一张图片
                                }
                            }
                        })
                    logger.info("开始生成鸡尾酒图片（使用最终呈现图片标准，基于recipe）...")
                    
                    # Checker 4: 图片生成中（调配中）- 基于recipe生成
                    if progress_callback:
                        progress_callback({
                            "step": "正在生成鸡尾酒图片（基于recipe）...",
                            "progress": 73,
                            "details": {
                                "image_generation": {
                                    "status": "in_progress",
                                    "progress": 20,
                                    "step": "基于recipe准备图片生成...",
                                    "cocktail_image": "in_progress",
                                    "final_image": "in_progress"
                                }
                            }
                        })
                    
                    # 只生成一张图片，使用最终呈现图片的标准（使用cocktail_output.customized_recipe）
                    final_presentation_image_url = self._generate_final_presentation_image(
                        cocktail_name=cocktail_name,
                        cocktail_output=cocktail_output
                    )
                    
                    # 生成过程中更新进度
                    if progress_callback:
                        if final_presentation_image_url:
                            # Checker 5: 图片生成完毕
                            progress_callback({
                                "step": "图片生成完成",
                                "progress": 77,
                                "details": {
                                    "image_generation": {
                                        "status": "in_progress",
                                        "progress": 80,
                                        "step": "图片已生成，准备排版...",
                                        "cocktail_image": "completed",
                                        "final_image": "completed"
                                    }
                                }
                            })
                        else:
                            progress_callback({
                                "step": "图片生成失败",
                                "progress": 77,
                                "details": {
                                    "image_generation": {
                                        "status": "failed",
                                        "progress": 0,
                                        "step": "图片生成失败",
                                        "cocktail_image": "failed",
                                        "final_image": "failed"
                                    }
                                }
                            })
                    
                    # 使用同一张图片填充两个字段
                    if final_presentation_image_url:
                        cocktail_image_url = final_presentation_image_url  # 使用同一张图片
                        if progress_callback:
                            progress_callback({
                                "step": "图片生成完成",
                                "progress": 77,
                                "details": {
                                    "image_generation": {
                                        "status": "completed",
                                        "progress": 100,
                                        "step": "图片已生成完成",
                                        "cocktail_image": "completed",
                                        "final_image": "completed"
                                    }
                                }
                            })
                        logger.info(f"图片生成成功: {final_presentation_image_url}")
                    else:
                        if progress_callback:
                            progress_callback({
                                "step": "图片生成失败",
                                "progress": 77,
                                "details": {
                                    "image_generation": {
                                        "status": "failed",
                                        "progress": 0,
                                        "step": "图片生成失败",
                                        "cocktail_image": "failed",
                                        "final_image": "failed"
                                    }
                                }
                            })
                        logger.warning("图片生成返回None")
                except Exception as e:
                    logger.warning(f"图片生成失败: {str(e)}")
                    if progress_callback:
                        progress_callback({
                            "step": "图片生成失败，继续处理",
                            "progress": 77,
                            "details": {
                                "image_generation": {
                                    "status": "failed",
                                    "progress": 0,
                                    "step": f"图片生成失败: {str(e)[:50]}...",
                                    "cocktail_image": "failed",
                                    "final_image": "failed"
                                }
                            }
                        })
            else:
                logger.info("图像服务不可用，跳过图片生成")
                if progress_callback:
                    progress_callback({
                        "step": "跳过图片生成（服务不可用）",
                        "progress": 77,
                        "details": {
                            "image_generation": {
                                "status": "failed",
                                "progress": 0,
                                "step": "图片服务不可用",
                                "cocktail_image": "failed",
                                "final_image": "failed"
                            }
                        }
                    })
            
            # 视频生成（可选，需要基础图片，如果失败不影响整体流程）
            # 注意：视频生成在图片生成之后，但在返回结果之前完成
            production_video_url = None
            if self.video_service and final_presentation_image_url:  # 使用最终呈现图片
                try:
                    if progress_callback:
                        progress_callback({"step": "生成制作视频", "progress": 77})
                    logger.info(f"开始生成制作视频，基于图片: {final_presentation_image_url}")
                    production_video_url = self._generate_production_video(
                        cocktail_name=cocktail_name,
                        cocktail_output=cocktail_output,
                        base_image_url=final_presentation_image_url  # 使用最终呈现图片
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
                elif not final_presentation_image_url:
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
            # 视频生成也不包含酒名
            prompt = "A bartender's hands gracefully preparing a cocktail, mixing ingredients in a cocktail shaker, pouring into an elegant glass, cinematic lighting, smooth motion, professional bartending technique"
            
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
        """生成鸡尾酒图片（使用与最终呈现图片相同的标准）
        所有关于酒的图片都按照最终呈现图片的标准生成，不包含酒名
        """
        # 直接使用与最终呈现图片相同的生成逻辑，确保统一标准
        return self._generate_final_presentation_image(
            cocktail_name=cocktail_name,  # 虽然不传入prompt，但保留参数签名
            cocktail_output=cocktail_output
        )
    
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
            "premium borosilicate glass with elegant stem",
            "hand-blown artisanal glass with unique texture",
            "luxury crystal martini glass with gold rim",
            "modern geometric glass with clean lines",
            "vintage-inspired glass with decorative etching"
        ]
        # 增加使用有色/特殊玻璃的概率到50%，提高视觉多样性
        if random.random() < 0.5:
            premium_glass = random.choice(glass_styles)
        
        # 增加装饰物多样性，避免总是橙色+橘子切片
        garnish_options = []
        
        # 根据配方推断可能的装饰物
        if "lime" in recipe_lower:
            garnish_options.extend([
                "lime wheel on decorative pick",
                "lime wedge with fresh mint",
                "lime zest twist",
                "thin lime slice floating"
            ])
        if "lemon" in recipe_lower:
            garnish_options.extend([
                "lemon twist and slice on decorative pick",
                "lemon peel spiral",
                "lemon wheel with fresh herbs",
                "candied lemon slice"
            ])
        if "orange" in recipe_lower:
            garnish_options.extend([
                "orange slice and peel on decorative pick",
                "orange zest curl",
                "candied orange peel",
                "fresh orange wheel"
            ])
        if "mint" in recipe_lower:
            garnish_options.extend([
                "fresh mint leaves and fruit slice on decorative pick",
                "mint sprig bouquet",
                "muddled mint with berries",
                "fresh mint crown"
            ])
        if "cherry" in recipe_lower:
            garnish_options.extend([
                "maraschino cherry and citrus slice on decorative pick",
                "brandied cherry with stem",
                "fresh cherry with lime twist",
                "cherry and orange flag"
            ])
        if "berry" in recipe_lower or "cranberry" in recipe_lower:
            garnish_options.extend([
                "fresh berries on decorative pick",
                "cranberry and lime wheel",
                "mixed berry skewer",
                "raspberry and mint"
            ])
        if "herb" in recipe_lower or "basil" in recipe_lower or "rosemary" in recipe_lower:
            garnish_options.extend([
                "fresh herb sprig",
                "herb bouquet",
                "herb and citrus twist"
            ])
        
        # 如果没有特定装饰物，随机选择通用装饰物
        if not garnish_options:
            garnish_options = [
                "elegant fruit slice on decorative cocktail pick",
                "fresh citrus twist",
                "herb sprig with berries",
                "decorative edible flower",
                "candied fruit peel",
                "fresh mint sprig",
                "simple lemon twist",
                "berry and mint garnish"
            ]
        
        # 随机选择装饰物（增加多样性）
        garnish_desc = random.choice(garnish_options)
        
        # 精简提示词，控制在1024字符以内
        accessories = f"thin straw, geometric ice, {garnish_desc}"
        
        # 最终呈现图片标准（简洁、特写、不包含酒名）
        prompt = f"""Premium cocktail as central focus in {premium_glass} on wooden bar. 
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
