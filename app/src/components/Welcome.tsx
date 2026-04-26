"use client";

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppContext } from './AppContext';
import { FaMicrophone, FaBrain, FaHistory, FaCog, FaUser, FaRocket, FaShieldAlt } from 'react-icons/fa';

const cards = [
  {
    title: "Welcome to Cortex",
    description: "Your advanced AI voice assistant designed for seamless interaction.",
    icon: <FaRocket />,
    color: "from-purple-500 to-blue-500"
  },
  {
    title: "Voice Intelligence",
    description: "Natural language processing that understands your voice with high precision.",
    icon: <FaMicrophone />,
    color: "from-blue-500 to-cyan-500"
  },
  {
    title: "Memory Aware",
    description: "The assistant remembers your preferences and past interactions for better context.",
    icon: <FaBrain />,
    color: "from-purple-600 to-red-500"
  },
  {
    title: "Session History",
    description: "Access and review your previous conversations anytime in the history tab.",
    icon: <FaHistory />,
    color: "from-red-500 to-orange-500"
  },
  {
    title: "Customizable Experience",
    description: "Tweak voice, language, and behavior in the settings to suit your needs.",
    icon: <FaCog />,
    color: "from-orange-500 to-yellow-500"
  },
  {
    title: "Privacy Focused",
    description: "Your data is handled with care, ensuring a secure and private environment.",
    icon: <FaShieldAlt />,
    color: "from-green-500 to-teal-500"
  },
  {
    title: "Ready to Start?",
    description: "Click get started to begin your journey with your new AI companion.",
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
      justifyContent: 'center',
      background: 'var(--background)',
      overflow: 'hidden'
    }}>
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
                background: i === current ? 'var(--accent-purple)' : '#333',
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
