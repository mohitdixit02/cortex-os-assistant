"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useWebSocket } from "../components/socket/WebSocket";
import { motion, AnimatePresence } from "framer-motion";
import { FaStop, FaPlay, FaPaperPlane, FaUser, FaRobot } from "react-icons/fa";
import AssistantOrb3D from "../components/AssistantOrb3D";
import { useAppContext } from "../components/AppContext";
import { useMessages } from "../hooks/useApi";
import { apiClient } from "../utility/apiClient";

export default function Home() {
  const { activeThreadId } = useAppContext();
  const { messages, mutate: mutateMessages } = useMessages(activeThreadId);
  const [textInput, setTextInput] = useState("");
  const [isSendingText, setIsSendingText] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

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

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendText = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!textInput.trim() || isSendingText || !activeThreadId) return;

    try {
      setIsSendingText(true);
      const query = textInput;
      setTextInput("");

      // Optimistic update
      const optimisticMessage = {
        message_id: Math.random().toString(),
        session_id: activeThreadId,
        user_id: "me",
        content: query,
        role: "USER",
        created_at: new Date().toISOString()
      };
      mutateMessages([...(messages || []), optimisticMessage], false);

      const response = await apiClient<{ response: string }>('/api/query/', {
        method: 'POST',
        body: JSON.stringify({ query })
      });

      // Refetch messages to get the real ones (including AI response)
      mutateMessages();
    } catch (err) {
      console.error("Failed to send text query", err);
    } finally {
      setIsSendingText(false);
    }
  };

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 350px',
      height: 'calc(100vh - 150px)',
      gap: '40px'
    }}>
      {/* Left Side: Assistant Orb */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '20px',
        position: 'relative'
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

      {/* Right Side: Chat History and Text Input */}
      <div className="glass-card" style={{
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        height: '100%'
      }}>
        <div style={{
          padding: '20px',
          borderBottom: '1px solid rgba(255,255,255,0.05)',
          fontWeight: '600',
          fontSize: '16px'
        }}>
          Conversation
        </div>

        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '15px'
        }}>
          <AnimatePresence initial={false}>
            {messages?.map((msg) => (
              <motion.div
                key={msg.message_id}
                initial={{ opacity: 0, x: msg.role === 'USER' ? 20 : -20 }}
                animate={{ opacity: 1, x: 0 }}
                style={{
                  alignSelf: msg.role === 'USER' ? 'flex-end' : 'flex-start',
                  maxWidth: '85%',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '5px',
                  alignItems: msg.role === 'USER' ? 'flex-end' : 'flex-start'
                }}
              >
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontSize: '12px',
                  color: 'var(--text-muted)'
                }}>
                  {msg.role === 'USER' ? <><FaUser size={10} /> You</> : <><FaRobot size={10} /> Cortex</>}
                </div>
                <div style={{
                  padding: '12px 16px',
                  borderRadius: msg.role === 'USER' ? '18px 18px 2px 18px' : '18px 18px 18px 2px',
                  background: msg.role === 'USER' ? 'var(--primary-gradient)' : 'rgba(255,255,255,0.05)',
                  color: 'white',
                  fontSize: '14px',
                  lineHeight: '1.5',
                  boxShadow: msg.role === 'USER' ? '0 4px 15px rgba(0,0,0,0.2)' : 'none'
                }}>
                  {msg.content}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>

        <form 
          onSubmit={handleSendText}
          style={{
            padding: '20px',
            borderTop: '1px solid rgba(255,255,255,0.05)',
            display: 'flex',
            gap: '10px'
          }}
        >
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder="Type a message..."
            disabled={!activeThreadId}
            style={{
              flex: 1,
              background: 'rgba(255,255,255,0.03)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '10px',
              padding: '12px 16px',
              color: 'white',
              fontSize: '14px',
              outline: 'none'
            }}
          />
          <button
            type="submit"
            disabled={!textInput.trim() || isSendingText || !activeThreadId}
            style={{
              width: '45px',
              height: '45px',
              borderRadius: '10px',
              background: 'var(--primary-gradient)',
              color: 'white',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'transform 0.2s',
              opacity: (!textInput.trim() || isSendingText || !activeThreadId) ? 0.5 : 1
            }}
            onMouseEnter={(e) => !isSendingText && (e.currentTarget.style.transform = 'scale(1.05)')}
            onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1)')}
          >
            <FaPaperPlane size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}
