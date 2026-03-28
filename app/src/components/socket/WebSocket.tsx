import { useCallback, useEffect, useMemo, useRef } from "react";
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
    const socketRef = useRef<WebSocket | null>(initializeWebSocket(socketUrl, binaryType));
    const isStreamingRef = useRef(false);

    const {
        startRecording,
        stopRecording,
        playAudio,
        configAudioSpec,
        pauseAudio,
        closeAudioPlayer
    } = useAudioManager();

    const attachBackendListener = async ({
        metaDataKey = "audio_meta",
        audioEndKey = "done"
    }: BackendListenerProps) => {
        socketRef.current?.addEventListener("message", async (event) => {
            if (!isStreamingRef.current) {
                console.warn("Received message while not streaming, ignoring:", event.data);
                return;
            }
            if (typeof event.data === "string") {
                const data = JSON.parse(event.data) as {
                    type?: string;
                    sampleRate?: number;
                    channels?: number;
                    format?: string;
                };
                if (data.type === metaDataKey) {
                    configAudioSpec({
                        codec: (data.format || "f32le").toLowerCase().includes("16")
                            ? "Int16"
                            : "Float32",
                        sampleRate: Number(data.sampleRate) || 24000,
                        channels: Number(data.channels) || 1,
                    });
                }
                if (data.type === audioEndKey) {
                    await pauseAudio();
                }
                return;
            }

            if (event.data instanceof Blob || event.data instanceof ArrayBuffer) {
                await playAudio(event.data);
                return;
            }
        });

        socketRef.current?.addEventListener("error", (e) => {
            console.error("WebSocket error:", e);
        });

    };

    const closeSocket = (socketEndResponse: string = "close_connection") => {
        return () => {
            closeAudioPlayer();
            isStreamingRef.current = false;
            if (socketRef.current?.readyState === WebSocket.OPEN) {
                socketRef.current.send(JSON.stringify({ type: socketEndResponse }));
            }
            socketRef.current.close();
        };
    }

    const startAudioStreaming = async () => {
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
            ws.send(JSON.stringify({ type: "start_conversation", mime: "audio/wav" }));
            isStreamingRef.current = true;

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
    };

    const stopAudioStreaming = async () => {
        const ws = socketRef.current;
        await closeAudioPlayer();
        isStreamingRef.current = false;
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "end_conversation" }));
        }
    };

    return {
        startAudioStreaming,
        stopAudioStreaming,
        attachBackendListener,
        closeSocket
    }
};