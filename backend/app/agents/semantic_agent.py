from typing import Dict, Any, List
from app.services.llm_service import get_llm_service
from app.models.schemas import SemanticAnalysisOutput
import json
import logging

logger = logging.getLogger(__name__)


class SemanticAgent:
    """语义分析Agent - 分析用户故事并输出三个维度的结果"""
    
    def __init__(self):
        self.llm_service = get_llm_service()
    
    def analyze(self, user_story: str) -> SemanticAnalysisOutput:
        """
        分析用户故事
        
        Args:
            user_story: 用户输入的故事文本
        
        Returns:
            SemanticAnalysisOutput: 包含三个输出的分析结果
        """
        try:
            # 构建prompt
            prompt = self._build_analysis_prompt(user_story)
            
            # 调用GPT-4进行分析
            response = self.llm_service.generate_sync(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            # 解析JSON响应
            analysis_result = json.loads(response)
            
            # 构建输出对象
            return SemanticAnalysisOutput(
                energy=analysis_result.get("energy", 3),
                tension=analysis_result.get("tension", 3),
                control=analysis_result.get("control", 3),
                needs=analysis_result.get("needs", []),
                response_text=analysis_result.get("response_text", ""),
                subtle_emotions=analysis_result.get("subtle_emotions", []),
                tone=analysis_result.get("tone", ""),
                themes=analysis_result.get("themes", [])
            )
        except Exception as e:
            logger.error(f"语义分析失败: {str(e)}")
            # 返回默认值
            return SemanticAnalysisOutput(
                energy=3,
                tension=3,
                control=3,
                needs=["comfort", "understanding", "support"],
                response_text="感谢你分享你的故事。",
                subtle_emotions=[],
                tone="中性",
                themes=[]
            )
    
    def _build_analysis_prompt(self, user_story: str) -> str:
        """构建语义分析的prompt"""
        prompt = f"""你是一个专业的情感分析专家。请分析以下用户故事，并输出JSON格式的分析结果。

用户故事：
{user_story}

请按照以下要求分析：

1. **输出1 - 四维度分析**：
   - energy: 能量维度（1-5整数，1表示低能量/疲惫，5表示高能量/兴奋）
   - tension: 紧张度（1-5整数，1表示放松，5表示高度紧张/焦虑）
   - control: 控制感（1-5整数，1表示失控/无力，5表示完全掌控）
   - needs: 三种情感需求（字符串数组，如：["comfort", "understanding", "support"]）

2. **输出2 - 300字回复**：
   - response_text: 针对用户故事给出正面、支持、安慰、助兴、理解的回复（300字以内，中文）

3. **输出3 - 细微情感分析**：
   - subtle_emotions: 细微的情感关键词列表（3-5个关键词）
   - tone: 整体语调描述（如：温和、积极、沉思等）
   - themes: 故事主题列表（2-3个主题词）

请确保输出严格的JSON格式，示例：
{{
  "energy": 3,
  "tension": 4,
  "control": 2,
  "needs": ["comfort", "understanding", "warmth"],
  "response_text": "感谢你分享这段经历...",
  "subtle_emotions": ["nostalgia", "yearning", "hope"],
  "tone": "温和而深沉",
  "themes": ["回忆", "成长"]
}}
"""
        return prompt
