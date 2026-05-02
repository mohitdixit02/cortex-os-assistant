"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useWebSocket } from "../components/socket/WebSocket";
import { FaStop, FaPlay, FaPaperPlane } from "react-icons/fa";
import AssistantOrb3D from "../components/AssistantOrb3D";
import ChatHistory from "../components/ChatHistory";
import { useAppContext } from "../components/AppContext";
import { useMessages } from "../hooks/useApi";
import { apiClient } from "../utility/apiClient";

export default function Home() {
  const { activeThreadId } = useAppContext();
  const { messages, mutate: mutateMessages } = useMessages(activeThreadId);
  const [textInput, setTextInput] = useState("");
  const [isSendingText, setIsSendingText] = useState(false);

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

      await apiClient<{ response: string }>('/api/query/', {
        method: 'POST',
        body: JSON.stringify({ query, session_id: activeThreadId })
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

        <ChatHistory messages={messages} />

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
