"use client";

import { useState, useEffect, useRef } from "react";
import Lottie from "lottie-react";
import medBotAnimation from "../app/animations/med-bot.json";
import DoctorCard from "./DoctorCard";
import ResourceCard from "./ResourceCard"; // ✅ Import ResourceCard

// Typing Indicator Component
const TypingIndicator = () => {
  return (
    <div className="chat-message bot-message">
      <div className="message-content typing-indicator">
        <div className="typing-dots">
          <div className="typing-dot"></div>
          <div className="typing-dot"></div>
          <div className="typing-dot"></div>
        </div>
      </div>
    </div>
  );
};

export default function ChatInterface() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: "bot",
      content:
        "Hello! I'm your AI medical assistant. How can I help you today?",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const quickSuggestions = [
    "Find a cardiologist near me",
    "What are COVID-19 symptoms?",
    "Schedule a checkup",
    "Find urgent care centers",
  ];

  // Scroll to bottom when messages update
  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: "user",
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);
    setIsTyping(true);

    try {
      // Simulate typing delay
      await new Promise((resolve) => setTimeout(resolve, 1500));

      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: userMessage.content }),
      });

      let botResponse,
        therapists = [],
        resources = [];
      if (response.ok) {
        const data = await response.json();
        console.log("🔍 Full API Response:", data);

        botResponse =
          data.response ||
          "I apologize, but I couldn't generate a proper response at this time.";
        therapists = data.therapists || [];
        resources = data.resources || [];

        console.log("👥 Therapists found:", therapists.length);
        console.log("📚 Resources found:", resources.length);
      } else {
        throw new Error("API request failed");
      }

      setIsTyping(false);

      const botMessage = {
        id: Date.now() + 1,
        type: "bot",
        content: botResponse,
        therapists,
        resources,
        timestamp: new Date(),
      };

      console.log("💬 Bot message with data:", botMessage);
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("❌ Error in handleSendMessage:", error);
      setIsTyping(false);
      const fallbackMessage = {
        id: Date.now() + 1,
        type: "bot",
        content:
          "I'm currently experiencing technical difficulties. Please try again later or contact your healthcare provider directly.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, fallbackMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setInputValue(suggestion);
  };

  return (
    <div className="chat-container">
      {/* Header */}
      <div className="chat-header glass">
        <div className="header-content">
          <div className="logo-section">
            <div className="logo">
              <Lottie
                animationData={medBotAnimation}
                loop={true}
                style={{ width: 64, height: 64 }}
              />
            </div>
            <div className="logo-text">
              <h1 className="app-title text-glow">Med-Bot</h1>
              <p className="app-subtitle">AI Medical Assistant</p>
            </div>
          </div>
          <div className="status-indicators">
            <div className="status-item">
              <span className="status-dot online"></span>
              <span>Online</span>
            </div>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="messages-container">
        <div className="messages-list">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`chat-message ${message.type}-message message-animation`}
            >
              <div className="message-content">
                <p>{message.content}</p>

                {/* ✅ Render therapist cards if available */}
                {message.therapists && message.therapists.length > 0 && (
  <div className="doctors-container mt-4 space-y-4">
    <div className="text-sm text-gray-600 mb-3 font-medium">
      Found {message.therapists.length} healthcare provider(s):
    </div>
    {message.therapists.map((therapist, index) => (
      <DoctorCard
        key={`${message.id}-therapist-${index}`}
        name={therapist.provider_name || "N/A"}
        providerType={therapist.provider_type || "Therapist"}
        address={therapist.address || ""}
        city={therapist.city || ""}
        state={therapist.state || ""}
        email={therapist.email || "Not provided"}
      />
    ))}
  </div>
)}


                {/* ✅ Render resource cards if available */}
                {message.resources && message.resources.length > 0 && (
                  <div className="resources-container mt-4 space-y-4">
                    <div className="text-sm text-gray-600 mb-3 font-medium">
                      Found {message.resources.length} resource(s):
                    </div>
                    {message.resources.map((resource, index) => (
                      <ResourceCard
                        key={`${message.id}-resource-${index}`}
                        title={resource.title}
                        url={resource.url}
                        content={resource.content}
                      />
                    ))}
                  </div>
                )}

                <span className="message-timestamp">
                  {message.timestamp.toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
              </div>
            </div>
          ))}
          {isTyping && <TypingIndicator />}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Quick Suggestions */}
      <div className="suggestions-container">
        <div className="suggestions-list">
          {quickSuggestions.map((suggestion, index) => (
            <button
              key={index}
              className="suggestion-button card-hover"
              onClick={() => handleSuggestionClick(suggestion)}
              disabled={isLoading}
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>

      {/* Input Area */}
      <div className="input-container glass">
        <div className="input-wrapper">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your medical question here..."
            className="message-input input-focus"
            maxLength={500}
            rows={1}
            disabled={isLoading}
          />
          <div className="input-controls">
            <span className="character-counter">{inputValue.length}/500</span>
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isLoading}
              className="send-button btn-hover"
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22,2 15,22 11,13 2,9"></polygon>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
