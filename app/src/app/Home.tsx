"use client";

import { useCallback, useEffect, useMemo, useRef } from "react";
import { useWebSocket } from "../components/socket/WebSocket";
import styles from "./page.module.css";

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
    <div className={styles.voicePanel}>
      <div className={styles.orbStage} aria-label="Assistant activity indicator" role="status">
        <div className={`${styles.orbShell} ${isListening ? styles.listening : ""} ${isSpeaking ? styles.speaking : ""}`}>
          <div className={styles.orbGlow} />
          <div className={styles.orbCore} id="assistant-orb" />
          <div className={styles.rippleSet} aria-hidden="true">
            <span className={styles.ripple} />
            <span className={styles.ripple} />
            <span className={styles.ripple} />
          </div>
        </div>
      </div>

      <div className={styles.voiceTextBlock}>
        <p className={styles.kicker}>Voice Assistant Recorder</p>
        <h2 className={styles.voiceTitle}>Memory Aware AI</h2>
        <p className={styles.voiceSubtitle}>
          {isSpeaking ? "Speaking" : isListening ? "Listening" : "Idle"}
        </p>
      </div>

      <div className={styles.voiceActions}>
        <button className={styles.primaryButton} onClick={startAudioStreaming}>Start Conversation</button>
        <button className={styles.secondaryButton} onClick={stopAudioStreaming}>Stop Conversation</button>
      </div>
    </div>
  );
}
