import React from 'react';
import './WelcomeScreen.css';

interface WelcomeScreenProps {
  onStart: () => void;
}

const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onStart }) => {
  return (
    <div className="welcome-screen">
      <div className="welcome-content">
        <h1 className="welcome-title">情感鸡尾酒推荐系统</h1>
        <p className="welcome-subtitle">分享你的故事，我们为你调制专属鸡尾酒</p>
        <button className="start-button" onClick={onStart}>
          来一杯吧
        </button>
      </div>
    </div>
  );
};

export default WelcomeScreen;
