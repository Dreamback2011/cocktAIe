"""
OpenAI DALL-E图片生成服务
使用OpenAI的DALL-E模型进行图片生成
"""
import os
import httpx
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DalleImageService:
    """OpenAI DALL-E图片生成服务"""

    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1"
        
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY环境变量未设置，DALL-E图片生成功能将不可用")
            self.available = False
        else:
            self.available = True
            logger.info("DalleImageService初始化成功，使用DALL-E-3模型")

    def generate_image_sync(
        self,
        prompt: str,
        model: str = "dall-e-3",
        size: str = "1024x1024",
        quality: str = "standard",
        timeout: int = 120
    ) -> Optional[str]:
        """
        同步生成图片
        
        Args:
            prompt: 图片描述提示词
            model: 模型名称（dall-e-3 或 dall-e-2）
            size: 图片尺寸（dall-e-3支持: "1024x1024", "1792x1024", "1024x1792"）
            quality: 图片质量（dall-e-3支持: "standard", "hd"）
            timeout: 请求超时时间（秒）
        
        Returns:
            图片URL或None
        """
        if not self.available:
            logger.warning("DALL-E图片生成服务不可用，跳过图片生成")
            return None

        try:
            logger.info(f"开始使用DALL-E生成图片: {prompt[:50]}...")
            
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "model": model,
                "prompt": prompt,
                "size": size,
                "quality": quality,
                "n": 1
            }
            
            # 调用OpenAI DALL-E API
            with httpx.Client(timeout=timeout) as client:
                response = client.post(
                    f"{self.base_url}/images/generations",
                    headers=headers,
                    json=payload
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"DALL-E图片生成API响应: {result}")
                
                # 解析响应
                if "data" in result and len(result["data"]) > 0:
                    image_url = result["data"][0].get("url")
                    if image_url:
                        logger.info(f"图片生成成功: {image_url}")
                        return image_url
                    else:
                        logger.error(f"响应中没有找到图片URL: {result}")
                        return None
                else:
                    logger.error(f"响应中没有data字段或data为空: {result}")
                    return None
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"DALL-E图片生成API HTTP错误: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.TimeoutException:
            logger.error(f"DALL-E图片生成API请求超时（超过{timeout}秒）")
            return None
        except Exception as e:
            logger.error(f"DALL-E图片生成失败: {str(e)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return None


# 全局服务实例
_dalle_image_service_instance: Optional[DalleImageService] = None


def get_dalle_image_service() -> DalleImageService:
    """获取全局DALL-E图片生成服务实例"""
    global _dalle_image_service_instance
    if _dalle_image_service_instance is None:
        _dalle_image_service_instance = DalleImageService()
    return _dalle_image_service_instance
