"use client";

import React from 'react';
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

  return (
    <div style={{ position: 'relative' }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '8px 16px',
          borderRadius: '12px',
          background: 'rgba(255,255,255,0.05)',
          border: '1px solid rgba(255,255,255,0.1)',
          color: 'white',
          fontSize: '14px',
          fontWeight: '500',
          cursor: 'pointer',
          minWidth: '200px',
          justifyContent: 'space-between'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FaCommentAlt size={14} color="var(--accent-purple)" />
          <span style={{ maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {activeThread?.summary || "New Conversation"}
          </span>
        </div>
        <FaChevronDown size={12} style={{ transform: isOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            <div 
              style={{ position: 'fixed', inset: 0, zIndex: 998 }} 
              onClick={() => setIsOpen(false)} 
            />
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              style={{
                position: 'absolute',
                top: 'calc(100% + 8px)',
                left: 0,
                width: '100%',
                background: '#1a1a1a',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '12px',
                boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
                zIndex: 999,
                overflow: 'hidden',
                maxHeight: '300px',
                display: 'flex',
                flexDirection: 'column'
              }}
            >
              <div style={{ padding: '8px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <button
                  onClick={handleCreateThread}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '10px',
                    borderRadius: '8px',
                    color: 'white',
                    fontSize: '14px',
                    background: 'var(--primary-gradient)',
                    fontWeight: '600'
                  }}
                >
                  <FaPlus size={12} /> New Thread
                </button>
              </div>

              <div style={{ overflowY: 'auto', flex: 1 }}>
                {threads?.map((thread) => (
                  <button
                    key={thread.session_id}
                    onClick={() => handleSelectThread(thread.session_id)}
                    style={{
                      width: '100%',
                      textAlign: 'left',
                      padding: '12px 16px',
                      color: activeThreadId === thread.session_id ? 'white' : 'var(--text-muted)',
                      background: activeThreadId === thread.session_id ? 'rgba(255,255,255,0.05)' : 'transparent',
                      fontSize: '14px',
                      borderBottom: '1px solid rgba(255,255,255,0.03)',
                      transition: 'all 0.2s',
                      display: 'block',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
                    onMouseLeave={(e) => {
                      if (activeThreadId !== thread.session_id) {
                        e.currentTarget.style.background = 'transparent';
                      } else {
                        e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
                      }
                    }}
                  >
                    {thread.summary || "Conversation from " + new Date(thread.created_at).toLocaleDateString()}
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
