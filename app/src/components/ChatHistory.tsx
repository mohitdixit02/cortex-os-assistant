"use client";

import React, { useEffect, useRef, memo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FaUser, FaRobot } from "react-icons/fa";
import { Message } from "../hooks/useApi";
import { ToolBadge } from "../utility/toolConfig";

interface ChatHistoryProps {
  messages: Message[] | undefined;
}

const ChatHistory = ({ messages }: ChatHistoryProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div style={{
      flex: 1,
      overflowY: "auto",
      padding: "20px",
      display: "flex",
      flexDirection: "column",
      gap: "15px"
    }}>
      <AnimatePresence initial={false}>
        {messages?.map((msg) => (
          <motion.div
            key={msg.message_id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            style={{
              alignSelf: msg.role === "USER" ? "flex-end" : "flex-start",
              maxWidth: "85%",
              display: "flex",
              flexDirection: "column",
              gap: "5px",
              alignItems: msg.role === "USER" ? "flex-end" : "flex-start"
            }}
          >
            <div style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              fontSize: "12px",
              color: "var(--text-muted)"
            }}>
              {msg.role === "USER" ? <><FaUser size={10} /> You</> : <><FaRobot size={10} /> Cortex</>}
            </div>
            <div className={`msg-bubble ${msg.role === "USER" ? "msg-user-glass" : "msg-ai-glass"}`}>
              {msg.is_refined_query ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <div style={{ opacity: 0.5, fontSize: '11px', fontStyle: 'italic' }}>
                    Original: "{msg.content}"
                  </div>
                  <div style={{ color: 'white' }}>
                    {msg.refined_query}
                  </div>
                </div>
              ) : (
                msg.content
              )}
              {msg.role !== "USER" && <ToolBadge tool_id={msg.tool_id} />}
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
      <div ref={messagesEndRef} />
    </div>
  );
};

export default memo(ChatHistory);
