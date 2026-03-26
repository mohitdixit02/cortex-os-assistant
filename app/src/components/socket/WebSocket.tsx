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

const configureWebSocket = async (socket: WebSocket) => {
    if(!socket) {
        socket = initializeWebSocket(socket.url, socket.binaryType);
        if(!socket) {
            throw new Error("Failed to initialize WebSocket");
        }
    }
    // socket object is present, check for open state
    try{
        await ensureSocketOpen(socket);
    }
    catch(error) {
        // fallback to reconnect WebSocket
        socket = initializeWebSocket(socket.url, socket.binaryType);
        await ensureSocketOpen(socket); // if this fails, it will throw and be caught by caller
        console.log("WebSocket connected successfully");
    }
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
    const socket = initializeWebSocket(socketUrl, binaryType);
    const socketRef = useRef(socket);

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
            if (socketRef.current?.readyState === WebSocket.OPEN) {
                socketRef.current.send(JSON.stringify({ type: socketEndResponse }));
            }
            socketRef.current.close();
        };
    }

    const startAudioStreaming = async () => {
        try {
            await configureWebSocket(socketRef.current);
            const ws = socketRef.current;
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
            ws.send(JSON.stringify({ type: "start_conversation", mime: "audio/wav" }));

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
        await stopRecording();
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