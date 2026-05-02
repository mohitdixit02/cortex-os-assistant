"use client";

import React, { useEffect, useRef, memo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FaUser, FaRobot } from "react-icons/fa";
import { Message } from "../hooks/useApi";

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
            <div style={{
              padding: "12px 16px",
              borderRadius: msg.role === "USER" ? "18px 18px 2px 18px" : "18px 18px 18px 2px",
              background: msg.role === "USER" ? "var(--primary-gradient)" : "rgba(255,255,255,0.05)",
              color: 'white',
              fontSize: '14px',
              lineHeight: '1.5',
              boxShadow: msg.role === "USER" ? '0 4px 15px rgba(199,80,82,0.2)' : 'none'
              }}>              {msg.content}
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
      <div ref={messagesEndRef} />
    </div>
  );
};

export default memo(ChatHistory);
