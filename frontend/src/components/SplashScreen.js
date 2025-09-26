'use client';

import { useEffect, useState } from 'react';
import Lottie from 'lottie-react';


export default function SplashScreen({ onComplete }) {
  const [animationData, setAnimationData] = useState(null);
  const [showHeading, setShowHeading] = useState(false);
  const [showLoading, setShowLoading] = useState(false);

  const headingText =
    'Med-Bot: your AI assistant to find the best doctors for you.';

  useEffect(() => {
    const loadAnimation = async () => {
      try {
        const response = await fetch('/animations/med-bot.json');
        if (response.ok) {
          const data = await response.json();
          setAnimationData(data);

          // Show heading shortly after animation starts
          setTimeout(() => setShowHeading(true), 1800);

          // Show loading after heading
          setTimeout(() => setShowLoading(true), 2800);

          // Finish splash after delay (ensures animation completes)
          setTimeout(() => {
            onComplete();
          }, 5000);
        } else {
          throw new Error('Animation file not found');
        }
      } catch (error) {
        console.error('⚠️ Failed to load Lottie animation:', error.message);
      }
    };

    loadAnimation();
  }, [onComplete]);

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-app-medical text-center min-h-screen z-50">
      <div className="relative flex items-center justify-center">
        {animationData && (
          <div className="w-[380px] h-[380px] md:w-[460px] md:h-[460px] mt-[-4rem]">
            <Lottie
              animationData={animationData}
              loop={false}
              autoplay
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        )}

        {/* Heading positioned absolutely below animation, single line */}
        {showHeading && (
          <h1 className="absolute top-[calc(100%+1rem)] text-2xl md:text-4xl font-bold text-[#0f172a] max-w-xl leading-relaxed tracking-wide text-glow fade-slide whitespace-nowrap">
            {headingText}
          </h1>
        )}

        {/* Loading text positioned absolutely further below */}
        {showLoading && (
          <p className="absolute top-[calc(100%+4rem)] text-sm md:text-base text-[#486581] tracking-[0.25em] fade-in animate-pulse-subtle">
            Loading…
          </p>
        )}
      </div>
    </div>
  );
}