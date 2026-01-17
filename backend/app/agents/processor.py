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
        
        # 步骤1：用户输入处理（Checker 1: 用户输入完成）
        user_story = ""
        if request.audio_url:
            result.progress = {
                "step": "语音转文字",
                "progress": 5,
                "progress_details": {
                    "user_input": {"status": "in_progress", "progress": 0, "step": "处理音频输入..."}
                }
            }
            voice_service = get_voice_service()
            # 注意：这里audio_url应该是文件路径
            user_story = voice_service.transcribe_audio_sync(request.audio_url)
        elif request.text:
            user_story = request.text
        else:
            raise ValueError("必须提供音频URL或文本输入")
        
        # Checker 1: 用户输入完成
        result.progress = {
            "step": "用户输入完成",
            "progress": 10,
            "progress_details": {
                "user_input": {"status": "completed", "progress": 100, "step": "用户输入已接收"}
            }
        }
        
        # 步骤2：语义分析
        result.progress = {
            "step": "语义分析",
            "progress": 20,
            "progress_details": {
                "semantic_analysis": {"status": "in_progress", "progress": 0, "step": "分析用户故事..."},
                "cocktail_recommendation": {"status": "pending", "progress": 0},
                "text_generation": {"status": "pending", "progress": 0},
                "image_generation": {"status": "pending", "progress": 0},
                "layout": {"status": "pending", "progress": 0}
            }
        }
        semantic_agent = SemanticAgent()
        semantic_output = semantic_agent.analyze(user_story)
        result.semantic_analysis = semantic_output
        
        # Checker 2: 语义分析完成
        result.progress = {
            "step": "语义分析完成",
            "progress": 30,
            "progress_details": {
                "user_input": {"status": "completed", "progress": 100},
                "semantic_analysis": {"status": "completed", "progress": 100, "step": "语义分析完成"},
                "cocktail_recommendation": {"status": "pending", "progress": 0},
                "text_generation": {"status": "pending", "progress": 0},
                "image_generation": {"status": "pending", "progress": 0},
                "layout": {"status": "pending", "progress": 0}
            }
        }
        
        # 步骤3：鸡尾酒调配（可以与步骤4并行，但这里串行实现）
        result.progress = {
            "step": "鸡尾酒调配",
            "progress": 40,
            "progress_details": {
                **result.progress.get('progress_details', {}),
                "cocktail_recommendation": {"status": "in_progress", "progress": 50, "step": "匹配并调配鸡尾酒..."}
            }
        }
        cocktail_agent = CocktailAgent()
        # 使用task_id作为session_id，记录推荐历史
        cocktail_output = cocktail_agent.mix_cocktail(semantic_output, session_id=task_id)
        result.cocktail_mix = cocktail_output
        
        # Checker 3: 选酒完成（基于recipe生成图片提示词）
        result.progress = {
            "step": "鸡尾酒调配完成",
            "progress": 50,
            "progress_details": {
                **result.progress.get('progress_details', {}),
                "cocktail_recommendation": {"status": "completed", "progress": 100, "step": "鸡尾酒已匹配完成，recipe已生成"},
                "text_generation": {"status": "pending", "progress": 0},
                "image_generation": {"status": "pending", "progress": 0}
            }
        }
        
        # 步骤4：呈现生成（包括文字生成和图片生成）
        def update_progress(progress_info):
            """更新进度的回调函数，包含详细进度信息"""
            # 更新总体进度
            result.progress.update(progress_info)
            
            # 更新详细进度信息
            if 'progress_details' not in result.progress:
                result.progress['progress_details'] = {}
            if 'details' in progress_info:
                result.progress['progress_details'].update(progress_info['details'])
            
            # 同步到task_storage（在main.py中会自动同步）
            # main.py中的sync_task_storage函数会在获取状态时同步
        
        result.progress = {
            "step": "生成呈现内容",
            "progress": 60,
            "progress_details": {
                "semantic_analysis": {"status": "completed", "progress": 100},
                "cocktail_recommendation": {"status": "completed", "progress": 100},
                "text_generation": {"status": "in_progress", "progress": 0},
                "image_generation": {"status": "pending", "progress": 0},
                "layout": {"status": "pending", "progress": 0}
            }
        }
        
        presentation_agent = PresentationAgent()
        presentation_output = presentation_agent.generate_presentation(
            semantic_output=semantic_output,
            cocktail_output=cocktail_output,
            progress_callback=update_progress
        )
        result.presentation = presentation_output
        
        # 确保所有内容都已生成完成
        if not presentation_output.cocktail_name:
            raise Exception("鸡尾酒名称生成失败")
        
        # 检查图片是否生成（至少有一个图片）
        has_image = (
            presentation_output.cocktail_image_url or 
            presentation_output.final_presentation_image_url
        )
        
        if not has_image:
            logger.warning("图片生成失败，但继续处理")
        
        # 更新进度：所有呈现内容已生成
        result.progress = {
            "step": "呈现内容生成完成，准备排版",
            "progress": 80,
            "progress_details": {
                "semantic_analysis": {"status": "completed", "progress": 100},
                "cocktail_recommendation": {"status": "completed", "progress": 100},
                "text_generation": {"status": "completed", "progress": 100},
                "image_generation": {
                    "status": "completed" if has_image else "failed",
                    "progress": 100 if has_image else 0,
                    "cocktail_image": "completed" if presentation_output.cocktail_image_url else "failed",
                    "final_image": "completed" if presentation_output.final_presentation_image_url else "failed"
                },
                "layout": {"status": "in_progress", "progress": 0}
            }
        }
        
        # 步骤5：排版（只有在所有内容生成完成后才进行）
        result.progress = {
            "step": "名片排版",
            "progress": 90,
            "progress_details": {
                **result.progress.get('progress_details', {}),
                "layout": {"status": "in_progress", "progress": 50}
            }
        }
        
        layout_agent = LayoutAgent()
        layout_output = layout_agent.create_card(
            cocktail_name=presentation_output.cocktail_name,
            semantic_output=semantic_output,
            presentation_output=presentation_output
        )
        result.layout = layout_output
        
        result.progress = {
            "step": "名片排版完成",
            "progress": 100,
            "progress_details": {
                **result.progress.get('progress_details', {}),
                "layout": {"status": "completed", "progress": 100}
            }
        }
        
        # 标记为完成
        result.status = TaskStatus.COMPLETED
        
        logger.info(f"任务 {task_id} 处理完成")
        
    except Exception as e:
        logger.error(f"任务 {task_id} 处理失败: {str(e)}")
        if task_id in task_storage:
            task_storage[task_id].status = TaskStatus.FAILED
            task_storage[task_id].error = str(e)
