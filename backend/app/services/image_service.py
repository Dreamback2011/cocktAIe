import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# 延迟导入replicate以避免Python 3.14兼容性问题
_replicate_client = None

def _get_replicate_client():
    """延迟加载replicate客户端，失败时返回None而不是抛出异常"""
    global _replicate_client
    if _replicate_client is None:
        try:
            import replicate
            api_token = os.getenv("REPLICATE_API_TOKEN")
            if not api_token:
                logger.warning("REPLICATE_API_TOKEN环境变量未设置")
                return None
            os.environ["REPLICATE_API_TOKEN"] = api_token
            _replicate_client = replicate.Client(api_token=api_token)
        except Exception as e:
            logger.warning(f"Replicate客户端初始化失败: {str(e)}，将跳过图片生成")
            return None
    return _replicate_client


class ImageService:
    """Stable Diffusion图像生成服务（通过Replicate）"""
    
    def __init__(self):
        self.client = _get_replicate_client()
        if self.client is None:
            logger.warning("ImageService初始化失败，Replicate客户端不可用")
        # 使用Stable Diffusion模型
        self.model = "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
    
    async def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024
    ) -> str:
        """
        生成图像
        
        Args:
            prompt: 图像描述提示词
            negative_prompt: 负面提示词
            width: 图像宽度
            height: 图像高度
        
        Returns:
            生成图像的URL
        """
        try:
            input_params = {
                "prompt": prompt,
                "width": width,
                "height": height,
            }
            if negative_prompt:
                input_params["negative_prompt"] = negative_prompt
            
            output = self.client.run(
                self.model,
                input=input_params
            )
            
            # Replicate返回的是列表，取第一个URL
            if isinstance(output, list) and len(output) > 0:
                return output[0]
            elif isinstance(output, str):
                return output
            else:
                raise Exception(f"意外的输出格式: {output}")
        except Exception as e:
            logger.error(f"图像生成失败: {str(e)}")
            raise Exception(f"图像生成失败: {str(e)}")
    
    def generate_image_sync(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        timeout: int = 120
    ) -> Optional[str]:
        """同步版本的图像生成（带超时）"""
        if self.client is None:
            logger.warning("Replicate客户端不可用，跳过图片生成")
            return None
        try:
            logger.info(f"开始生成图像: {prompt[:50]}...")
            input_params = {
                "prompt": prompt,
                "width": width,
                "height": height,
            }
            if negative_prompt:
                input_params["negative_prompt"] = negative_prompt
            
            # Replicate的run方法可能会阻塞，这里设置超时
            import signal
            import threading
            
            output = None
            error = None
            
            def run_generation():
                nonlocal output, error
                try:
                    output = self.client.run(
                        self.model,
                        input=input_params
                    )
                except Exception as e:
                    error = e
            
            thread = threading.Thread(target=run_generation)
            thread.daemon = True
            thread.start()
            thread.join(timeout=timeout)
            
            if thread.is_alive():
                logger.warning(f"图像生成超时（{timeout}秒）")
                raise Exception(f"图像生成超时（{timeout}秒），请稍后重试")
            
            if error:
                raise error
            
            if isinstance(output, list) and len(output) > 0:
                logger.info(f"图像生成成功: {output[0][:50]}...")
                return output[0]
            elif isinstance(output, str):
                logger.info(f"图像生成成功: {output[:50]}...")
                return output
            else:
                raise Exception(f"意外的输出格式: {output}")
        except Exception as e:
            logger.error(f"图像生成失败: {str(e)}")
            raise


# 全局服务实例
_image_service_instance: Optional[ImageService] = None


def get_image_service() -> ImageService:
    """获取全局图像服务实例"""
    global _image_service_instance
    if _image_service_instance is None:
        _image_service_instance = ImageService()
    return _image_service_instance
