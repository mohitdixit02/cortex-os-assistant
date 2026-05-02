import { useEffect, useRef, useState, useCallback } from "react";
import { useAudioManager } from "../audio/AudioManager";
import { MicStreamRes } from "../audio/AudioInterface";

const ensureSocketOpen = async (socket: WebSocket) => {
    if(!socket) {
        throw new Error("WebSocket is not initialized");
    }
    if (socket.readyState === WebSocket.OPEN) {
        return {
            ok: true,
            message: "WebSocket is already open",
        };
    }

    if (socket.readyState !== WebSocket.CONNECTING) {
        throw new Error("WebSocket is not connected");
    }

    await new Promise<void>((resolve, reject) => {
        const onOpen = () => {
            socket.removeEventListener("error", onError);
            resolve();
        };
        const onError = () => {
            socket.removeEventListener("open", onOpen);
            reject(new Error("Failed to open WebSocket"));
        };

        socket.addEventListener("open", onOpen, { once: true });
        socket.addEventListener("error", onError, { once: true });
    });
};

const initializeWebSocket = (socketUrl: string, binaryType: "arraybuffer" | "blob") => {
    const socket = new WebSocket(socketUrl);
    socket.binaryType = binaryType;
    return socket;
}

const configureWebSocket = async (
    socket: WebSocket | null,
    socketUrl: string,
    binaryType: "arraybuffer" | "blob"
) => {
    let activeSocket = socket;
    if (!activeSocket || activeSocket.readyState === WebSocket.CLOSING || activeSocket.readyState === WebSocket.CLOSED) {
        activeSocket = initializeWebSocket(socketUrl, binaryType);
    }
    await ensureSocketOpen(activeSocket); // throws error if socket fails to open
    console.log("WebSocket connected successfully");
    return activeSocket;
}

type BackendListenerProps = {
    metaDataKey?: string;
    audioEndKey?: string;
}

