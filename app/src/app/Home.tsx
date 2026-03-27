"use client";

import { useCallback, useEffect, useMemo, useRef } from "react";
import { useWebSocket } from "../components/socket/WebSocket";

export default function Home() {
  const backendUrl = useMemo(() => process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000", []);
  const {
    startAudioStreaming,
    stopAudioStreaming,
    attachBackendListener,
    closeSocket
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
    <div className="p-4 border rounded-lg flex flex-col items-center gap-4">
      <h2 className="text-xl font-bold">Voice Assistant Recorder</h2>
      <button onClick={startAudioStreaming}>Start Conversation</button>
      <button onClick={stopAudioStreaming}>Stop Conversation</button>
    </div>
  );
}
