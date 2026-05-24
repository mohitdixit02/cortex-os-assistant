"use client";

import React, { useEffect, useRef, useTransition } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FaPlus, FaChevronDown, FaCommentAlt } from 'react-icons/fa';
import { useAppContext } from './AppContext';
import { useThreads, ChatThread } from '../hooks/useApi';
import { apiClient } from '../utility/apiClient';

export default function ThreadSelector() {
  const { activeThreadId, setActiveThreadId } = useAppContext();
  const { threads, mutate } = useThreads();
  const [isOpen, setIsOpen] = React.useState(false);

  const activeThread = threads?.find(t => t.session_id === activeThreadId);

  const handleCreateThread = async () => {
    try {
      const newThread = await apiClient<ChatThread>('/api/v1/chat/threads', { method: 'POST' });
      mutate([...(threads || []), newThread]);
      setActiveThreadId(newThread.session_id);
      setIsOpen(false);
    } catch (err) {
      console.error("Failed to create thread", err);
    }
  };

  const handleSelectThread = (id: string) => {
    setActiveThreadId(id);
    setIsOpen(false);
  };

  useEffect(() => {
    const setDefaultThread = async () => {
      console.log("enetered");
      console.log("activeThreadId:", activeThreadId);
      if (activeThreadId) return;
      if (!threads) return;
      if (threads.length > 0) {
        setActiveThreadId(threads[0].session_id);
      } else {
        console.log("No threads found, creating default thread");
        await handleCreateThread();
      }
    };
    setDefaultThread();
  }, [threads]);

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '12px 18px',
          borderRadius: '14px',
          background: 'rgba(255,255,255,0.03)',
          border: '1px solid rgba(255,255,255,0.08)',
          color: 'white',
          fontSize: '15px',
          fontWeight: '600',
          cursor: 'pointer',
          width: '100%',
          justifyContent: 'space-between',
          transition: 'all 0.2s'
        }}
        onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.06)'}
        onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ 
            width: '32px', 
            height: '32px', 
            borderRadius: '10px', 
            background: 'rgba(0,242,255,0.1)', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center' 
          }}>
            <FaCommentAlt size={14} color="var(--accent-primary)" />
          </div>
          <span style={{ maxWidth: '220px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {activeThread?.summary || "New Conversation"}
          </span>
        </div>
        <FaChevronDown size={12} style={{ transform: isOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s', opacity: 0.5 }} />
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            <div
              style={{ position: 'fixed', inset: 0, zIndex: 998 }}
              onClick={() => setIsOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              style={{
                position: 'absolute',
                top: 'calc(100% + 12px)',
                right: 0,
                width: '380px',
                background: 'rgba(25, 25, 25, 0.95)',
                backdropFilter: 'blur(30px)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '20px',
                boxShadow: '0 25px 50px rgba(0,0,0,0.7)',
                zIndex: 1000,
                overflow: 'hidden',
                maxHeight: '480px',
                display: 'flex',
                flexDirection: 'column',
                padding: '12px'
              }}
            >
              {/* Sleek New Thread Button */}
              <button
                onClick={handleCreateThread}
                className="btn-neon-primary"
                style={{
                  width: '100%',
                  padding: '14px 20px',
                  borderRadius: '14px',
                  marginBottom: '15px'
                }}
              >
                <FaPlus size={14} />
                <span>New Conversation</span>
              </button>

              <div style={{ 
                fontSize: '11px', 
                fontWeight: '800', 
                color: 'rgba(255,255,255,0.3)', 
                textTransform: 'uppercase', 
                letterSpacing: '1.5px',
                marginBottom: '12px',
                paddingLeft: '8px'
              }}>
                Recent Sessions
              </div>

              <div style={{ overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '8px', paddingRight: '5px' }}>
                {threads?.map((thread) => (
                  <button
                    key={thread.session_id}
                    onClick={() => handleSelectThread(thread.session_id)}
                    style={{
                      width: '100%',
                      textAlign: 'left',
                      padding: '12px 15px',
                      borderRadius: '12px',
                      color: activeThreadId === thread.session_id ? 'white' : 'var(--text-muted)',
                      background: activeThreadId === thread.session_id ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.02)',
                      border: activeThreadId === thread.session_id ? '1px solid rgba(255,255,255,0.1)' : '1px solid transparent',
                      transition: 'all 0.2s',
                      cursor: 'pointer'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.06)'}
                    onMouseLeave={(e) => {
                      if (activeThreadId !== thread.session_id) {
                        e.currentTarget.style.background = 'rgba(255,255,255,0.02)';
                      } else {
                        e.currentTarget.style.background = 'rgba(255,255,255,0.08)';
                      }
                    }}
                  >
                    <div style={{ fontWeight: '600', fontSize: '14px', marginBottom: '4px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {thread.summary || "Conversation Session"}
                    </div>
                    <div style={{ fontSize: '11px', opacity: 0.6 }}>
                      {new Date(thread.created_at).toLocaleDateString(undefined, { month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </button>
                ))}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
