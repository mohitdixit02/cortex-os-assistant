"use client";

import React from "react";
import { motion } from "framer-motion";
import { AIState } from "./socket/types";

interface AssistantOrbProps {
  aiState: AIState;
}

export default function AssistantOrb3D({ aiState }: AssistantOrbProps) {
  // Speed and scale based on assistant state
  // STANDBY: 12s, LISTENING: 6s, SPEAKING: 3s, ANALYZING/PROCESSING: 1.5s
  const rotationDuration = 
    aiState === AIState.STANDBY ? 12 :
    aiState === AIState.LISTENING ? 6 :
    aiState === AIState.SPEAKING ? 3 : 1.5;
  
  // Pulsing scale
  const pulseScale = 
    aiState === AIState.SPEAKING ? [1, 1.15, 1] :
    (aiState === AIState.ANALYZING || aiState === AIState.PROCESSING) ? [1, 1.04, 1] :
    aiState === AIState.LISTENING ? [1, 1.08, 1] : [1, 1.02, 1];

  const pulseDuration = 
    aiState === AIState.SPEAKING ? 0.4 :
    (aiState === AIState.ANALYZING || aiState === AIState.PROCESSING) ? 0.8 :
    aiState === AIState.LISTENING ? 1.2 : 2.5;

  // Distortion animation (blob effect) speed
  const distortionDuration = 
    (aiState === AIState.SPEAKING || aiState === AIState.ANALYZING || aiState === AIState.PROCESSING) ? 2 :
    aiState === AIState.LISTENING ? 4 : 6;

  // Color shift: Listening -> Cyan, Speaking -> Pink, Others -> Mix
  const gradientColors = 
    aiState === AIState.LISTENING 
      ? "#00f2ff, #7950c7, #00f2ff, #7950c7, #00f2ff" 
      : aiState === AIState.SPEAKING 
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
          boxShadow: aiState === AIState.LISTENING 
            ? "0 0 40px rgba(0, 242, 255, 0.5)" 
            : aiState === AIState.SPEAKING 
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
