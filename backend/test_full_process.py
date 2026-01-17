"""
测试完整处理流程，包括新的进度追踪系统
"""

import sys
import os
import time
import asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.schemas import ProcessStoryRequest
from app.agents.processor import process_story_async, task_storage
import uuid

async def test_full_process():
    """测试完整的处理流程"""
    
    print("=" * 80)
    print("完整处理流程测试")
    print("=" * 80)
    print()
    
    # 测试文本
    test_text = """雨又落在陌生的街道上，和我脚步的节奏错开。霓虹把湿漉漉的人行道染成碎裂的光，我拖着行李箱穿过地铁口，像被城市反复吞吐的一粒尘。
    
公寓窗外是永远不熟悉的天际线，楼下咖啡店的名字我念不顺，邻居的问候点到为止。手机里母亲的语音隔着时差，带着厨房的油烟味，却在播放结束时变得空旷。

我习惯把钥匙放在固定的位置，却总忘记自己为何留下。工作在屏幕里流动，会议、表格、航班，像把时间切成整齐的薄片，却拼不回完整的一天。

夜深时我坐在地板上，看冰箱里冷白的灯，想起曾经在老巷口等雨停的夏天。窗外电车掠过，风声里混着远方的口音。我忽然明白，异乡并不残忍，它只是冷静地容纳我，却从不替我记住来路。

我把窗帘拉紧，灯熄灭。黑暗里，只有心跳替我证明，我仍在路上，而不是已经抵达。"""
    
    # 创建任务ID
    task_id = str(uuid.uuid4())
    
    # 创建请求
    request = ProcessStoryRequest(
        text=test_text
    )
    
    print(f"任务ID: {task_id}")
    print(f"测试文本长度: {len(test_text)} 字符")
    print()
    
    # 启动异步处理任务
    print("开始处理...")
    print("-" * 80)
    
    # 在后台运行处理任务
    import asyncio
    task = asyncio.create_task(process_story_async(task_id, request))
    
    # 轮询进度
    print("轮询进度...")
    print()
    
    last_progress = -1
    last_step = ""
    last_details = {}
    poll_count = 0
    max_polls = 300  # 最多轮询5分钟（300秒 * 1秒间隔）
    
    while poll_count < max_polls:
        poll_count += 1
        await asyncio.sleep(1)  # 等待1秒后再检查
        
        if task_id in task_storage:
            result = task_storage[task_id]
            
            # 显示总体进度
            if result.progress:
                current_progress = result.progress.get('progress', 0)
                current_step = result.progress.get('step', '未知')
                
                # 如果进度或步骤变化，显示更新
                if current_progress != last_progress or current_step != last_step:
                    print(f"\n[{current_progress}%] {current_step}")
                    last_progress = current_progress
                    last_step = current_step
                
                # 显示详细进度（只在有变化时显示）
                progress_details = result.progress.get('progress_details', {})
                if progress_details:
                    # 检查是否有变化
                    details_changed = False
                    if progress_details != last_details:
                        details_changed = True
                        last_details = progress_details.copy()
                    
                    if details_changed:
                        print("  详细进度:")
                        for key, detail in progress_details.items():
                            status = detail.get('status', 'unknown')
                            step = detail.get('step', '')
                            progress = detail.get('progress', 0)
                            
                            status_icon = {
                                'pending': '○',
                                'in_progress': '⟳',
                                'completed': '✓',
                                'failed': '✗'
                            }.get(status, '?')
                            
                            # 格式化键名（中文）
                            key_names = {
                                'semantic_analysis': '语义分析',
                                'cocktail_recommendation': '鸡尾酒推荐',
                                'text_generation': '文字生成',
                                'image_generation': '图片生成',
                                'layout': '名片排版'
                            }
                            key_name = key_names.get(key, key)
                            
                            print(f"    {status_icon} {key_name}: {status} ({progress}%)", end='')
                            if step:
                                print(f" - {step}")
                            else:
                                print()
                            
                            # 图片生成的特殊处理
                            if key == 'image_generation':
                                cocktail_image = detail.get('cocktail_image', '')
                                final_image = detail.get('final_image', '')
                                if cocktail_image and cocktail_image != 'pending':
                                    print(f"        → 鸡尾酒图片: {cocktail_image}")
                                if final_image and final_image != 'pending':
                                    print(f"        → 最终图片: {final_image}")
                        
                        print()  # 空行分隔
            
            # 检查是否完成
            if result.status.value == 'completed':
                print("\n" + "=" * 80)
                print("处理完成！")
                print("=" * 80)
                print(f"总耗时: 约 {poll_count} 秒")
                print()
                
                # 显示结果摘要
                if result.semantic_analysis:
                    print("语义分析结果:")
                    print(f"  Energy: {result.semantic_analysis.energy}/5")
                    print(f"  Tension: {result.semantic_analysis.tension}/5")
                    print(f"  Control: {result.semantic_analysis.control}/5")
                    print(f"  需求: {', '.join(result.semantic_analysis.needs)}")
                    print()
                
                if result.cocktail_mix:
                    print("鸡尾酒调配结果:")
                    print(f"  基础鸡尾酒: {result.cocktail_mix.base_cocktail.name}")
                    print(f"  定制配方: {result.cocktail_mix.customized_recipe}")
                    print()
                
                if result.presentation:
                    print("呈现内容:")
                    print(f"  鸡尾酒名称: {result.presentation.cocktail_name}")
                    print(f"  鸡尾酒图片: {result.presentation.cocktail_image_url or '未生成'}")
                    print(f"  最终呈现图片: {result.presentation.final_presentation_image_url or '未生成'}")
                    print(f"  视频: {result.presentation.production_video_url or '未生成'}")
                    print()
                
                if result.layout:
                    print("排版结果:")
                    print(f"  简化回复: {result.layout.simplified_response}")
                    print(f"  最终名片: {result.layout.final_card_url or '未生成'}")
                    print()
                
                break
            elif result.status.value == 'failed':
                print(f"\n处理失败: {result.error}")
                break
        else:
            # 任务还未开始，继续等待
            if poll_count % 5 == 0:  # 每5秒显示一次等待
                print(".", end="", flush=True)
    
    if poll_count >= max_polls:
        print("\n\n⚠️  警告: 处理超时（5分钟）")
        if task_id in task_storage:
            result = task_storage[task_id]
            print(f"当前状态: {result.status.value}")
            if result.error:
                print(f"错误信息: {result.error}")
    
    # 等待任务完成
    try:
        await task
    except Exception as e:
        print(f"\n任务执行异常: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n测试完成！")

if __name__ == "__main__":
    asyncio.run(test_full_process())
