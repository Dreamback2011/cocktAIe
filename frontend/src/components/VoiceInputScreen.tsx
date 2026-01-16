import React, { useState } from 'react';
import { useAudioRecorder } from '../hooks/useAudioRecorder';
import { uploadAudio, processStory } from '../services/api';
import './VoiceInputScreen.css';

interface VoiceInputScreenProps {
  onRecordingComplete: (taskId: string) => void;
  onBack: () => void;
}

type InputMode = 'voice' | 'text';

const VoiceInputScreen: React.FC<VoiceInputScreenProps> = ({ onRecordingComplete, onBack }) => {
  const { isRecording, audioBlob, startRecording, stopRecording, resetRecording } = useAudioRecorder();
  const [isUploading, setIsUploading] = useState(false);
  const [inputMode, setInputMode] = useState<InputMode>('voice');
  const [textInput, setTextInput] = useState('');

  const handleRecord = async () => {
    if (isRecording) {
      stopRecording();
    } else {
      resetRecording();
      await startRecording();
    }
  };

  const handleSubmit = async () => {
    // 检查输入模式
    if (inputMode === 'voice') {
      if (!audioBlob) {
        alert('请先录制音频');
        return;
      }
    } else {
      if (!textInput.trim()) {
        alert('请输入您的故事');
        return;
      }
    }

    setIsUploading(true);
    try {
      let processResponse: { task_id: string };
      
      if (inputMode === 'voice') {
        // 语音输入模式：上传音频文件
        const audioFile = new File([audioBlob], 'recording.webm', { type: 'audio/webm' });
        const uploadResponse = await uploadAudio(audioFile);
        // 开始处理故事（使用task_id作为audio_url，后端会识别）
        processResponse = await processStory(uploadResponse.task_id);
      } else {
        // 文本输入模式：直接发送文本
        processResponse = await processStory(undefined, textInput);
      }
      
      onRecordingComplete(processResponse.task_id);
    } catch (error: any) {
      console.error('提交失败:', error);
      const errorMessage = error?.response?.data?.detail || error?.message || '提交失败，请重试';
      alert(`提交失败: ${errorMessage}`);
      console.error('详细错误信息:', {
        message: error?.message,
        response: error?.response?.data,
        status: error?.response?.status,
      });
    } finally {
      setIsUploading(false);
    }
  };

  const canSubmit = inputMode === 'voice' 
    ? (audioBlob && !isRecording) 
    : (textInput.trim().length > 0);

  return (
    <div className="voice-input-screen">
      <div className="voice-input-content">
        <button className="back-button" onClick={onBack}>← 返回</button>
        <h2 className="voice-input-title">我有酒，来说说你的故事</h2>
        
        {/* 输入模式切换 */}
        <div className="input-mode-selector">
          <button
            className={`mode-button ${inputMode === 'voice' ? 'active' : ''}`}
            onClick={() => {
              setInputMode('voice');
              setTextInput('');
            }}
            disabled={isUploading || isRecording}
          >
            🎤 语音输入
          </button>
          <button
            className={`mode-button ${inputMode === 'text' ? 'active' : ''}`}
            onClick={() => {
              setInputMode('text');
              resetRecording();
            }}
            disabled={isUploading || isRecording}
          >
            ✍️ 文字输入
          </button>
        </div>

        {/* 语音输入区域 */}
        {inputMode === 'voice' && (
          <div className="recording-area">
            <button
              className={`record-button ${isRecording ? 'recording' : ''}`}
              onClick={handleRecord}
              disabled={isUploading}
            >
              {isRecording ? '🛑 停止录音' : '🎤 开始录音'}
            </button>
            {isRecording && (
              <div className="recording-indicator">
                <span className="pulse-dot"></span>
                正在录音...
              </div>
            )}
            {audioBlob && !isRecording && (
              <div className="audio-preview">
                <p>录音完成 ✓</p>
                <audio src={URL.createObjectURL(audioBlob)} controls />
              </div>
            )}
          </div>
        )}

        {/* 文本输入区域 */}
        {inputMode === 'text' && (
          <div className="text-input-area">
            <textarea
              className="story-textarea"
              placeholder="在这里输入您的故事...&#10;&#10;例如：今天工作很累，但想到即将到来的周末，心情又好了起来。"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              disabled={isUploading}
              rows={8}
            />
            <div className="text-input-hint">
              <p>💡 提示：请详细描述您的心情、经历或感受，这样我们可以为您推荐最合适的鸡尾酒</p>
            </div>
          </div>
        )}

        <button
          className="submit-button"
          onClick={handleSubmit}
          disabled={!canSubmit || isUploading || isRecording}
        >
          {isUploading ? '提交中...' : '提交'}
        </button>
      </div>
    </div>
  );
};

export default VoiceInputScreen;
