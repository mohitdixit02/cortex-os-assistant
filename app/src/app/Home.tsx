"use client";

import { useCallback, useEffect, useMemo, useRef } from "react";
import PCMPlayer from "pcm-player";
import { useWebSocket } from "../components/socket/WebSocket";

type RecorderStartResult = { ok: boolean; error?: string };
type PcmCodec = "Int16" | "Float32";

type AssistantAPI = {
  startMicRecording: (options?: Record<string, unknown>) => Promise<RecorderStartResult>;
  stopMicRecording: () => Promise<RecorderStartResult>;
  onMicChunk: (handler: (chunk: unknown) => void) => () => void;
  onMicError: (handler: (error: string) => void) => () => void;
};

export default function Home() {
  const backendUrl = useMemo(() => process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000", []);
  const {
    startAudioStreaming,
    stopAudioStreaming,
    attachBackendListener,
    closeSocket
  } = useWebSocket(backendUrl.replace(/^http/, "ws") + "/ws");

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
