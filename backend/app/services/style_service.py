import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# 延迟导入replicate以避免Python 3.14兼容性问题
_replicate_client = None

def _get_replicate_client():
    """延迟加载replicate客户端"""
    global _replicate_client
    if _replicate_client is None:
        try:
            import replicate
            api_token = os.getenv("REPLICATE_API_TOKEN")
            if not api_token:
                raise ValueError("REPLICATE_API_TOKEN环境变量未设置")
            os.environ["REPLICATE_API_TOKEN"] = api_token
            _replicate_client = replicate.Client(api_token=api_token)
        except Exception as e:
            logger.error(f"Replicate客户端初始化失败: {str(e)}")
            raise
    return _replicate_client


class StyleService:
    """水墨画风格转换服务（通过Replicate）"""
    
    def __init__(self):
        self.client = _get_replicate_client()
        # 使用水墨画风格转换模型（示例，需要根据实际可用模型调整）
        # 可以使用图像到图像的转换模型
        self.model = "lucataco/style-transfer:95d7a1e501b9f5c03b4c5a6cfdfda2b4e70941f5"
    
    async def convert_to_ink_painting(
        self,
        image_url: str,
        style_strength: float = 0.8
    ) -> str:
        """
        将图片转换为水墨画风格
        
        Args:
            image_url: 原始图片URL
            style_strength: 风格强度 (0-1)
        
        Returns:
            转换后的图片URL
        """
        try:
            # 使用风格转换模型
            # 注意：实际的模型和参数需要根据Replicate上的可用模型调整
            input_params = {
                "image": image_url,
                "style_strength": style_strength,
            }
            
            output = self.client.run(
                self.model,
                input=input_params
            )
            
            if isinstance(output, list) and len(output) > 0:
                return output[0]
            elif isinstance(output, str):
                return output
            else:
                raise Exception(f"意外的输出格式: {output}")
        except Exception as e:
            logger.error(f"风格转换失败: {str(e)}")
            # 如果风格转换失败，返回原图URL作为降级方案
            logger.warning(f"风格转换失败，返回原图: {image_url}")
            return image_url
    
    def convert_to_ink_painting_sync(
        self,
        image_url: str,
        style_strength: float = 0.8
    ) -> str:
        """同步版本的风格转换"""
        try:
            input_params = {
                "image": image_url,
                "style_strength": style_strength,
            }
            
            output = self.client.run(
                self.model,
                input=input_params
            )
            
            if isinstance(output, list) and len(output) > 0:
                return output[0]
            elif isinstance(output, str):
                return output
            else:
                raise Exception(f"意外的输出格式: {output}")
        except Exception as e:
            logger.error(f"风格转换失败: {str(e)}")
            logger.warning(f"风格转换失败，返回原图: {image_url}")
            return image_url


# 全局服务实例
_style_service_instance: Optional[StyleService] = None


def get_style_service() -> StyleService:
    """获取全局风格服务实例"""
    global _style_service_instance
    if _style_service_instance is None:
        _style_service_instance = StyleService()
    return _style_service_instance
