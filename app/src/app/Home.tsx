"use client";

import { useCallback, useEffect, useMemo, useRef } from "react";
import { useWebSocket } from "../components/socket/WebSocket";
import { motion, AnimatePresence } from "framer-motion";
import { FaStop, FaPlay } from "react-icons/fa";
import AssistantOrb3D from "../components/AssistantOrb3D";

export default function Home() {
  const backendUrl = useMemo(() => process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000", []);
  const {
    startAudioStreaming,
    stopAudioStreaming,
    attachBackendListener,
    closeSocket,
    isListening,
    isSpeaking
  } = useWebSocket(backendUrl.replace(/^http/, "ws") + "/ws/stream");

  useEffect(() => {
    attachBackendListener({
      metaDataKey: "audio_meta",
      audioEndKey: "done"
    });
    return () => {
      closeSocket();
    };
  }, [backendUrl]);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100%',
      gap: '20px'
    }}>
      <div style={{ textAlign: 'center' }}>
        <h1 style={{ fontSize: '36px', fontWeight: '800', marginBottom: '10px' }}>
          Hello, <span className="gradient-text">{`I'm Cortex`}</span>
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '18px' }}>
          {isSpeaking ? "Speaking..." : isListening ? "I'm listening..." : "How can I help you today?"}
        </p>
      </div>

      <div style={{
        position: 'relative', 
        width: '100%', 
        maxWidth: '500px', 
        height: '400px', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center' 
      }}>
        <AssistantOrb3D isListening={isListening} isSpeaking={isSpeaking} />
      </div>

      <div style={{ display: 'flex', gap: '20px', marginTop: '20px' }}>
        {!isListening ? (
          <button 
            onClick={startAudioStreaming}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '16px 32px',
              borderRadius: '50px',
              background: 'var(--primary-gradient)',
              color: 'white',
              fontSize: '18px',
              fontWeight: '600',
              boxShadow: '0 10px 20px rgba(0,0,0,0.2)',
              transition: 'transform 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
            onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
          >
            <FaPlay /> Start Conversation
          </button>
        ) : (
          <button 
            onClick={stopAudioStreaming}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '16px 32px',
              borderRadius: '50px',
              background: 'rgba(255, 255, 255, 0.1)',
              color: 'white',
              fontSize: '18px',
              fontWeight: '600',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              transition: 'transform 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
            onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
          >
            <FaStop /> Stop Conversation
          </button>
        )}
      </div>
    </div>
  );
}
