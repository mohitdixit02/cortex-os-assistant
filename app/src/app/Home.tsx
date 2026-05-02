"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useWebSocket } from "../components/socket/WebSocket";
import { motion, AnimatePresence } from "framer-motion";
import { FaStop, FaPlay, FaSync } from "react-icons/fa";
import AssistantOrb3D from "../components/AssistantOrb3D";
import ChatHistory from "../components/ChatHistory";
import { useAppContext } from "../components/AppContext";
import { useMessages } from "../hooks/useApi";

export default function Home() {
  const { user, activeThreadId } = useAppContext();
  const { messages, mutate: mutateMessages, isLoading: messagesLoading } = useMessages(activeThreadId);

  const backendUrl = useMemo(() => process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000", []);
  
  const {
    startAudioStreaming,
    stopAudioStreaming,
    attachBackendListener,
    closeSocket,
    isListening,
    isSpeaking
  } = useWebSocket(backendUrl.replace(/^http/, "ws") + "/ws/stream");

  // Refresh messages when speech ends
  const wasSpeaking = useRef(false);
  useEffect(() => {
    if (wasSpeaking.current && !isSpeaking) {
      setTimeout(() => mutateMessages(), 500);
    }
    wasSpeaking.current = isSpeaking;
  }, [isSpeaking, mutateMessages]);

  useEffect(() => {
    let detachFn: (() => void) | undefined;
    const setup = async () => {
      const detach = await attachBackendListener({
        metaDataKey: "audio_meta",
        audioEndKey: "done"
      });
      detachFn = detach;
    };
    setup();
    return () => {
      if (detachFn) detachFn();
      closeSocket();
    };
  }, [attachBackendListener, closeSocket]);

  return (
    <div style={{
      width: '100%',
      height: '100%',
      display: 'flex',
      overflow: 'hidden',
      background: 'var(--background)'
    }}>
      {/* Left Area: Assistant Orb - Always Centered in its space */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px',
        position: 'relative'
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
            key={isSpeaking ? "sp" : isListening ? "li" : "id"}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{ color: 'var(--text-muted)', fontSize: '18px', marginTop: '10px' }}
          >
            {isSpeaking ? "Speaking..." : isListening ? "Listening..." : "How can I help you today?"}
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
          <AssistantOrb3D isListening={isListening} isSpeaking={isSpeaking} />
        </div>

        <div style={{ marginTop: '40px' }}>
          {!isListening ? (
            <motion.button 
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => startAudioStreaming(user?.id, activeThreadId)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '16px 36px',
                borderRadius: '50px',
                background: 'var(--primary-gradient)',
                color: 'white',
                fontSize: '17px',
                fontWeight: '600',
                boxShadow: '0 10px 25px rgba(0,0,0,0.3)',
                cursor: 'pointer'
              }}
            >
              <FaPlay size={14} /> Start Conversation
            </motion.button>
          ) : (
            <motion.button 
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={stopAudioStreaming}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '16px 36px',
                borderRadius: '50px',
                background: 'rgba(255, 255, 255, 0.1)',
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

      {/* Right Area: Persistent History Window */}
      <div style={{
        width: '400px',
        background: 'rgba(255, 255, 255, 0.02)',
        borderLeft: '1px solid rgba(255, 255, 255, 0.05)',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        boxShadow: '-4px 0 20px rgba(0,0,0,0.2)'
      }}>
        <div style={{
          padding: '25px 20px',
          borderBottom: '1px solid rgba(255,255,255,0.05)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <span style={{ fontWeight: '800', fontSize: '20px', letterSpacing: '-0.5px' }}>Conversation</span>
          <button 
            onClick={() => mutateMessages()}
            disabled={messagesLoading}
            style={{ 
              color: 'white', 
              background: 'rgba(255,255,255,0.05)', 
              padding: '10px', 
              borderRadius: '10px',
              display: 'flex',
              cursor: 'pointer',
              opacity: messagesLoading ? 0.5 : 1,
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => !messagesLoading && (e.currentTarget.style.background = 'rgba(255,255,255,0.08)')}
            onMouseLeave={(e) => !messagesLoading && (e.currentTarget.style.background = 'rgba(255,255,255,0.05)')}
          >
            <FaSync size={14} className={messagesLoading ? 'spin' : ''} />
          </button>
        </div>

        <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <ChatHistory messages={messages} />
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
