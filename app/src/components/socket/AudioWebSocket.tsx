import { useEffect, useRef, useState, useCallback } from "react";
import { useAudioManager } from "../audio/AudioManager";
import { MicStreamRes } from "../audio/AudioInterface";
import { handleAudioMessage } from "./handlers";
import { configureWebSocket } from "./utility";
import {
    AudioStreamSession,
} from "./types";
import Emitter from "./emitter";

export const useAudioWebSocket = (
    streamSession: AudioStreamSession
) => {
    const BASE_URL = streamSession.baseUrl || "";
    const binaryType = streamSession.binaryType || "arraybuffer";
    if (!BASE_URL) {
        throw new Error("WebSocket base URL is required");
    }
    const audioSocketRef = useRef<WebSocket | null>(null);
    const AUDIO_SOCKET_ENDPOINT = `${BASE_URL}/audio?user_id=${streamSession.userId}`;
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

    const attachAudioListener = useCallback(async (onFinishSpeaking?: () => void) => {
        if (playbackDrainTimerRef.current) {
            clearTimeout(playbackDrainTimerRef.current);
            playbackDrainTimerRef.current = null;
        }

        const audioSocket = audioSocketRef.current;

        const audioEventHandler = (event: MessageEvent) => {
            handleAudioMessage(
                audioSocketRef,
                event,
                streamPlaybackRef,
                playbackDrainTimerRef,
                playAudio,
                configAudioSpec,
                setIsSpeaking,
                setIsListening,
                onFinishSpeaking
            );
        };

        if (audioSocket) {
            audioSocket.addEventListener("message", audioEventHandler);
        }

        return () => {
            audioSocket?.removeEventListener("message", audioEventHandler);
        };
    }, [audioSocketRef, configAudioSpec, playAudio]);

    const closeAudioSocket = useCallback(() => {
        if (playbackDrainTimerRef.current) {
            clearTimeout(playbackDrainTimerRef.current);
            playbackDrainTimerRef.current = null;
        }
        closeAudioPlayer();
        // setIsListening(false);
        // setIsSpeaking(false);

        audioSocketRef.current?.close();
        audioSocketRef.current = null;
    }, [closeAudioPlayer]);

    const startAudioStreaming = useCallback(async (userId?: string, sessionId?: string) => {
        try {
            const audioWs = await configureWebSocket(audioSocketRef.current, AUDIO_SOCKET_ENDPOINT, binaryType);
            audioSocketRef.current = audioWs;

            const chunkHandler = (chunk: ArrayBuffer) => {
                if (audioWs.readyState === WebSocket.OPEN) {
                    audioWs.send(chunk);
                }
            };

            const interruptionHandler = (res: MicStreamRes) => {
                if (res.event === "speech-start") {
                    setIsListening(true);
                    setIsSpeaking(false);
                } else if (res.event === "speech-end") {
                    setIsListening(false);
                }
                const eventType: typeof Emitter.EventType[keyof typeof Emitter.EventType] = res.event === "speech-start"
                    ? Emitter.EventType.USER_START_SPEAKING
                    : Emitter.EventType.USER_STOP_SPEAKING;
                Emitter.emitSocketEvent(audioSocketRef.current, eventType);
            };
            Emitter.emitAudioSocket(
                audioSocketRef.current,
                Emitter.EventType.CONVERSATION_START,
                {
                    mime: "audio/wav",
                    user_id: userId,
                    session_id: sessionId
                }
            );

            // setIsListening(true);
            // setIsSpeaking(false);

            startRecording(chunkHandler, (err) => console.error(err), interruptionHandler);
        } catch (error) {
            console.error("Failed to start streaming:", error);
            await stopRecording();
        }
    }, [binaryType, startRecording, stopRecording, audioSocketRef, AUDIO_SOCKET_ENDPOINT]);

    const stopAudioStreaming = useCallback(async () => {
        await closeAudioPlayer();
        // setIsListening(false);
        // setIsSpeaking(false);
        Emitter.emitAudioSocket(audioSocketRef.current, Emitter.EventType.CONVERSATION_END);
    }, [closeAudioPlayer]);

    return {
        startAudioStreaming,
        stopAudioStreaming,
        attachAudioListener,
        closeAudioSocket,
        isListening,
        isSpeaking
    }
};