export const useWebSocket = (
    socketUrl?: string,
    binaryType: "arraybuffer" | "blob" = "arraybuffer"
) => {
    if (!socketUrl) {
        throw new Error("WebSocket URL is required");
    }
    // Fix: initialize as null to avoid creating orphaned sockets on every render
    const socketRef = useRef<WebSocket | null>(null);
    const isStreamingRef = useRef(false);
    const [isListening, setIsListening] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const playbackDrainTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const streamPlaybackRef = useRef({
        streamId: null as number | null,
        sampleRate: 24000,
        channels: 1,
        bytesPerSample: 4,
        firstChunkAtMs: 0,
        totalSamples: 0,
    });

    const {
        startRecording,
        stopRecording,
        playAudio,
        configAudioSpec,
        closeAudioPlayer
    } = useAudioManager();

    const attachBackendListener = useCallback(async ({
        metaDataKey = "audio_meta",
        audioEndKey = "done"
    }: BackendListenerProps) => {
        if (playbackDrainTimerRef.current) {
            clearTimeout(playbackDrainTimerRef.current);
            playbackDrainTimerRef.current = null;
        }

        // Lazy initialization if needed
        if (!socketRef.current || socketRef.current.readyState === WebSocket.CLOSED) {
            socketRef.current = initializeWebSocket(socketUrl, binaryType);
        }

        const socket = socketRef.current;

        const handleMessage = async (event: MessageEvent) => {
            console.log("Received message from WebSocket:", event.data);
            if (!isStreamingRef.current) {
                console.warn("Received message while not streaming, ignoring:", event.data);
                return;
            }
            if (typeof event.data === "string") {
                const data = JSON.parse(event.data) as {
                    type?: string;
                    streamId?: number;
                    sampleRate?: number;
                    channels?: number;
                    format?: string;
                };
                if (data.type === metaDataKey) {
                    setIsSpeaking(true);
                    setIsListening(false);
                    const isInt16 = (data.format || "f32le").toLowerCase().includes("16");
                    configAudioSpec({
                        codec: isInt16
                            ? "Int16"
                            : "Float32",
                        sampleRate: Number(data.sampleRate) || 24000,
                        channels: Number(data.channels) || 1,
                    });

                    if (playbackDrainTimerRef.current) {
                        clearTimeout(playbackDrainTimerRef.current);
                        playbackDrainTimerRef.current = null;
                    }

                    streamPlaybackRef.current = {
                        streamId: typeof data.streamId === "number" ? data.streamId : null,
                        sampleRate: Number(data.sampleRate) || 24000,
                        channels: Number(data.channels) || 1,
                        bytesPerSample: isInt16 ? 2 : 4,
                        firstChunkAtMs: 0,
                        totalSamples: 0,
                    };
                }
                if (data.type === audioEndKey) {
                    console.log("Received audio end signal from backend");
                    setIsSpeaking(false);
                    setIsListening(isStreamingRef.current);
                    const now = Date.now();
                    const playbackState = streamPlaybackRef.current;
                    const totalDurationMs = playbackState.sampleRate > 0
                        ? (playbackState.totalSamples / playbackState.sampleRate) * 1000
                        : 0;
                    const elapsedMs = playbackState.firstChunkAtMs > 0
                        ? now - playbackState.firstChunkAtMs
                        : 0;
                    const remainingMs = Math.max(0, totalDurationMs - elapsedMs);
                    const drainSafetyMs = 180;
                    const ackAfterMs = Math.max(40, Math.ceil(remainingMs + drainSafetyMs));
                    const doneStreamId = typeof data.streamId === "number"
                        ? data.streamId
                        : playbackState.streamId;

                    if (playbackDrainTimerRef.current) {
                        clearTimeout(playbackDrainTimerRef.current);
                    }

                    playbackDrainTimerRef.current = setTimeout(() => {
                        const ws = socketRef.current;
                        if (ws && ws.readyState === WebSocket.OPEN) {
                            ws.send(JSON.stringify({
                                type: "playback_done",
                                streamId: doneStreamId,
                            }));
                        }
                    }, ackAfterMs);
                }
                return;
            }

            if (event.data instanceof Blob || event.data instanceof ArrayBuffer) {
                const playbackState = streamPlaybackRef.current;
                const chunkByteLength = event.data instanceof Blob ? event.data.size : event.data.byteLength;
                const denominator = playbackState.bytesPerSample * Math.max(playbackState.channels, 1);
                const chunkSamples = denominator > 0 ? chunkByteLength / denominator : 0;
                if (playbackState.firstChunkAtMs === 0) {
                    playbackState.firstChunkAtMs = Date.now();
                }
                playbackState.totalSamples += chunkSamples;

                await playAudio(event.data);
                return;
            }
        };

        const handleError = (e: Event) => {
            console.error("WebSocket error:", e);
        };

        socket.addEventListener("message", handleMessage);
        socket.addEventListener("error", handleError);

        // Cleanup function for listeners
        return () => {
            socket.removeEventListener("message", handleMessage);
            socket.removeEventListener("error", handleError);
        };
    }, [socketUrl, binaryType, configAudioSpec, playAudio]);

    const closeSocket = useCallback((socketEndResponse: string = "close_connection") => {
        if (playbackDrainTimerRef.current) {
            clearTimeout(playbackDrainTimerRef.current);
            playbackDrainTimerRef.current = null;
        }
        closeAudioPlayer();
        isStreamingRef.current = false;
        setIsListening(false);
        setIsSpeaking(false);
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify({ type: socketEndResponse }));
        }
        socketRef.current?.close();
        socketRef.current = null;
    }, [closeAudioPlayer]);

    const startAudioStreaming = useCallback(async (userId?: string, sessionId?: string) => {
        try {
            const ws = await configureWebSocket(socketRef.current, socketUrl, binaryType);
            socketRef.current = ws;
            console.log("WebSocket configuration result:", ws.readyState);
            const chunkHandler = (chunk: ArrayBuffer) => {
                if (ws.readyState === WebSocket.OPEN) {
                    console.log("Sending audio chunk of size:", chunk.byteLength);
                    ws.send(chunk);
                }
            };
            const errHandler = (error: string) => {
                console.error("Mic recorder error:", error);
            }
            const interruptionHandler = (res: MicStreamRes) => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ type: "interruption", event: res.event }));
                }
            }

            // trigger audio start
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                throw new Error("WebSocket is not open for sending audio data");
            }
            ws.send(JSON.stringify({ 
                type: "start_conversation", 
                mime: "audio/wav",
                user_id: userId,
                session_id: sessionId
            }));
            isStreamingRef.current = true;
            setIsListening(true);
            setIsSpeaking(false);

            // Audio manager will handle chunks as per handlers provided
            startRecording(
                chunkHandler,
                errHandler,
                interruptionHandler
            );
        } catch (error) {
            console.error("Failed to start streaming:", error);
            await stopRecording();
        }
    }, [socketUrl, binaryType, startRecording, stopRecording]);

    const stopAudioStreaming = useCallback(async () => {
        const ws = socketRef.current;
        await closeAudioPlayer();
        isStreamingRef.current = false;
        setIsListening(false);
        setIsSpeaking(false);
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "end_conversation" }));
        }
    }, [closeAudioPlayer]);

    return {
        startAudioStreaming,
        stopAudioStreaming,
        attachBackendListener,
        closeSocket,
        isListening,
        isSpeaking
    }
};