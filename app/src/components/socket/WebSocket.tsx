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
    baseUrl?: string,
    binaryType: "arraybuffer" | "blob" = "arraybuffer"
) => {
    if (!baseUrl) {
        throw new Error("WebSocket base URL is required");
    }
    const eventSocketRef = useRef<WebSocket | null>(null);
    const audioSocketRef = useRef<WebSocket | null>(null);
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

        const handleEventMessage = async (event: MessageEvent) => {
            if (typeof event.data !== "string") return;
            console.log("Received event message:", event.data);
            
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
                // Report to backend
                if (eventSocketRef.current?.readyState === WebSocket.OPEN) {
                    eventSocketRef.current.send(JSON.stringify({ type: "AIStartSpeakingEvent" }));
                }
                const isInt16 = (data.format || "f32le").toLowerCase().includes("16");
                configAudioSpec({
                    codec: isInt16 ? "Int16" : "Float32",
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
                    setIsSpeaking(false);
                    setIsListening(isStreamingRef.current);
                    if (eventSocketRef.current?.readyState === WebSocket.OPEN) {
                        eventSocketRef.current.send(JSON.stringify({
                            type: "playback_done",
                            streamId: doneStreamId,
                        }));
                        // Report AI finished speaking
                        eventSocketRef.current.send(JSON.stringify({ type: "AIStopSpeakingEvent" }));
                    }
                }, ackAfterMs);
            }

        };

        const handleAudioMessage = async (event: MessageEvent) => {
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
            }
        };

        const eventSocket = eventSocketRef.current;
        const audioSocket = audioSocketRef.current;

        if (eventSocket) {
            eventSocket.addEventListener("message", handleEventMessage);
        }
        if (audioSocket) {
            audioSocket.addEventListener("message", handleAudioMessage);
        }

        return () => {
            eventSocket?.removeEventListener("message", handleEventMessage);
            audioSocket?.removeEventListener("message", handleAudioMessage);
        };
    }, [configAudioSpec, playAudio]);

    const closeSocket = useCallback(() => {
        if (playbackDrainTimerRef.current) {
            clearTimeout(playbackDrainTimerRef.current);
            playbackDrainTimerRef.current = null;
        }
        closeAudioPlayer();
        isStreamingRef.current = false;
        setIsListening(false);
        setIsSpeaking(false);

        eventSocketRef.current?.close();
        eventSocketRef.current = null;
        audioSocketRef.current?.close();
        audioSocketRef.current = null;
    }, [closeAudioPlayer]);

    const startAudioStreaming = useCallback(async (userId?: string, sessionId?: string) => {
        try {
            const eventUrl = `${baseUrl}/event?user_id=${userId}`;
            const audioUrl = `${baseUrl}/audio?user_id=${userId}`;

            if (!eventSocketRef.current || eventSocketRef.current.readyState !== WebSocket.OPEN) {
                eventSocketRef.current = await configureWebSocket(null, eventUrl, "blob");
            }
            
            const audioWs = await configureWebSocket(audioSocketRef.current, audioUrl, binaryType);
            audioSocketRef.current = audioWs;

            const chunkHandler = (chunk: ArrayBuffer) => {
                if (audioWs.readyState === WebSocket.OPEN) {
                    audioWs.send(chunk);
                }
            };

            const interruptionHandler = (res: MicStreamRes) => {
                if (eventSocketRef.current?.readyState === WebSocket.OPEN) {
                    const eventType = res.event === "speech-start" ? "UserSpeechStartEvent" : "UserSpeechEndEvent";
                    eventSocketRef.current.send(JSON.stringify({ type: eventType }));
                }
            };

            audioWs.send(JSON.stringify({ 
                type: "start_conversation", 
                mime: "audio/wav",
                user_id: userId,
                session_id: sessionId
            }));
            
            isStreamingRef.current = true;
            setIsListening(true);
            setIsSpeaking(false);

            startRecording(chunkHandler, (err) => console.error(err), interruptionHandler);
        } catch (error) {
            console.error("Failed to start streaming:", error);
            await stopRecording();
        }
    }, [baseUrl, binaryType, startRecording, stopRecording]);

    const stopAudioStreaming = useCallback(async () => {
        const audioWs = audioSocketRef.current;
        await closeAudioPlayer();
        isStreamingRef.current = false;
        setIsListening(false);
        setIsSpeaking(false);
        if (audioWs && audioWs.readyState === WebSocket.OPEN) {
            audioWs.send(JSON.stringify({ type: "end_conversation" }));
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