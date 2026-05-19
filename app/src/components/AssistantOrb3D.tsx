"use client";

import React from "react";
import { motion } from "framer-motion";

interface AssistantOrbProps {
  isListening: boolean;
  isSpeaking: boolean;
  isThinking?: boolean;
}

export default function AssistantOrb3D({ isListening, isSpeaking, isThinking = false }: AssistantOrbProps) {
  // Speed and scale based on assistant state
  // Idle: 12s, Listening: 6s, Thinking: 1.5s (Rapid), Speaking: 3s
  const rotationDuration = isThinking ? 1.5 : isSpeaking ? 3 : isListening ? 6 : 12;
  
  // Pulsing scale
  const pulseScale = isSpeaking ? [1, 1.15, 1] : isThinking ? [1, 1.04, 1] : isListening ? [1, 1.08, 1] : [1, 1.02, 1];
  const pulseDuration = isSpeaking ? 0.4 : isThinking ? 0.8 : isListening ? 1.2 : 2.5;

  // Distortion animation (blob effect) speed
  const distortionDuration = isSpeaking || isThinking ? 2 : isListening ? 4 : 6;

  // Color shift: Listening -> more Cyan, Speaking -> more Pink, Thinking -> Mix
  const gradientColors = isListening 
    ? "#00f2ff, #7950c7, #00f2ff, #7950c7, #00f2ff" 
    : isSpeaking 
    ? "#ff00e5, #7950c7, #ff00e5, #7950c7, #ff00e5" 
    : "#00f2ff, #ff00e5, #00f2ff, #ff00e5, #00f2ff";

  const distortion = [
    "50% 50% 50% 50% / 50% 50% 50% 50%",
    "48% 52% 51% 49% / 51% 48% 52% 49%",
    "52% 48% 49% 51% / 49% 52% 48% 51%",
    "50% 52% 48% 50% / 52% 50% 50% 48%",
    "50% 50% 50% 50% / 50% 50% 50% 50%"
  ];

  return (
    <div style={{ 
      width: "100%", 
      height: "100%", 
      display: "flex", 
      alignItems: "center", 
      justifyContent: "center",
      minHeight: "400px"
    }}>
      <motion.div
        animate={{ 
          rotate: 360,
          scale: pulseScale,
          borderRadius: distortion
        }}
        transition={{
          rotate: {
            duration: rotationDuration,
            repeat: Infinity,
            ease: "linear"
          },
          scale: {
            duration: pulseDuration,
            repeat: Infinity,
            ease: "easeInOut"
          },
          borderRadius: {
            duration: distortionDuration,
            repeat: Infinity,
            ease: "easeInOut"
          }
        }}
        style={{
          width: "240px",
          height: "240px",
          padding: "25px", // Thickness of the gradient ring
          background: `conic-gradient(from 0deg, ${gradientColors})`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: isListening 
            ? "0 0 40px rgba(0, 242, 255, 0.5)" 
            : isSpeaking 
            ? "0 0 40px rgba(255, 0, 229, 0.5)" 
            : "0 0 30px rgba(255, 255, 255, 0.1)",
          position: "relative",
          overflow: "hidden",
          transition: "box-shadow 0.5s ease"
        }}
      >
        {/* Inner Circle - Black center with matching distortion */}
        <motion.div 
          animate={{ borderRadius: distortion }}
          transition={{
            duration: distortionDuration,
            repeat: Infinity,
            ease: "easeInOut"
          }}
          style={{
            width: "100%",
            height: "100%",
            background: "#000000"
          }} 
        />
      </motion.div>
    </div>
  );
}
