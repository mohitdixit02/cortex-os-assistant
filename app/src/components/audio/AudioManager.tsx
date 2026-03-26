import { useCallback, useEffect, useMemo, useRef } from "react";
import { usePCMPlayer } from "./PCMPlayer";
import {
    PcmCodec,
    RecorderStartResult,
    AssistantAPI,
    MicStreamRes,
    AudioConfig
} from "./AudioInterface";

const getAssistantApi = (): AssistantAPI | null => {
    const value = (window as Window & { assistantAPI?: AssistantAPI }).assistantAPI;
    return value || null;
};

const normalizeArrayBuffer = (chunk: unknown): ArrayBuffer | null => {
    if (chunk instanceof ArrayBuffer) {
        return chunk;
    }
    if (ArrayBuffer.isView(chunk)) {
        return new Uint8Array(chunk.buffer, chunk.byteOffset, chunk.byteLength).slice().buffer;
    }
    if (typeof chunk === "object" && chunk !== null) {
        const maybeBuffer = chunk as { type?: string; data?: number[] };
        if (maybeBuffer.type === "Buffer" && Array.isArray(maybeBuffer.data)) {
            return Uint8Array.from(maybeBuffer.data).buffer;
        }
    }
    return null;
};

export const useAudioManager = () => {
    // Is audio currently playing
    const playingRef = useRef(false);

    // PCM Player
    const { reInitializePlayer, feedPcm } = usePCMPlayer();

    // References for mic event listeners so we can detach them later
    const detachMicChunkRef = useRef<(() => void) | null>(null);
    const detachMicErrorRef = useRef<(() => void) | null>(null);

    // State to track if user is currently speaking (based on VAD)
    const isUserSpeaking = useRef(false);

    // Detach mic event listeners
    const detachMicListeners = () => {
        console.log("Detaching mic listeners");
        if (detachMicChunkRef.current) {
            detachMicChunkRef.current();
            detachMicChunkRef.current = null;
        }
        if (detachMicErrorRef.current) {
            detachMicErrorRef.current();
            detachMicErrorRef.current = null;
        }
    };

    const configAudioSpec = async (
        config: AudioConfig
    ) => { await reInitializePlayer(config); }

    const startRecording = async (
        chunkHandler: (chunk: ArrayBuffer) => void,
        errHandler: (error: string) => void,
        interuptionHandler: (data: MicStreamRes) => void
    ) => {
        const api = getAssistantApi();
        if (!api) {
            console.error("assistantAPI bridge is not available in renderer");
            throw new Error("Assistant API not available");
        }

        try {
            detachMicListeners(); // clean up any existing listeners

            // Listener to mic chunks from main process
            detachMicChunkRef.current = api.onMicChunk(async (res: MicStreamRes) => {
                if (res.event === "speech-start") {
                    isUserSpeaking.current = true;
                    console.log("VAD detected speech start");
                    await pauseAudio(); // pause any currently playing audio when user starts speaking
                    interuptionHandler({ event: "speech-start" });
                    return;
                }
                if (res.event === "speech-end") {
                    isUserSpeaking.current = false;
                    console.log("VAD detected speech end");
                    interuptionHandler({ event: "speech-end" });
                    return;
                }
                if (res.event === "speech-data" && res.chunk) {
                    const normalized = normalizeArrayBuffer(res.chunk);
                    if (!normalized) {
                        throw new Error("Received mic chunk in unknown format");
                    }

                    console.log("[Audio Manager] Received mic chunk:", normalized.byteLength, "bytes");
                    chunkHandler(normalized);
                }
            });

            // Listener to mic recording errors from main process
            detachMicErrorRef.current = api.onMicError((error) => {
                console.error("Mic recorder error:", error);
                errHandler(error);
            });

            // Invoke main process to start mic recording
            const result = await api.startMicRecording();

            if (!result.ok) {
                throw new Error(result.error || "Failed to start microphone recording");
            }
        }
        catch (error) {
            console.error("Failed to perform mic recording:", error);
            detachMicListeners();
            stopRecording();
            throw error;
        }
    }

    const stopRecording = async () => {
        const api = getAssistantApi();
        detachMicListeners();
        if (api) {
            try {
                await api.stopMicRecording();
                console.log("Main process mic recording stopped successfully");
            } catch (error) {
                console.error("Failed to stop mic recorder:", error);
            }
        }
        else {
            console.error("assistantAPI bridge is not available in renderer");
        }
    };

    const playAudio = async (audio: ArrayBuffer | Blob) => {
        if (!audio || (!(audio instanceof Blob) && !(audio instanceof ArrayBuffer))) return; const chunk = audio instanceof Blob ? await audio.arrayBuffer() : audio;
        if (!isUserSpeaking.current) {
            playingRef.current = true;
            await feedPcm(chunk); // PCM Player will handle the chunk and play it
        }
    }

    const pauseAudio = async () => {
        playingRef.current = false;
        await reInitializePlayer(); // reset PCM Player to clear any buffered audio
    }

    const closeAudioPlayer = async () => {
        playingRef.current = false;
        await stopRecording(); // ensure mic recording is stopped
        await reInitializePlayer(); // reset PCM Player
    }

    return {
        startRecording,
        stopRecording,
        playAudio,
        pauseAudio,
        configAudioSpec,
        closeAudioPlayer
    }
}