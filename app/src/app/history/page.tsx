"use client";

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FaHistory, FaCalendarAlt, FaChevronRight } from 'react-icons/fa';
import { useThreads } from '../../hooks/useApi';
import { useAppContext } from '../../components/AppContext';
import { useRouter } from 'next/navigation';
import { toast } from 'react-toastify';

export default function Conversations() {
  const { threads, isLoading: threadsLoading } = useThreads();
  const { setActiveThreadId, isConversationActive, setActiveOverlay } = useAppContext();
  const router = useRouter();

  const handleThreadClick = (id: string) => {
    if (isConversationActive) {
      toast.warn("Please stop the current conversation before switching sessions.");
      return;
    }
    setActiveThreadId(id);
    setActiveOverlay(null);
    router.push('/');
  };

  return (
    <div style={{
      height: '100%',
      overflowY: 'auto',
      padding: '40px'
    }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ maxWidth: '95%', margin: '0 auto' }}
      >
        <div style={{ marginBottom: '40px' }}>
          <h1 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '10px' }}><span className="gradient-text">Conversations</span></h1>
          <p style={{ color: 'var(--text-muted)' }}>Review your past conversations with Cortex.</p>
        </div>

        <AnimatePresence mode="wait">
            <motion.div
              key="conversations"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}
            >
              {threadsLoading ? (
                <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading conversations...</div>
              ) : threads?.length === 0 ? (
                <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>No conversations yet.</div>
              ) : threads?.map((thread, index) => (
                <motion.div
                  key={thread.session_id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="glass-card"
                  onClick={() => handleThreadClick(thread.session_id)}
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
                    <div 
                      className="icon-glass-container"
                      style={{ 
                        width: '45px', 
                        height: '45px', 
                        fontSize: '16px'
                      }}
                    >
                      <FaHistory color="var(--accent-primary)" />
                    </div>
                    <div>
                      <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '4px' }}>{thread.display_title || "New Conversation"}</h3>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '12px', color: 'var(--text-muted)' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                          <FaCalendarAlt size={12} /> {new Date(thread.created_at).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  <FaChevronRight color="var(--text-muted)" />
                </motion.div>
              ))}
            </motion.div>
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
