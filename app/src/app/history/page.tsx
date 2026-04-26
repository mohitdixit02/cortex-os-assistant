"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { FaHistory, FaCalendarAlt, FaChevronRight } from 'react-icons/fa';

const historyData = [
  { id: 1, title: "Weather in London", date: "2 hours ago", type: "Query" },
  { id: 2, title: "Summarize the project document", date: "5 hours ago", type: "Task" },
  { id: 3, title: "Set a reminder for 6 PM", date: "Yesterday", type: "Action" },
  { id: 4, title: "How does React Context work?", date: "Yesterday", type: "Query" },
  { id: 5, title: "Draft an email to the team", date: "2 days ago", type: "Task" },
];

export default function History() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      style={{ maxWidth: '800px', margin: '0 auto' }}
    >
      <div style={{ marginBottom: '40px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '10px' }}>Interaction <span className="gradient-text">History</span></h1>
        <p style={{ color: 'var(--text-muted)' }}>Review your past conversations and sessions with Cortex.</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
        {historyData.map((item, index) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="glass-card"
            style={{
              padding: '20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              cursor: 'pointer',
              transition: 'background 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
            onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
              <div style={{ 
                width: '50px', 
                height: '50px', 
                borderRadius: '12px', 
                background: 'var(--primary-gradient)', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                fontSize: '20px'
              }}>
                <FaHistory color="white" />
              </div>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '4px' }}>{item.title}</h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '14px', color: 'var(--text-muted)' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <FaCalendarAlt size={12} /> {item.date}
                  </span>
                  <span>•</span>
                  <span>{item.type}</span>
                </div>
              </div>
            </div>
            <FaChevronRight color="var(--text-muted)" />
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
