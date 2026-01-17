from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
import uuid
import os
from dotenv import load_dotenv

from app.models.schemas import (
    AudioUploadResponse,
    ProcessStoryRequest,
    ProcessStoryResponse,
    ProcessStatusResponse,
    ProcessingResult,
    TaskStatus,
)

load_dotenv()

app = FastAPI(title="情感鸡尾酒推荐系统", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:5173"),
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录（用于访问生成的名片）
os.makedirs("generated_cards", exist_ok=True)
app.mount("/generated_cards", StaticFiles(directory="generated_cards"), name="generated_cards")

# 临时存储任务状态（生产环境应使用Redis等）
task_storage: dict[str, ProcessingResult] = {}

# 同步processor中的task_storage
from app.agents.processor import task_storage as processor_task_storage
def sync_task_storage():
    """同步任务状态"""
    for task_id, result in processor_task_storage.items():
        if task_id in task_storage:
            task_storage[task_id] = result


@app.get("/")
async def root():
    return {"message": "情感鸡尾酒推荐系统API", "version": "1.0.0"}


@app.post("/api/upload-audio", response_model=AudioUploadResponse)
async def upload_audio(file: UploadFile = File(...)):
    """接收音频文件上传"""
    try:
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 保存音频文件到临时目录
        temp_dir = "temp_audio"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, f"{task_id}_{file.filename}")
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 初始化任务状态
        task_storage[task_id] = ProcessingResult(
            task_id=task_id,
            status=TaskStatus.PENDING,
            progress={"audio_uploaded": True, "file_path": file_path}
        )
        
        return AudioUploadResponse(task_id=task_id, message="音频上传成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@app.post("/api/process-story", response_model=ProcessStoryResponse)
async def process_story(
    request: ProcessStoryRequest,
    background_tasks: BackgroundTasks
):
    """处理用户故事的主要端点"""
    # 验证输入：必须提供音频URL或文本
    if not request.audio_url and not request.text:
        raise HTTPException(status_code=400, detail="必须提供audio_url或text")
    
    # 如果audio_url看起来像task_id（不包含http），则从task_storage中获取文件路径
    task_id = None
    if request.audio_url:
        if not request.audio_url.startswith('http') and request.audio_url in task_storage:
            task_id = request.audio_url
            stored_result = task_storage[task_id]
            file_path = stored_result.progress.get('file_path')
            if file_path:
                request.audio_url = file_path
    
    # 如果还没有task_id（文本输入或新任务），创建新的
    if not task_id:
        task_id = str(uuid.uuid4())
    
    # 初始化任务状态
    if task_id not in task_storage:
        task_storage[task_id] = ProcessingResult(
            task_id=task_id,
            status=TaskStatus.PROCESSING,
            progress={"started": True}
        )
    
    # 启动后台任务处理
    from app.agents.processor import process_story_async, task_storage as processor_task_storage
    
    # 同步task_storage
    if task_id not in task_storage:
        task_storage[task_id] = ProcessingResult(
            task_id=task_id,
            status=TaskStatus.PROCESSING,
            progress={}
        )
    processor_task_storage[task_id] = task_storage[task_id]
    
    # 启动后台任务
    try:
        background_tasks.add_task(process_story_async, task_id, request)
    except Exception as e:
        # 如果后台任务启动失败，标记任务为失败
        if task_id in task_storage:
            task_storage[task_id].status = TaskStatus.FAILED
            task_storage[task_id].error = str(e)
        raise HTTPException(status_code=500, detail=f"启动处理任务失败: {str(e)}")
    
    return ProcessStoryResponse(task_id=task_id, status=TaskStatus.PROCESSING)


@app.get("/api/process-status/{task_id}", response_model=ProcessStatusResponse)
async def get_process_status(task_id: str):
    """获取处理状态"""
    # 同步processor中的任务状态
    from app.agents.processor import task_storage as processor_task_storage
    if task_id in processor_task_storage:
        task_storage[task_id] = processor_task_storage[task_id]
    
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    result = task_storage[task_id]
    
    # 在processing过程中也返回部分结果（如果存在），方便前端显示图片等
    partial_result = None
    if result.status == TaskStatus.COMPLETED:
        partial_result = result
    elif result.presentation or result.cocktail_mix or result.semantic_analysis:
        # 返回部分结果，让前端可以提前显示已生成的内容
        partial_result = result
    
    # 从result.progress中提取progress_details
    progress_details = {}
    if isinstance(result.progress, dict):
        progress_details = result.progress.get('progress_details', {})
    
    return ProcessStatusResponse(
        task_id=task_id,
        status=result.status,
        progress=result.progress if isinstance(result.progress, dict) else {},
        progress_details=progress_details,
        result=partial_result
    )


@app.get("/api/get-result/{task_id}", response_model=ProcessingResult)
async def get_result(task_id: str):
    """获取最终结果"""
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    result = task_storage[task_id]
    if result.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="任务尚未完成")
    
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
