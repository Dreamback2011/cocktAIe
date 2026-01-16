"""
处理流程协调器 - 协调所有Agent的工作
"""
import asyncio
import os
import logging
from typing import Optional
from app.models.schemas import ProcessStoryRequest, ProcessingResult, TaskStatus
from app.services.voice_service import get_voice_service
from app.agents.semantic_agent import SemanticAgent
from app.agents.cocktail_agent import CocktailAgent
from app.agents.presentation_agent import PresentationAgent
from app.agents.layout_agent import LayoutAgent

logger = logging.getLogger(__name__)

# 全局任务存储（实际应使用Redis等）
# 这个存储与main.py中的task_storage同步
task_storage: dict[str, ProcessingResult] = {}


async def process_story_async(task_id: str, request: ProcessStoryRequest):
    """
    异步处理用户故事的完整流程
    
    Args:
        task_id: 任务ID
        request: 处理请求
    """
    try:
        # 初始化任务状态
        if task_id not in task_storage:
            task_storage[task_id] = ProcessingResult(
                task_id=task_id,
                status=TaskStatus.PROCESSING,
                progress={}
            )
        
        result = task_storage[task_id]
        result.progress = {"step": "开始处理", "progress": 0}
        
        # 步骤1：语音转文字（如果有音频）
        user_story = ""
        if request.audio_url:
            result.progress = {"step": "语音转文字", "progress": 10}
            voice_service = get_voice_service()
            # 注意：这里audio_url应该是文件路径
            user_story = voice_service.transcribe_audio_sync(request.audio_url)
        elif request.text:
            user_story = request.text
            result.progress = {"step": "使用文本输入", "progress": 10}
        else:
            raise ValueError("必须提供音频URL或文本输入")
        
        # 步骤2：语义分析
        result.progress = {"step": "语义分析", "progress": 20}
        semantic_agent = SemanticAgent()
        semantic_output = semantic_agent.analyze(user_story)
        result.semantic_analysis = semantic_output
        result.progress = {"step": "语义分析完成", "progress": 30}
        
        # 步骤3：鸡尾酒调配（可以与步骤4并行，但这里串行实现）
        result.progress = {"step": "鸡尾酒调配", "progress": 40}
        cocktail_agent = CocktailAgent()
        cocktail_output = cocktail_agent.mix_cocktail(semantic_output)
        result.cocktail_mix = cocktail_output
        result.progress = {"step": "鸡尾酒调配完成", "progress": 50}
        
        # 步骤4：呈现生成
        def update_progress(progress_info):
            """更新进度的回调函数"""
            result.progress.update(progress_info)
            # 同步到processor_task_storage
            if task_id in processor_task_storage:
                processor_task_storage[task_id].progress.update(progress_info)
        
        result.progress = {"step": "生成呈现内容", "progress": 60}
        presentation_agent = PresentationAgent()
        presentation_output = presentation_agent.generate_presentation(
            semantic_output=semantic_output,
            cocktail_output=cocktail_output,
            progress_callback=update_progress
        )
        result.presentation = presentation_output
        result.progress = {"step": "呈现内容生成完成", "progress": 80}
        
        # 步骤5：排版
        result.progress = {"step": "名片排版", "progress": 90}
        layout_agent = LayoutAgent()
        layout_output = layout_agent.create_card(
            cocktail_name=presentation_output.cocktail_name,
            semantic_output=semantic_output,
            presentation_output=presentation_output
        )
        result.layout = layout_output
        result.progress = {"step": "名片排版完成", "progress": 100}
        
        # 标记为完成
        result.status = TaskStatus.COMPLETED
        
        logger.info(f"任务 {task_id} 处理完成")
        
    except Exception as e:
        logger.error(f"任务 {task_id} 处理失败: {str(e)}")
        if task_id in task_storage:
            task_storage[task_id].status = TaskStatus.FAILED
            task_storage[task_id].error = str(e)
