"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useWebSocket } from "../components/socket/WebSocket";
import { AIState } from "../components/socket/types";
import { motion, AnimatePresence } from "framer-motion";
import { FaStop, FaPlay, FaSync } from "react-icons/fa";
import AssistantOrb3D from "../components/AssistantOrb3D";
import ChatHistory from "../components/ChatHistory";
import { useAppContext } from "../components/AppContext";
import { useMessages } from "../hooks/useApi";

import ThreadSelector from "../components/ThreadSelector";
import { FaEdit, FaCheck, FaTimes as FaCancel } from "react-icons/fa";
import { apiClient } from "../utility/apiClient";
import { useThreads } from "../hooks/useApi";

export default function Home() {
  const { user, activeThreadId } = useAppContext();
  const { messages, mutate: mutateMessages, isLoading: messagesLoading } = useMessages(activeThreadId);
  const { threads, mutate: mutateThreads } = useThreads();

  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [hoveredButton, setHoveredButton] = useState<string | null>(null);

  const activeThread = threads?.find(t => t.session_id === activeThreadId);

  const handleStartEdit = () => {
    setNewTitle(activeThread?.display_title || "");
    setIsEditingTitle(true);
  };

  const handleSaveTitle = async () => {
    if (!activeThreadId || !newTitle.trim()) return;
    try {
      await apiClient(`/api/v1/chat/threads/${activeThreadId}/summary`, {
        method: 'PUT',
        body: JSON.stringify({ summary: newTitle.trim() })
      });
      mutateThreads();
      setIsEditingTitle(false);
    } catch (err) {
      console.error("Failed to update thread summary", err);
    }
  };

  const backendUrl = useMemo(() => process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000", []);
  
  const {
    startAudioStream,
    endAudioStream,
    isConversationActive,
    aiState
  } = useWebSocket(backendUrl.replace(/^http/, "ws") + "/ws");

  return (
    <div style={{
      width: '100%',
      height: '100%',
      display: 'flex',
      overflow: 'hidden',
      padding: '25px',
      gap: '25px',
      position: 'relative'
    }}>
      {/* Left Area: Assistant Orb Section */}
      <div className="orb-parent-card" style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px',
        position: 'relative',
        height: '100%',
        overflow: 'hidden'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '30px' }}>
          <motion.h1 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ fontSize: '42px', fontWeight: '800', letterSpacing: '-0.5px' }}
          >
            Hello, <span className="gradient-text">{`I'm Cortex`}</span>
          </motion.h1>
          <motion.p
            key={aiState}
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ 
              fontSize: '18px', 
              fontWeight: '500', 
              color: 'var(--text-muted)',
              marginTop: '8px',
              textTransform: 'uppercase',
              letterSpacing: '2px'
            }}
          >
            {aiState === AIState.LISTENING && "Listening..."}
            {aiState === AIState.SPEAKING && "Speaking..."}
            {aiState === AIState.ANALYZING && "Analyzing..."}
            {aiState === AIState.PROCESSING && "Thinking..."}
            {aiState === AIState.STANDBY && "Standby"}
          </motion.p>
        </div>

        <div style={{
          width: '100%', 
          maxWidth: '500px',
          height: '400px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          position: 'relative'
        }}>
          <AssistantOrb3D 
            aiState={aiState}
          />
        </div>

        <div style={{ marginTop: '40px' }}>
          {!isConversationActive ? (
            <motion.button 
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => startAudioStream(activeThreadId)}
              className="btn-neon-purple-gradient"
            >
              <FaPlay size={14} /> Start Conversation
            </motion.button>
          ) : (
            <motion.button 
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={endAudioStream}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '16px 36px',
                borderRadius: '50px',
                background: 'rgba(255, 255, 255, 0.05)',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: 'white',
                fontSize: '17px',
                fontWeight: '600',
                cursor: 'pointer'
              }}
            >
              <FaStop size={14} /> Stop Conversation
            </motion.button>
          )}
        </div>
      </div>

      {/* Right Area: Stacked Contextual Cards */}
      <div style={{
        width: '420px',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
        height: '100%'
      }}>
        {/* Header Card: Thread Management */}
        <div className="glass-parent" style={{ padding: '20px', zIndex: 50, position: 'relative' }}>
          <div style={{ marginBottom: '15px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontWeight: '800', fontSize: '14px', letterSpacing: '1px', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
              Current Session
            </span>
            <div style={{ color: 'var(--text-muted)', fontSize: '11px' }}>
              {new Date().toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
            </div>
          </div>
          <ThreadSelector />
        </div>

        {/* Chat Card: Conversation History */}
        <div className="glass-parent" style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}>
          <div style={{
            padding: '20px 25px',
            borderBottom: '1px solid rgba(255,255,255,0.05)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'rgba(255,255,255,0.01)',
            minHeight: '73px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1, overflow: 'hidden' }}>
              {isEditingTitle ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', width: '100%' }}>
                  <input
                    autoFocus
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleSaveTitle();
                      if (e.key === 'Escape') setIsEditingTitle(false);
                    }}
                    style={{
                      background: 'rgba(255,255,255,0.05)',
                      border: '1px solid var(--accent-primary)',
                      borderRadius: '8px',
                      color: 'white',
                      padding: '6px 12px',
                      fontSize: '16px',
                      fontWeight: '600',
                      width: '100%',
                      outline: 'none',
                      boxShadow: '0 0 15px rgba(0,242,255,0.1)'
                    }}
                  />
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button onClick={handleSaveTitle} style={{ 
                      color: 'var(--accent-primary)', 
                      background: 'rgba(0,242,255,0.1)', 
                      border: '1px solid rgba(0,242,255,0.2)', 
                      borderRadius: '8px',
                      padding: '8px',
                      cursor: 'pointer',
                      display: 'flex'
                    }}>
                      <FaCheck size={14} />
                    </button>
                    <button onClick={() => setIsEditingTitle(false)} style={{ 
                      color: '#ff4d4d', 
                      background: 'rgba(255,77,77,0.1)', 
                      border: '1px solid rgba(255,77,77,0.2)', 
                      borderRadius: '8px',
                      padding: '8px',
                      cursor: 'pointer',
                      display: 'flex'
                    }}>
                      <FaCancel size={14} />
                    </button>
                  </div>
                </div>
              ) : (
                <span style={{ 
                  fontWeight: '800', 
                  fontSize: '18px', 
                  letterSpacing: '-0.5px',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}>
                  {activeThread?.display_title || "Conversation"}
                </span>
              )}
            </div>
            
            {!isEditingTitle && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginLeft: '20px' }}>
                <div style={{ position: 'relative' }}>
                  <button 
                    onClick={handleStartEdit}
                    onMouseEnter={() => setHoveredButton('edit')}
                    onMouseLeave={() => setHoveredButton(null)}
                    style={{ 
                      color: 'white', 
                      background: 'rgba(255,255,255,0.03)', 
                      padding: '8px', 
                      borderRadius: '10px',
                      display: 'flex',
                      cursor: 'pointer',
                      border: '1px solid rgba(255,255,255,0.05)',
                      transition: 'all 0.2s'
                    }}
                  >
                    <FaEdit size={14} />
                  </button>
                  <AnimatePresence>
                    {hoveredButton === 'edit' && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        style={{
                          position: 'absolute',
                          top: 'calc(100% + 10px)',
                          right: '0',
                          background: 'rgba(20, 20, 20, 0.95)',
                          backdropFilter: 'blur(10px)',
                          padding: '6px 12px',
                          borderRadius: '8px',
                          border: '1px solid rgba(255,255,255,0.1)',
                          color: 'white',
                          fontSize: '12px',
                          fontWeight: '600',
                          whiteSpace: 'nowrap',
                          pointerEvents: 'none',
                          boxShadow: '0 5px 15px rgba(0,0,0,0.3)',
                          zIndex: 100
                        }}
                      >
                        Edit Summary
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                <div style={{ position: 'relative' }}>
                  <button 
                    onClick={() => mutateMessages()}
                    onMouseEnter={() => setHoveredButton('refresh')}
                    onMouseLeave={() => setHoveredButton(null)}
                    disabled={messagesLoading}
                    style={{ 
                      color: 'white', 
                      background: 'rgba(255,255,255,0.03)', 
                      padding: '8px', 
                      borderRadius: '10px',
                      display: 'flex',
                      cursor: 'pointer',
                      border: '1px solid rgba(255,255,255,0.05)',
                      opacity: messagesLoading ? 0.5 : 1,
                      transition: 'all 0.2s'
                    }}
                  >
                    <FaSync size={14} className={messagesLoading ? 'spin' : ''} />
                  </button>
                  <AnimatePresence>
                    {hoveredButton === 'refresh' && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        style={{
                          position: 'absolute',
                          top: 'calc(100% + 10px)',
                          right: '0',
                          background: 'rgba(20, 20, 20, 0.95)',
                          backdropFilter: 'blur(10px)',
                          padding: '6px 12px',
                          borderRadius: '8px',
                          border: '1px solid rgba(255,255,255,0.1)',
                          color: 'white',
                          fontSize: '12px',
                          fontWeight: '600',
                          whiteSpace: 'nowrap',
                          pointerEvents: 'none',
                          boxShadow: '0 5px 15px rgba(0,0,0,0.3)',
                          zIndex: 100
                        }}
                      >
                        Refresh Messages
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </div>
            )}
          </div>

          <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <ChatHistory messages={messages} />
          </div>
        </div>
      </div>

      <style jsx global>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .spin {
          animation: spin 1s linear infinite;
        }
      `}</style>
    </div>
  );
}
