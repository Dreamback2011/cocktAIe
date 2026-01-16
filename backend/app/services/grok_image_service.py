"""
Grok图片生成服务
使用xAI的Grok-2-Image模型进行图片生成
"""
import os
import httpx
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class GrokImageService:
    """Grok图片生成服务（通过xAI API）"""

    def __init__(self):
        self.grok_api_key = os.getenv("GROK_API_KEY")
        self.grok_base_url = os.getenv("GROK_API_BASE", "https://api.x.ai/v1")
        # 尝试多个可能的模型名称
        self.model = os.getenv("GROK_IMAGE_MODEL", "grok-2-image-1212")  # 默认使用完整模型名
        
        if not self.grok_api_key:
            logger.warning("GROK_API_KEY环境变量未设置，图片生成功能将不可用")
            self.available = False
        else:
            self.available = True
            logger.info(f"GrokImageService初始化成功，模型: {self.model}")

    def generate_image_sync(
        self,
        prompt: str,
        n: int = 1,
        response_format: str = "url",
        timeout: int = 120
    ) -> Optional[str]:
        """
        同步生成图片
        
        Args:
            prompt: 图片描述提示词
            n: 生成图片数量（1-10）
            response_format: 返回格式，"url" 或 "b64_json"
            timeout: 请求超时时间（秒）
        
        Returns:
            图片URL（如果response_format="url"）或None
        """
        if not self.available:
            logger.warning("Grok图片生成服务不可用，跳过图片生成")
            return None

        if n > 10:
            n = 10
            logger.warning(f"图片数量超过10，已调整为10")
        elif n < 1:
            n = 1

        try:
            logger.info(f"开始使用Grok生成图片: {prompt[:50]}...")
            
            headers = {
                "Authorization": f"Bearer {self.grok_api_key}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "image_format": response_format,
                "n": n
            }
            
            # 调用Grok图片生成API
            with httpx.Client(timeout=timeout) as client:
                response = client.post(
                    f"{self.grok_base_url}/images/generations",
                    headers=headers,
                    json=payload
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"Grok图片生成API响应: {result}")
                
                # 解析响应
                if "data" in result and len(result["data"]) > 0:
                    if response_format == "url":
                        image_url = result["data"][0].get("url")
                        if image_url:
                            logger.info(f"图片生成成功: {image_url}")
                            return image_url
                        else:
                            logger.error(f"响应中没有找到图片URL: {result}")
                            return None
                    elif response_format == "b64_json":
                        # 返回base64编码的图片（如果需要）
                        b64_data = result["data"][0].get("b64_json")
                        if b64_data:
                            logger.info("图片生成成功（Base64格式）")
                            return b64_data
                        else:
                            logger.error(f"响应中没有找到Base64数据: {result}")
                            return None
                    else:
                        logger.error(f"不支持的response_format: {response_format}")
                        return None
                else:
                    logger.error(f"响应中没有data字段或data为空: {result}")
                    return None
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"Grok图片生成API HTTP错误: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.TimeoutException:
            logger.error(f"Grok图片生成API请求超时（超过{timeout}秒）")
            return None
        except Exception as e:
            logger.error(f"Grok图片生成失败: {str(e)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return None

    async def generate_image(
        self,
        prompt: str,
        n: int = 1,
        response_format: str = "url",
        timeout: int = 120
    ) -> Optional[str]:
        """
        异步生成图片
        
        Args:
            prompt: 图片描述提示词
            n: 生成图片数量（1-10）
            response_format: 返回格式，"url" 或 "b64_json"
            timeout: 请求超时时间（秒）
        
        Returns:
            图片URL（如果response_format="url"）或None
        """
        if not self.available:
            logger.warning("Grok图片生成服务不可用，跳过图片生成")
            return None

        if n > 10:
            n = 10
            logger.warning(f"图片数量超过10，已调整为10")
        elif n < 1:
            n = 1

        try:
            logger.info(f"开始使用Grok异步生成图片: {prompt[:50]}...")
            
            headers = {
                "Authorization": f"Bearer {self.grok_api_key}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "image_format": response_format,
                "n": n
            }
            
            # 调用Grok图片生成API
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.grok_base_url}/images/generations",
                    headers=headers,
                    json=payload
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"Grok图片生成API响应: {result}")
                
                # 解析响应
                if "data" in result and len(result["data"]) > 0:
                    if response_format == "url":
                        image_url = result["data"][0].get("url")
                        if image_url:
                            logger.info(f"图片生成成功: {image_url}")
                            return image_url
                        else:
                            logger.error(f"响应中没有找到图片URL: {result}")
                            return None
                    elif response_format == "b64_json":
                        b64_data = result["data"][0].get("b64_json")
                        if b64_data:
                            logger.info("图片生成成功（Base64格式）")
                            return b64_data
                        else:
                            logger.error(f"响应中没有找到Base64数据: {result}")
                            return None
                    else:
                        logger.error(f"不支持的response_format: {response_format}")
                        return None
                else:
                    logger.error(f"响应中没有data字段或data为空: {result}")
                    return None
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"Grok图片生成API HTTP错误: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.TimeoutException:
            logger.error(f"Grok图片生成API请求超时（超过{timeout}秒）")
            return None
        except Exception as e:
            logger.error(f"Grok图片生成失败: {str(e)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return None


# 全局服务实例
_grok_image_service_instance: Optional[GrokImageService] = None


def get_grok_image_service() -> GrokImageService:
    """获取全局Grok图片生成服务实例"""
    global _grok_image_service_instance
    if _grok_image_service_instance is None:
        _grok_image_service_instance = GrokImageService()
    return _grok_image_service_instance
