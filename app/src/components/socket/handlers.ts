import {
    StreamPlaybackRef,
    AudioMetaData,
    META_DATA_KEY,
    AUDIO_END_KEY,
    AIState,
    EVENT_TYPE_INTERRUPTION,
    EVENT_STAGE_WAITING,
    EVENT_STAGE_FINISHED,
    EVENT_STAGE_PENDING,
} from "./types";

import {
    AudioConfig,
} from "../audio/AudioInterface";

import Emitter from "./emitter";

// Event Handler for Event Web Socket
export const handleEventMessage = async (
    event: MessageEvent,
) => {
    if (typeof event.data !== "string") return;
    console.log("Received event message:", event.data);
};

/**
### Handle incoming messages on the audio WebSocket connection, including both metadata and audio data
#### Arguments
- `audioSocket`: Ref to the audio WebSocket, used for sending audio data back to the backend
- `event`: The incoming WebSocket message event, which may contain either metadata (as JSON string) or audio data (as Blob or ArrayBuffer)
- `streamPlaybackRef`: Ref to the current stream playback state, used for tracking stream ID, sample rate, channels, and playback timing
- `playbackDrainTimerRef`: Ref to the timer used for draining audio playback after receiving an audio end signal
- `playAudio`: Function to play incoming audio data chunks
- `configAudioSpec`: Function to configure the audio playback specifications (sample rate, channels, codec) based on incoming metadata
**/
export const handleAudioMessage = async (
    audioSocket: React.RefObject<WebSocket | null>,
    event: MessageEvent,
    streamPlaybackRef: StreamPlaybackRef,
    playbackDrainTimerRef: React.RefObject<ReturnType<typeof setTimeout> | null>,
    playAudio: (data: Blob | ArrayBuffer) => Promise<void>,
    configAudioSpec: (spec: AudioConfig) => void,
    setAiState: (state: AIState) => void,
    onFinishSpeaking?: () => void,
) => {
    console.log("Received audio socket message:", event.data);

    if (typeof event.data === "string") {
        const data = JSON.parse(event.data) as AudioMetaData;
        
        // Handle Interruption States
        if (data.type === EVENT_TYPE_INTERRUPTION) {
            if (data.stage === EVENT_STAGE_WAITING) {
                setAiState(AIState.ANALYZING);
                return;
            }
            if (data.stage === EVENT_STAGE_FINISHED) {
                setAiState(AIState.PROCESSING);
                return;
            }
        }

        if (data.type === META_DATA_KEY) {
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

        if (data.type === AUDIO_END_KEY) {
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
                if (data.stage === EVENT_STAGE_PENDING) {
                    setAiState(AIState.PROCESSING);
                } else {
                    setAiState(AIState.STANDBY);
                }
                
                Emitter.emitAudioSocket(
                    audioSocket.current, 
                    Emitter.EventType.AI_STOP_SPEAKING, 
                    { streamId: doneStreamId }
                );
                playbackDrainTimerRef.current = null;
                
                // Trigger callback after playback finishes and backend is notified
                if (onFinishSpeaking) {
                    onFinishSpeaking();
                }
            }, ackAfterMs);
        }
    }

    if (event.data instanceof Blob || event.data instanceof ArrayBuffer) {
        const playbackState = streamPlaybackRef.current;
        const chunkByteLength = event.data instanceof Blob ? event.data.size : event.data.byteLength;
        const denominator = playbackState.bytesPerSample * Math.max(playbackState.channels, 1);
        const chunkSamples = denominator > 0 ? chunkByteLength / denominator : 0;
        if (playbackState.firstChunkAtMs === 0) {
            playbackState.firstChunkAtMs = Date.now();
            setAiState(AIState.SPEAKING);
            Emitter.emitAudioSocket(audioSocket.current, Emitter.EventType.AI_START_SPEAKING);
        }
        playbackState.totalSamples += chunkSamples;
        await playAudio(event.data);
    }
};