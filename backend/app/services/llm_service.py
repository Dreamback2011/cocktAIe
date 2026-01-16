import os
from typing import List, Dict, Any, Optional
import json
import logging
import httpx

logger = logging.getLogger(__name__)


class LLMService:
    """LLM服务 - 支持 Grok (xAI) 和 OpenAI"""
    
    def __init__(self, model: str = None):
        # 优先使用Grok API
        grok_key = os.getenv("GROK_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if grok_key:
            self.api_type = "grok"
            self.api_key = grok_key
            self.base_url = "https://api.x.ai/v1"
            self.model = model or "grok-2-1212"  # 使用最新的grok模型
            logger.info("使用 Grok (xAI) API")
        elif openai_key:
            try:
                from openai import OpenAI
                self.api_type = "openai"
                self.api_key = openai_key
                self.client = OpenAI(api_key=openai_key)
                self.model = model or "gpt-4o"
                logger.info("使用 OpenAI API")
            except ImportError:
                raise ValueError("OpenAI库未安装，且未配置GROK_API_KEY")
        else:
            raise ValueError("必须设置GROK_API_KEY或OPENAI_API_KEY环境变量")
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        response_format: Optional[Dict[str, str]] = None
    ) -> str:
        """
        调用LLM生成文本（支持Grok和OpenAI）
        
        Args:
            prompt: 提示词
            max_tokens: 最大token数
            temperature: 温度参数
            response_format: 响应格式（如{"type": "json_object"}）
        
        Returns:
            生成的文本
        """
        return self.generate_sync(prompt, max_tokens, temperature, response_format)
    
    def generate_sync(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        response_format: Optional[Dict[str, str]] = None
    ) -> str:
        """同步版本的生成"""
        try:
            messages = [{"role": "user", "content": prompt}]
            
            if self.api_type == "grok":
                # 使用Grok API
                return self._call_grok_api(messages, max_tokens, temperature, response_format)
            else:
                # 使用OpenAI API
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }
                if response_format:
                    kwargs["response_format"] = response_format
                
                response = self.client.chat.completions.create(**kwargs)
                return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            logger.error(f"LLM生成失败: {error_msg}")
            raise Exception(f"LLM生成失败: {error_msg}")
    
    def _call_grok_api(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        response_format: Optional[Dict[str, str]] = None
    ) -> str:
        """调用Grok API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        # Grok API 可能支持 response_format，但需要验证
        if response_format:
            payload["response_format"] = response_format
        
        url = f"{self.base_url}/chat/completions"
        
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # Grok API 响应格式与OpenAI兼容
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            elif "content" in result:
                # 可能直接返回content
                return result["content"]
            else:
                raise Exception(f"意外的响应格式: {result}")
    
    def generate_json(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        生成JSON格式的响应
        
        Args:
            prompt: 提示词
            max_tokens: 最大token数
            temperature: 温度参数
        
        Returns:
            解析后的JSON字典
        """
        response = self.generate_sync(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            response_format={"type": "json_object"}
        )
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}, 响应: {response}")
            raise Exception(f"JSON解析失败: {str(e)}")


# 全局服务实例
_llm_service_instance: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """获取全局LLM服务实例"""
    global _llm_service_instance
    if _llm_service_instance is None:
        _llm_service_instance = LLMService()
    return _llm_service_instance
