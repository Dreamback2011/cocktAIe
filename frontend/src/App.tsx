import React, { useState } from 'react';
import WelcomeScreen from './components/WelcomeScreen';
import VoiceInputScreen from './components/VoiceInputScreen';
import LoadingScreen from './components/LoadingScreen';
import ResultCard from './components/ResultCard';
import { ProcessingResult } from './services/api';
import './App.css';

type Screen = 'welcome' | 'voice' | 'loading' | 'result';

function App() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('welcome');
  const [taskId, setTaskId] = useState<string>('');
  const [result, setResult] = useState<ProcessingResult | null>(null);

  const handleStart = () => {
    setCurrentScreen('voice');
  };

  const handleBack = () => {
    setCurrentScreen('welcome');
  };

  const handleRecordingComplete = (newTaskId: string) => {
    setTaskId(newTaskId);
    setCurrentScreen('loading');
  };

  const handleLoadingComplete = (processingResult: ProcessingResult) => {
    setResult(processingResult);
    setCurrentScreen('result');
  };

  const handleRestart = () => {
    setCurrentScreen('welcome');
    setTaskId('');
    setResult(null);
  };

  return (
    <div className="App">
      {currentScreen === 'welcome' && <WelcomeScreen onStart={handleStart} />}
      {currentScreen === 'voice' && (
        <VoiceInputScreen
          onRecordingComplete={handleRecordingComplete}
          onBack={handleBack}
        />
      )}
      {currentScreen === 'loading' && taskId && (
        <LoadingScreen
          taskId={taskId}
          onComplete={handleLoadingComplete}
        />
      )}
      {currentScreen === 'result' && result && (
        <ResultCard result={result} onRestart={handleRestart} />
      )}
    </div>
  );
}

export default App;
