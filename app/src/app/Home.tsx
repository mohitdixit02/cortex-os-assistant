"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useWebSocket } from "../components/socket/WebSocket";
import { motion, AnimatePresence } from "framer-motion";
import { FaStop, FaPlay, FaSync } from "react-icons/fa";
import AssistantOrb3D from "../components/AssistantOrb3D";
import ChatHistory from "../components/ChatHistory";
import { useAppContext } from "../components/AppContext";
import { useMessages } from "../hooks/useApi";

import ThreadSelector from "../components/ThreadSelector";

export default function Home() {
  const { user, activeThreadId } = useAppContext();
  const { messages, mutate: mutateMessages, isLoading: messagesLoading } = useMessages(activeThreadId);

  const backendUrl = useMemo(() => process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000", []);
  
  const {
    startAudioStream,
    endAudioStream,
    isConversationActive,
    isListening,
    isSpeaking
  } = useWebSocket(backendUrl.replace(/^http/, "ws") + "/ws");

  const [isThinking, setIsThinking] = useState(false);

  // Derive thinking state: User stopped speaking but assistant hasn't started yet
  useEffect(() => {
    if (!isListening && isConversationActive && !isSpeaking) {
      // Small delay to avoid flickering between states
      const timer = setTimeout(() => setIsThinking(true), 500);
      return () => clearTimeout(timer);
    } else {
      setIsThinking(false);
    }
  }, [isListening, isSpeaking, isConversationActive]);

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
            isListening={isListening} 
            isSpeaking={isSpeaking} 
            isThinking={isThinking} 
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
            background: 'rgba(255,255,255,0.01)'
          }}>
            <span style={{ fontWeight: '800', fontSize: '18px', letterSpacing: '-0.5px' }}>Conversation</span>
            <button 
              onClick={() => mutateMessages()}
              disabled={messagesLoading}
              style={{ 
                color: 'white', 
                background: 'rgba(255,255,255,0.03)', 
                padding: '8px', 
                borderRadius: '8px',
                display: 'flex',
                cursor: 'pointer',
                opacity: messagesLoading ? 0.5 : 1
              }}
            >
              <FaSync size={12} className={messagesLoading ? 'spin' : ''} />
            </button>
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
