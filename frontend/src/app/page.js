'use client';

import { useState } from 'react';
import SplashScreen from '@/components/SplashScreen';
import ChatInterface from '@/components/ChatInterface';

export default function HomePage() {
  const [showSplash, setShowSplash] = useState(true);

  const handleSplashComplete = () => {
    setShowSplash(false);
  };

  return (
    <main className="h-screen overflow-hidden">
      {showSplash ? (
        <SplashScreen onComplete={handleSplashComplete} />
      ) : (
        <ChatInterface />
      )}
    </main>
  );
}