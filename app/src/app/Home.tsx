"use client";

import { useEffect, useMemo, useRef } from "react";

export default function Home() {
    const backendUrl = useMemo(
        () => process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000",
        []
    );

    const socketRef = useRef<WebSocket | null>(null);
    const audioCtxRef = useRef<AudioContext | null>(null);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const micStreamRef = useRef<MediaStream | null>(null);

    const sampleRateRef = useRef(24000);
    const channelsRef = useRef(1);
    const nextPlayTimeRef = useRef(0);

    const ensureSocketOpen = async (socket: WebSocket) => {
        if (socket.readyState === WebSocket.OPEN) {
            return;
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

    const playPcmFrame = async (buffer: ArrayBuffer) => {
        const ctx = audioCtxRef.current;
        if (!ctx) {
            return;
        }
        if (ctx.state === "suspended") {
            await ctx.resume();
        }

        const channels = channelsRef.current;
        const sampleRate = sampleRateRef.current;
        const pcm = new Float32Array(buffer);
        const frameCount = Math.floor(pcm.length / channels);
        if (frameCount <= 0) {
            return;
        }

        const audioBuffer = ctx.createBuffer(channels, frameCount, sampleRate);
        for (let ch = 0; ch < channels; ch += 1) {
            const channelData = audioBuffer.getChannelData(ch);
            for (let i = 0; i < frameCount; i += 1) {
                channelData[i] = pcm[i * channels + ch] ?? 0;
            }
        }

        const source = ctx.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(ctx.destination);

        const startAt = Math.max(ctx.currentTime, nextPlayTimeRef.current);
        source.start(startAt);
        nextPlayTimeRef.current = startAt + audioBuffer.duration;
    };

    useEffect(() => {
        const socket = new WebSocket(backendUrl.replace(/^http/, "ws") + "/ws");
        socketRef.current = socket;
        audioCtxRef.current = new AudioContext();

        socket.onmessage = async (event) => {
            if (typeof event.data === "string") {
                const data = JSON.parse(event.data);
                if (data.type === "audio_meta") {
                    sampleRateRef.current = Number(data.sampleRate) || 24000;
                    channelsRef.current = Number(data.channels) || 1;
                    nextPlayTimeRef.current = audioCtxRef.current?.currentTime ?? 0;
                }
                if (data.type === "done") {
                    console.log("TTS stream complete");
                }
                return;
            }

            if (event.data instanceof Blob) {
                const arr = await event.data.arrayBuffer();
                await playPcmFrame(arr);
                return;
            }

            if (event.data instanceof ArrayBuffer) {
                await playPcmFrame(event.data);
            }
        };

        socket.onerror = (e) => {
            console.error("WebSocket error:", e);
        };

        return () => {
            const recorder = mediaRecorderRef.current;
            if (recorder && recorder.state !== "inactive") {
                recorder.stop();
            }
            micStreamRef.current?.getTracks().forEach((track) => track.stop());
            socket.close();
            audioCtxRef.current?.close();
        };
    }, [backendUrl]);

    const startStreaming = async () => {
        try {
            const ws = socketRef.current;
            if (!ws) {
                console.error("WebSocket not initialized");
                return;
            }

            await ensureSocketOpen(ws);

            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            micStreamRef.current = stream;

            const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
            mediaRecorderRef.current = recorder;

            ws.send(JSON.stringify({ type: "start", mime: recorder.mimeType }));

            recorder.ondataavailable = (e) => {
                if (e.data.size > 0 && ws.readyState === WebSocket.OPEN) {
                    ws.send(e.data);
                }
            };

            recorder.onstop = () => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ type: "stop" }));
                }
                stream.getTracks().forEach((track) => track.stop());
                micStreamRef.current = null;
            };

            recorder.start(100);
            console.log("MediaRecorder state:", recorder.state);
        } catch (err) {
            console.error("Failed to start streaming:", err);
        }
    };

    const stopRecording = () => {
        const recorder = mediaRecorderRef.current;
        if (recorder && recorder.state !== "inactive") {
            recorder.stop();
        }
    };

    return (
        <div className="p-4 border rounded-lg flex flex-col items-center gap-4">
            <h2 className="text-xl font-bold">Voice Assistant Recorder</h2>
            <button onClick={startStreaming}>Start Conversation</button>
            <button onClick={stopRecording}>Stop Conversation</button>
        </div>
    );
}
