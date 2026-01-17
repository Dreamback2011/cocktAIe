import React, { useEffect, useState } from 'react';
import { getProcessStatus, ProcessingResult } from '../services/api';
import './LoadingScreen.css';

interface LoadingScreenProps {
  taskId: string;
  onComplete: (result: ProcessingResult) => void;
}

interface ProgressDetail {
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress: number;
  step?: string;
  [key: string]: any;
}

const LoadingScreen: React.FC<LoadingScreenProps> = ({ taskId, onComplete }) => {
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('开始处理');
  const [responseText, setResponseText] = useState('');
  const [progressDetails, setProgressDetails] = useState<Record<string, ProgressDetail>>({});

  useEffect(() => {
    let isMounted = true;
    let pollTimeout: NodeJS.Timeout | null = null;
    
    const pollStatus = async () => {
      if (!isMounted) return;
      
      try {
        const status = await getProcessStatus(taskId);
        
        if (!isMounted) return;
        
        // 修复进度读取：status.progress 是字典，包含 progress 和 step 字段
        if (status.progress) {
          // status.progress 本身是一个字典，包含 progress 和 step 字段
          const progressValue = status.progress.progress || 0;
          const step = status.progress.step || currentStep;
          
          // 确保进度值是数字
          const numProgress = typeof progressValue === 'number' ? progressValue : parseInt(String(progressValue)) || 0;
          
          setProgress(numProgress);
          setCurrentStep(step);
          
          // 更新详细进度信息 - 优先使用status.progress_details，否则从status.progress中提取
          if (status.progress_details && Object.keys(status.progress_details).length > 0) {
            setProgressDetails(status.progress_details);
          } else if (status.progress?.progress_details) {
            setProgressDetails(status.progress.progress_details);
          }
          
          // 调试输出
          console.log('进度更新:', { 
            progress: numProgress, 
            step, 
            progressDetails: status.progress_details || status.progress?.progress_details,
            fullProgress: status.progress
          });
          
          // 如果有语义分析结果，显示回复文本
          if (status.result?.semantic_analysis?.response_text) {
            setResponseText(status.result.semantic_analysis.response_text);
          }
        }
        
        if (status.status === 'completed' && status.result) {
          // 立即停止轮询，显示最终结果
          setProgress(100);
          setCurrentStep('完成！');
          onComplete(status.result);
          return; // 停止轮询
        } else if (status.status === 'failed') {
          alert('处理失败，请重试');
          return; // 停止轮询
        } else {
          // 继续轮询
          pollTimeout = setTimeout(pollStatus, 2000);
        }
      } catch (error) {
        console.error('获取状态失败:', error);
        if (isMounted) {
          pollTimeout = setTimeout(pollStatus, 3000);
        }
      }
    };

    pollStatus();
    
    // 清理函数：组件卸载时停止轮询
    return () => {
      isMounted = false;
      if (pollTimeout) {
        clearTimeout(pollTimeout);
      }
    };
  }, [taskId, onComplete, currentStep]);

  return (
    <div className="loading-screen">
      <div className="loading-content">
        <h2 className="loading-title">正在为你调制专属鸡尾酒...</h2>
        
        <div className="progress-container">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <p className="progress-text">{progress}%</p>
          <p className="current-step">{currentStep}</p>
          
          {/* 详细进度显示 */}
          {progressDetails && Object.keys(progressDetails).length > 0 && (
            <div className="progress-details">
              {progressDetails.semantic_analysis && (
                <div className={`progress-detail-item ${progressDetails.semantic_analysis.status}`}>
                  <span className="detail-label">语义分析：</span>
                  <span className="detail-status">
                    {progressDetails.semantic_analysis.status === 'completed' ? '✓' : 
                     progressDetails.semantic_analysis.status === 'in_progress' ? '⟳' : 
                     progressDetails.semantic_analysis.status === 'failed' ? '✗' : '○'}
                  </span>
                  <span className="detail-step">{progressDetails.semantic_analysis.step || '等待中'}</span>
                </div>
              )}
              {progressDetails.cocktail_recommendation && (
                <div className={`progress-detail-item ${progressDetails.cocktail_recommendation.status}`}>
                  <span className="detail-label">鸡尾酒推荐：</span>
                  <span className="detail-status">
                    {progressDetails.cocktail_recommendation.status === 'completed' ? '✓' : 
                     progressDetails.cocktail_recommendation.status === 'in_progress' ? '⟳' : 
                     progressDetails.cocktail_recommendation.status === 'failed' ? '✗' : '○'}
                  </span>
                  <span className="detail-step">{progressDetails.cocktail_recommendation.step || '等待中'}</span>
                </div>
              )}
              {progressDetails.text_generation && (
                <div className={`progress-detail-item ${progressDetails.text_generation.status}`}>
                  <span className="detail-label">文字生成：</span>
                  <span className="detail-status">
                    {progressDetails.text_generation.status === 'completed' ? '✓' : 
                     progressDetails.text_generation.status === 'in_progress' ? '⟳' : 
                     progressDetails.text_generation.status === 'failed' ? '✗' : '○'}
                  </span>
                  <span className="detail-step">{progressDetails.text_generation.step || '等待中'}</span>
                  {progressDetails.text_generation.result && (
                    <span className="detail-result"> ({progressDetails.text_generation.result})</span>
                  )}
                </div>
              )}
              {progressDetails.image_generation && (
                <div className={`progress-detail-item ${progressDetails.image_generation.status}`}>
                  <span className="detail-label">图片生成：</span>
                  <span className="detail-status">
                    {progressDetails.image_generation.status === 'completed' ? '✓' : 
                     progressDetails.image_generation.status === 'in_progress' ? '⟳' : 
                     progressDetails.image_generation.status === 'failed' ? '✗' : '○'}
                  </span>
                  <span className="detail-step">{progressDetails.image_generation.step || '等待中'}</span>
                  {progressDetails.image_generation.cocktail_image && (
                    <span className="detail-substep"> [鸡尾酒图: {progressDetails.image_generation.cocktail_image}]</span>
                  )}
                  {progressDetails.image_generation.final_image && (
                    <span className="detail-substep"> [最终图: {progressDetails.image_generation.final_image}]</span>
                  )}
                </div>
              )}
              {progressDetails.layout && (
                <div className={`progress-detail-item ${progressDetails.layout.status}`}>
                  <span className="detail-label">名片排版：</span>
                  <span className="detail-status">
                    {progressDetails.layout.status === 'completed' ? '✓' : 
                     progressDetails.layout.status === 'in_progress' ? '⟳' : 
                     progressDetails.layout.status === 'failed' ? '✗' : '○'}
                  </span>
                  <span className="detail-step">{progressDetails.layout.step || '等待中'}</span>
                </div>
              )}
            </div>
          )}
        </div>

        {responseText && (
          <div className="response-preview">
            <h3>给您的回复：</h3>
            <p>{responseText}</p>
          </div>
        )}

        <div className="loading-animation">
          <div className="cocktail-icon">🍸</div>
        </div>
      </div>
    </div>
  );
};

export default LoadingScreen;
