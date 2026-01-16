from typing import Dict, Any
from app.services.llm_service import get_llm_service
from app.models.schemas import LayoutOutput, SemanticAnalysisOutput, PresentationOutput
from PIL import Image, ImageDraw, ImageFont
import httpx
from io import BytesIO
import os
import logging

logger = logging.getLogger(__name__)


class LayoutAgent:
    """排版Agent - 将呈现Agent的输出排版成精美的名片卡片"""
    
    def __init__(self):
        self.llm_service = get_llm_service()
    
    def create_card(
        self,
        cocktail_name: str,
        semantic_output: SemanticAnalysisOutput,
        presentation_output: PresentationOutput,
        output_dir: str = "generated_cards"
    ) -> LayoutOutput:
        """
        创建名片卡片
        
        Args:
            cocktail_name: 鸡尾酒名称
            semantic_output: 语义分析输出
            presentation_output: 呈现输出
            output_dir: 输出目录
        
        Returns:
            LayoutOutput: 排版结果
        """
        try:
            # 步骤1：文本简化
            simplified_response = self._simplify_response(
                response_text=semantic_output.response_text
            )
            
            # 步骤2：等待图片完全加载（确保图片URL可用）
            # 优先使用鸡尾酒图片，如果没有则使用最终呈现图片
            source_image_url = presentation_output.cocktail_image_url or presentation_output.final_presentation_image_url
            
            if not source_image_url:
                logger.warning("没有可用的图片URL，等待图片生成完成...")
                # 如果图片还在生成中，这里可以等待或使用占位符
                # 但为了流程顺畅，我们继续使用空值，稍后在_design_card中处理
            
            # 验证图片URL是否可访问（如果提供）- 使用GET请求确保图片完全加载
            if source_image_url:
                try:
                    logger.info(f"开始验证图片URL可访问性: {source_image_url}")
                    with httpx.Client(timeout=30.0) as client:  # 增加超时时间
                        # 使用GET请求下载图片头部，确保图片真的可用
                        response = client.get(source_image_url, follow_redirects=True)
                        if response.status_code != 200:
                            logger.warning(f"图片URL不可访问: {source_image_url} (状态码: {response.status_code})")
                            source_image_url = None
                        else:
                            # 验证响应内容确实是图片
                            content_type = response.headers.get('content-type', '')
                            if 'image' not in content_type.lower():
                                logger.warning(f"URL返回的不是图片: {content_type}")
                                source_image_url = None
                            else:
                                # 验证图片数据不为空
                                if len(response.content) < 100:  # 图片太小可能是错误页面
                                    logger.warning(f"图片数据异常小: {len(response.content)} 字节")
                                    source_image_url = None
                                else:
                                    logger.info(f"图片URL验证成功: {source_image_url} (大小: {len(response.content)} 字节, 类型: {content_type})")
                except httpx.TimeoutException:
                    logger.warning(f"图片URL验证超时: {source_image_url}，可能图片还在生成中")
                    source_image_url = None
                except Exception as e:
                    logger.warning(f"图片URL验证失败: {str(e)}，将使用空图片")
                    source_image_url = None
            
            # 步骤3：直接使用生成的图片（不进行风格转换）
            # 确保图片已完全加载后再进行排版
            image_url_for_card = source_image_url
            if not source_image_url:
                logger.warning("没有可用图片，将生成纯文字名片")
            else:
                logger.info(f"使用生成的图片进行排版: {image_url_for_card}")
            
            # 步骤4：名片卡片设计（确保图片URL可用且已完全加载）
            os.makedirs(output_dir, exist_ok=True)
            card_url = self._design_card(
                cocktail_name=cocktail_name,
                simplified_response=simplified_response,
                image_url_for_card=image_url_for_card,
                output_dir=output_dir
            )
            
            # 确保final_card_url不为空，使用备选图片URL
            final_url = card_url if card_url else (image_url_for_card or presentation_output.final_presentation_image_url or presentation_output.cocktail_image_url or "")
            logger.info(f"Layout输出 - final_card_url: {final_url}, image_url: {image_url_for_card or '无'}")
            
            return LayoutOutput(
                simplified_response=simplified_response,
                ink_style_image_url=image_url_for_card or presentation_output.final_presentation_image_url or "",  # 保留字段名，但存储原始图片URL
                final_card_url=final_url
            )
        except Exception as e:
            logger.error(f"排版生成失败: {str(e)}")
            # 返回默认值，使用备选图片URL
            simplified = simplified_response if 'simplified_response' in locals() else "感谢分享。"
            fallback_image_url = image_url_for_card if 'image_url_for_card' in locals() else (presentation_output.final_presentation_image_url or presentation_output.cocktail_image_url or "")
            return LayoutOutput(
                simplified_response=simplified,
                ink_style_image_url=fallback_image_url,  # 保留字段名，但存储原始图片URL
                final_card_url=fallback_image_url  # 使用备选图片作为final_card_url
            )
    
    def _simplify_response(self, response_text: str) -> str:
        """将300字回复简化为2句话，叙事性，避免主语"""
        try:
            prompt = f"""请将以下回复文本简化为2句话，每句话不超过30字。

要求：
1. 采用叙事性表达，避免使用"你"、"我"、"我们"等主语
2. 用第三人称或客观描述的方式表达
3. 保持原有情感和正面支持的语气
4. 保留核心安慰、理解和助兴的内容
5. 每句话完整且有意义，具有故事感和画面感
6. 用中文输出，直接用两句话，不需要编号

示例风格：
- "异乡的路途虽然漫长，但每一次的驻足都是成长的痕迹。"
- "漂泊的灵魂终会在某个转角找到属于自己的温暖。"
- "孤独不是终点，而是与自己对话的开始。"

原文：
{response_text}

简化后的两句话（叙事性，无主语）："""
            
            simplified = self.llm_service.generate_sync(
                prompt=prompt,
                max_tokens=200,
                temperature=0.7
            )
            
            # 清理输出，移除可能的编号和多余空白
            simplified = simplified.strip()
            # 移除所有句号，然后重新添加
            simplified = simplified.replace('。', '').replace('.', '')
            lines = [line.strip() for line in simplified.split('\n') if line.strip()]
            
            # 取前两句，每句只加一个句号
            if len(lines) >= 2:
                # 确保每句末尾只有一个句号
                line1 = lines[0].rstrip('。').rstrip('.') + '。'
                line2 = lines[1].rstrip('。').rstrip('.') + '。'
                return line1 + line2
            elif len(lines) == 1:
                # 单句也确保只有一个句号
                return lines[0].rstrip('。').rstrip('.') + '。'
            else:
                # 如果没有分行，尝试按句号分割
                parts = simplified.split('。')
                parts = [p.strip() for p in parts if p.strip()]
                if len(parts) >= 2:
                    return parts[0] + '。' + parts[1] + '。'
                elif len(parts) == 1:
                    return parts[0] + '。'
                else:
                    return simplified.rstrip('。').rstrip('.') + '。'
        except Exception as e:
            logger.error(f"文本简化失败: {str(e)}")
            return response_text[:60] + "..."  # 简单截取
    
    def _design_card(
        self,
        cocktail_name: str,
        simplified_response: str,
        image_url_for_card: str,
        output_dir: str
    ) -> str:
        """设计名片卡片"""
        try:
            # 名片尺寸：90mm x 54mm，约1063 x 638像素（300 DPI）
            card_width = 1063
            card_height = 638
            
            # 创建卡片图像
            card = Image.new('RGB', (card_width, card_height), color='white')
            draw = ImageDraw.Draw(card)
            
            # 计算左右分界（左半部分：图片，右半部分：文字）
            left_width = card_width // 2  # 左半部分宽度
            right_width = card_width - left_width  # 右半部分宽度
            right_start = left_width  # 右半部分起始位置
            
            # 加载并放置图片（左半部分）- 确保图片完全加载后再排版
            if image_url_for_card:
                try:
                    logger.info(f"开始加载图片用于排版: {image_url_for_card}")
                    with httpx.Client(timeout=30.0) as client:  # 增加超时时间
                        response = client.get(image_url_for_card, follow_redirects=True)
                        if response.status_code == 200:
                            # 验证内容类型
                            content_type = response.headers.get('content-type', '')
                            if 'image' not in content_type.lower():
                                raise Exception(f"URL返回的不是图片: {content_type}")
                            
                            # 验证图片数据
                            image_data = response.content
                            if len(image_data) < 100:
                                raise Exception(f"图片数据异常小: {len(image_data)} 字节")
                            
                            # 尝试打开图片
                            bg_image = Image.open(BytesIO(image_data))
                            # 验证图片格式
                            bg_image.verify()  # 验证图片完整性
                            bg_image = Image.open(BytesIO(image_data))  # 重新打开（verify后需要重新打开）
                            
                            # 调整图片大小以适应左半部分
                            bg_image = bg_image.resize((left_width, card_height), Image.Resampling.LANCZOS)
                            card.paste(bg_image, (0, 0))
                            logger.info(f"图片加载成功并应用到名片左侧: {len(image_data)} 字节")
                        else:
                            raise Exception(f"HTTP状态码: {response.status_code}")
                except httpx.TimeoutException:
                    logger.error(f"图片加载超时: {image_url_for_card}，图片可能还在生成中，使用占位背景")
                    # 左半部分用浅色背景
                    draw.rectangle([(0, 0), (left_width, card_height)], fill=(245, 245, 245))
                except Exception as e:
                    logger.error(f"加载图片失败: {str(e)}，左半部分使用纯色背景")
                    # 左半部分用浅色背景
                    draw.rectangle([(0, 0), (left_width, card_height)], fill=(245, 245, 245))
            else:
                logger.warning("没有图片URL，左半部分使用纯色背景")
                # 如果没有图片，左半部分用浅色背景
                draw.rectangle([(0, 0), (left_width, card_height)], fill=(245, 245, 245))
            
            # 右半部分背景（白色或浅色）
            draw.rectangle([(right_start, 0), (card_width, card_height)], fill=(255, 255, 255))
            
            # 尝试加载中文字体（优先钢笔书法字体）
            font_large = None
            font_medium = None
            
            # 尝试加载钢笔书法字体（Windows常见路径）
            calligraphy_fonts = [
                "C:/Windows/Fonts/STXINGKA.TTF",  # 华文行楷
                "C:/Windows/Fonts/STKAITI.TTF",   # 华文楷体
                "C:/Windows/Fonts/STLITI.TTF",    # 华文隶书
                "C:/Windows/Fonts/FZSTK.TTF",     # 方正舒体
                "C:/Windows/Fonts/FZXINGK.TTF",   # 方正行楷
            ]
            
            for font_path in calligraphy_fonts:
                try:
                    if os.path.exists(font_path):
                        font_large = ImageFont.truetype(font_path, 72)
                        font_medium = ImageFont.truetype(font_path, 32)
                        logger.info(f"使用钢笔书法字体: {font_path}")
                        break
                except:
                    continue
            
            # 如果没有找到书法字体，使用系统默认中文字体
            if font_large is None:
                try:
                    # Windows系统字体路径
                    font_large = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 72)
                    font_medium = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 32)
                    logger.info("使用黑体字体")
                except:
                    try:
                        # macOS系统字体路径
                        font_large = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 72)
                        font_medium = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 32)
                    except:
                        # 使用默认字体
                        font_large = ImageFont.load_default()
                        font_medium = ImageFont.load_default()
                        logger.warning("使用默认字体（可能不支持中文）")
            
            # 绘制鸡尾酒名称（右半部分，垂直居中偏上）
            name_bbox = draw.textbbox((0, 0), cocktail_name, font=font_large)
            name_width = name_bbox[2] - name_bbox[0]
            name_x = right_start + (right_width - name_width) // 2  # 右半部分居中
            name_y = card_height // 3  # 垂直位置约在1/3处
            draw.text((name_x, name_y), cocktail_name, fill='black', font=font_large)
            
            # 绘制简化的回复（右半部分，名称下方）
            # 计算文本区域（右半部分，名称下方）
            text_area_start_y = card_height // 2  # 从垂直中点开始
            text_margin_x = 40  # 左右边距（增大边距）
            max_text_width = right_width - text_margin_x * 2  # 最大文本宽度
            text_area_height = card_height - text_area_start_y - 50  # 可用高度
            
            # 智能文本换行函数
            def wrap_text(text, font, max_width):
                """将文本按宽度自动换行"""
                words = text.replace('。', '。\n').split('\n')  # 先按句号分割
                lines = []
                for word in words:
                    if not word.strip():
                        continue
                    # 测量文本宽度
                    bbox = draw.textbbox((0, 0), word, font=font)
                    word_width = bbox[2] - bbox[0]
                    
                    if word_width <= max_width:
                        lines.append(word.strip())
                    else:
                        # 文本太长，需要进一步分割
                        chars = list(word)
                        current_line = ""
                        for char in chars:
                            test_line = current_line + char
                            test_bbox = draw.textbbox((0, 0), test_line, font=font)
                            test_width = test_bbox[2] - test_bbox[0]
                            if test_width > max_width and current_line:
                                lines.append(current_line)
                                current_line = char
                            else:
                                current_line = test_line
                        if current_line:
                            lines.append(current_line)
                return lines
            
            # 处理文本，自动换行
            text_lines = wrap_text(simplified_response, font_medium, max_text_width)
            
            # 限制行数（最多3行）
            if len(text_lines) > 3:
                text_lines = text_lines[:3]
            
            # 计算每行间距
            line_height = 45  # 行高
            total_text_height = len(text_lines) * line_height
            start_y = text_area_start_y + (text_area_height - total_text_height) // 2  # 垂直居中
            
            # 绘制文本（每行居中）
            for i, line in enumerate(text_lines):
                if not line.strip():
                    continue
                bbox = draw.textbbox((0, 0), line, font=font_medium)
                line_width = bbox[2] - bbox[0]
                line_x = right_start + (right_width - line_width) // 2  # 每行居中
                line_y = start_y + i * line_height
                draw.text((line_x, line_y), line.strip(), fill='black', font=font_medium)
            
            # 保存卡片
            import uuid
            card_filename = f"card_{uuid.uuid4().hex[:8]}.png"
            card_path = os.path.join(output_dir, card_filename)
            card.save(card_path, 'PNG', dpi=(300, 300))
            
            # 返回文件路径（实际部署时应该返回URL）
            card_url = f"/generated_cards/{card_filename}"
            logger.info(f"名片卡片生成成功: {card_url} (文件路径: {card_path})")
            return card_url
        except Exception as e:
            logger.error(f"卡片设计失败: {str(e)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return ""  # 返回空字符串，调用方会使用备选URL
