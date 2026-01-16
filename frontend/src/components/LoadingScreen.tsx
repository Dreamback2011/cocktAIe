import React, { useEffect, useState } from 'react';
import { getProcessStatus, ProcessingResult } from '../services/api';
import './LoadingScreen.css';

interface LoadingScreenProps {
  taskId: string;
  onComplete: (result: ProcessingResult) => void;
}

const LoadingScreen: React.FC<LoadingScreenProps> = ({ taskId, onComplete }) => {
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('开始处理');
  const [responseText, setResponseText] = useState('');

  useEffect(() => {
    let isMounted = true;
    let pollTimeout: NodeJS.Timeout | null = null;
    
    const pollStatus = async () => {
      if (!isMounted) return;
      
      try {
        const status = await getProcessStatus(taskId);
        
        if (!isMounted) return;
        
        if (status.progress) {
          const progressValue = status.progress.progress || 0;
          const step = status.progress.step || currentStep;
          
          setProgress(progressValue);
          setCurrentStep(step);
          
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
