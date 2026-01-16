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
                return None
            os.environ["REPLICATE_API_TOKEN"] = api_token
            _replicate_client = replicate.Client(api_token=api_token)
        except Exception as e:
            logger.warning(f"Replicate客户端初始化失败: {str(e)}")
            return None
    return _replicate_client


class VideoService:
    """视频生成服务 - 使用Replicate (Stable Video Diffusion)作为主要方案"""
    
    def __init__(self):
        # 优先使用Replicate（不需要额外API Key，使用已有的REPLICATE_API_TOKEN）
        api_token = os.getenv("REPLICATE_API_TOKEN")
        if not api_token:
            logger.warning("REPLICATE_API_TOKEN未设置，视频生成功能将不可用")
            self.client = None
        else:
            self.client = _get_replicate_client()
        
        # 使用Stable Video Diffusion模型（通过Replicate）
        # 这是图像到视频的模型，需要先有一张图片
        self.model = "stability-ai/stable-video-diffusion:3f0457e4619daac51203dedb472816fd4af51f3149fa7a9e0b5ffcf1b8172438"
        
        # 备用：Runway API（如果配置了）
        self.runway_api_key = os.getenv("RUNWAY_API_KEY")
        self.use_runway = bool(self.runway_api_key)
    
    def generate_video_sync(
        self,
        prompt: str,
        base_image_url: Optional[str] = None
    ) -> Optional[str]:
        """
        同步生成视频（使用Replicate Stable Video Diffusion）
        
        Args:
            prompt: 视频描述提示词（如果提供base_image_url，此参数用于日志）
            base_image_url: 基础图片URL（如果提供，将使用此图片生成视频）
        
        Returns:
            生成视频的URL，如果失败返回None
        """
        if not self.client:
            logger.warning("Replicate客户端未初始化，跳过视频生成")
            return None
        
        try:
            # 如果没有提供基础图片，先使用Replicate生成一张图片
            if not base_image_url:
                # 使用Stable Diffusion生成基础图片
                image_model = "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
                logger.info(f"生成基础图片: {prompt}")
                image_output = self.client.run(
                    image_model,
                    input={"prompt": prompt, "width": 1024, "height": 1024}
                )
                if isinstance(image_output, list) and len(image_output) > 0:
                    base_image_url = image_output[0]
                elif isinstance(image_output, str):
                    base_image_url = image_output
                else:
                    raise Exception("图片生成失败")
            
            # 使用Stable Video Diffusion生成视频
            logger.info(f"基于图片生成视频: {base_image_url}")
            output = self.client.run(
                self.model,
                input={
                    "image": base_image_url,
                    "motion_bucket_id": 127,  # 运动强度（1-255）
                    "cond_aug": 0.02,  # 条件增强
                }
            )
            
            # 等待输出
            video_url = None
            if isinstance(output, str):
                video_url = output
            elif isinstance(output, list) and len(output) > 0:
                video_url = output[0]
            elif hasattr(output, '__iter__'):
                # Replicate可能返回迭代器
                for item in output:
                    video_url = item
                    break
            
            if video_url:
                return video_url
            else:
                raise Exception("未能获取视频URL")
        except Exception as e:
            logger.error(f"视频生成失败: {str(e)}")
            # 降级到None，表示不使用视频
            return None
    
    def generate_video_simple(
        self,
        prompt: str
    ) -> Optional[str]:
        """
        简化版视频生成（降级方案，返回None表示跳过视频）
        
        Args:
            prompt: 视频描述提示词
        
        Returns:
            视频URL或None（表示不使用视频）
        """
        logger.info("视频生成功能不可用，将在LoadingScreen中显示静态图片")
        return None


# 全局服务实例
_video_service_instance: Optional[VideoService] = None


def get_video_service() -> VideoService:
    """获取全局视频服务实例"""
    global _video_service_instance
    if _video_service_instance is None:
        try:
            _video_service_instance = VideoService()
        except Exception as e:
            logger.warning(f"视频服务初始化失败: {str(e)}，将使用降级方案")
            # 创建一个只返回None的降级服务
            _video_service_instance = VideoService.__new__(VideoService)
            _video_service_instance.client = None
            _video_service_instance.use_runway = False
            _video_service_instance.model = None
    return _video_service_instance
