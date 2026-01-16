import React, { useState } from 'react';
import { ProcessingResult } from '../services/api';
import './ResultCard.css';

interface ResultCardProps {
  result: ProcessingResult;
  onRestart: () => void;
}

const ResultCard: React.FC<ResultCardProps> = ({ result, onRestart }) => {
  const cocktailName = result.presentation?.cocktail_name || '心灵之酒';
  const simplifiedResponse = result.layout?.simplified_response || '';
  // 优先使用最终名片，如果没有则使用最终呈现图片，再没有则使用鸡尾酒图片
  const cardImageUrl = result.layout?.final_card_url || 
                       result.layout?.ink_style_image_url ||
                       result.presentation?.final_presentation_image_url || 
                       result.presentation?.cocktail_image_url || 
                       '';
  const [isDownloading, setIsDownloading] = useState(false);

  // 调试信息和图片URL验证
  React.useEffect(() => {
    console.log('ResultCard Debug Info:', {
      hasLayout: !!result.layout,
      layoutFinalCardUrl: result.layout?.final_card_url,
      layoutInkStyleUrl: result.layout?.ink_style_image_url,
      hasPresentation: !!result.presentation,
      presentationFinalImageUrl: result.presentation?.final_presentation_image_url,
      presentationCocktailImageUrl: result.presentation?.cocktail_image_url,
      finalCardImageUrl: cardImageUrl,
      cardImageUrlEmpty: !cardImageUrl,
      fullResult: result
    });
    
    // 如果cardImageUrl存在但以http开头，验证URL是否可访问
    if (cardImageUrl && cardImageUrl.startsWith('http')) {
      console.log('验证图片URL可访问性:', cardImageUrl);
      fetch(cardImageUrl, { method: 'HEAD', mode: 'no-cors' })
        .then(() => console.log('图片URL可访问'))
        .catch((err) => console.warn('图片URL可能不可访问:', err));
    }
  }, [result, cardImageUrl]);

  const handleDownload = async () => {
    if (!cardImageUrl) {
      alert('名片图片未准备好，请稍候再试');
      return;
    }

    if (isDownloading) {
      return; // 防止重复点击
    }

    setIsDownloading(true);

    try {
      // 如果cardImageUrl是相对路径，需要转换为完整URL
      const fullUrl = cardImageUrl.startsWith('http') 
        ? cardImageUrl 
        : `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}${cardImageUrl}`;
      
      // 使用fetch获取图片，解决跨域问题
      const response = await fetch(fullUrl, {
        mode: 'cors',
        credentials: 'omit'
      });
      
      if (!response.ok) {
        throw new Error(`下载失败: ${response.status} ${response.statusText}`);
      }
      
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = `${cocktailName}_名片.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // 清理blob URL
      setTimeout(() => {
        window.URL.revokeObjectURL(blobUrl);
      }, 100);
    } catch (error) {
      console.error('下载失败:', error);
      alert(`下载失败: ${error instanceof Error ? error.message : '未知错误'}`);
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="result-card-screen">
      <div className="result-card-content">
        <h2 className="result-title">您的专属鸡尾酒</h2>
        
        <div className="card-display">
          {cardImageUrl ? (
            <img 
              src={cardImageUrl.startsWith('http') 
                ? cardImageUrl 
                : `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}${cardImageUrl}`}
              alt={cocktailName}
              className="card-image"
              onError={(e) => {
                console.error('图片加载失败:', cardImageUrl);
                const img = e.target as HTMLImageElement;
                img.style.display = 'none';
                // 显示错误提示
                const errorDiv = document.createElement('div');
                errorDiv.className = 'image-error';
                errorDiv.textContent = '图片加载失败';
                errorDiv.style.cssText = 'padding: 1rem; color: #dc2626; text-align: center;';
                img.parentElement?.appendChild(errorDiv);
              }}
              onLoad={() => {
                console.log('图片加载成功:', cardImageUrl);
              }}
            />
          ) : (
            <div className="no-image-placeholder" style={{
              padding: '2rem',
              textAlign: 'center',
              color: '#6b7280',
              backgroundColor: '#f3f4f6',
              borderRadius: '10px',
              border: '2px dashed #d1d5db'
            }}>
              <p>暂无图片</p>
              <small>图片生成中或生成失败</small>
            </div>
          )}
          
          <div className="card-text-content">
            <h3 className="cocktail-name">{cocktailName}</h3>
            <p className="card-message">{simplifiedResponse}</p>
          </div>
        </div>

        {result.presentation?.user_response && (
          <div className="full-response">
            <h4>完整回复：</h4>
            <p>{result.presentation.user_response}</p>
          </div>
        )}

        {result.cocktail_mix && (
          <div className="cocktail-info">
            <h4>鸡尾酒配方：</h4>
            <p><strong>基础：</strong>{result.cocktail_mix.base_cocktail?.name}</p>
            <p><strong>定制配方：</strong>{result.cocktail_mix.customized_recipe}</p>
            {result.cocktail_mix.adjustment_rationale && (
              <p><strong>调配理念：</strong>{result.cocktail_mix.adjustment_rationale}</p>
            )}
          </div>
        )}

        <div className="result-actions">
          <button 
            className="download-button" 
            onClick={handleDownload}
            disabled={isDownloading || !cardImageUrl}
            title={!cardImageUrl ? '名片图片未准备好' : '下载名片'}
          >
            {isDownloading ? '下载中...' : (!cardImageUrl ? '图片未准备好' : '下载名片')}
          </button>
          <button className="restart-button" onClick={onRestart}>
            再来一杯
          </button>
        </div>
        {!cardImageUrl && (
          <div style={{ marginTop: '1rem', padding: '0.5rem', background: '#fff3cd', borderRadius: '5px', color: '#856404' }}>
            <small>提示：名片图片正在生成中，如果没有图片URL，可能是生成失败或仍在处理中。</small>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResultCard;
