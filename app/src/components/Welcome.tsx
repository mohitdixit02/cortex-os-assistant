"use client";

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppContext } from './AppContext';
import { FaBrain, FaHistory, FaCog, FaUser, FaRocket, FaSync, FaLightbulb } from 'react-icons/fa';
import CortexFullLogo from "../../public/assets/CortexAI full.png";
import Image from 'next/image';

const cards = [
  {
    title: "Your Proactive Companion",
    description: "Cortex is a memory-aware OS assistant that understands your history and behaviours.",
    icon: <FaRocket />,
    color: "from-purple-500 to-blue-500"
  },
  {
    title: "Non-Blocking Reasoning",
    description: "Ask follow-up questions while I'm thinking. I handle parallel queries without ever pausing our conversation.",
    icon: <FaSync />,
    color: "from-blue-500 to-cyan-500"
  },
  {
    title: "Emotionally Aligned",
    description: "I sense your mood and the time of day, adjusting my responses—from concise morning updates to relaxed evening chats.",
    icon: <FaLightbulb />,
    color: "from-purple-600 to-red-500"
  },
  {
    title: "Active Memory Building",
    description: "I learn your preferences and facts in real-time, building a persistent knowledge base that evolves with you.",
    icon: <FaBrain />,
    color: "from-red-500 to-orange-500"
  },
  {
    title: "Deep Thinking Workflows",
    description: "Utilizing advanced LangGraph orchestration to research, execute tools, and solve complex tasks for you.",
    icon: <FaCog />,
    color: "from-orange-500 to-yellow-500"
  },
  {
    title: "Smart Scheduling",
    description: "Precision reminders that can wake your system to deliver critical updates.",
    icon: <FaHistory />,
    color: "from-green-500 to-teal-500"
  },
  {
    title: "Personalized Discovery",
    description: "Click get started to securely sign in and begin your journey with a truly personalized AI experience.",
    icon: <FaUser />,
    color: "from-indigo-500 to-purple-600"
  }
];

export default function Welcome() {
  const [current, setCurrent] = useState(0);
  const { setIsOnboarded } = useAppContext();

  const next = () => {
    if (current < cards.length - 1) {
      setCurrent(current + 1);
    } else {
      setIsOnboarded(true);
    }
  };

  return (
    <div className="welcome-container" style={{
      height: '100vh',
      width: '100vw',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'left',
      gap: '20%',
      background: '#523c5a37',
      overflow: 'hidden',
    }}>
      <div style={{
        position: 'relative',
        top: 0,
        left: 0,
        height: '100%',
        width: '35%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--primary-gradient-dark)',
        borderRadius: '0 30px 30px 0',
      }}>
        <Image src={CortexFullLogo} alt="Cortex Logo" width={480} objectFit='contain' />
      </div>
      <AnimatePresence mode="wait">
        <motion.div
          key={current}
          initial={{ opacity: 0, x: 100 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -100 }}
          transition={{ duration: 0.4 }}
          style={{
            width: '400px',
            padding: '40px',
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '20px'
          }}
          className="glass-card"
        >
          <div style={{
            fontSize: '60px',
            marginBottom: '20px',
            background: 'var(--primary-gradient)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            display: 'flex',
            justifyContent: 'center'
          }}>
            {cards[current].icon}
          </div>
          <h2 style={{ fontSize: '24px', fontWeight: 'bold' }}>{cards[current].title}</h2>
          <p style={{ color: 'var(--text-muted)', lineHeight: '1.6' }}>{cards[current].description}</p>
          
          <div style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>
            {cards.map((_, i) => (
              <div key={i} style={{
                width: i === current ? '24px' : '8px',
                height: '8px',
                borderRadius: '4px',
                background: i === current ? 'var(--primary-gradient)' : '#333',
                transition: 'all 0.3s'
              }} />
            ))}
          </div>

          <button 
            onClick={next}
            style={{
              marginTop: '20px',
              padding: '12px 30px',
              borderRadius: '30px',
              background: 'var(--primary-gradient)',
              color: 'white',
              fontWeight: '600',
              fontSize: '16px',
              boxShadow: '0 4px 15px rgba(0,0,0,0.3)'
            }}
          >
            {current === cards.length - 1 ? "Get Started" : "Next"}
          </button>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
