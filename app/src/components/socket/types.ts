import React from "react";

export enum AIState {
    STANDBY = 0,
    LISTENING = 1,
    SPEAKING = 2,
    ANALYZING = 3,
    PROCESSING = 4,
}

export type StreamPlaybackRef = React.RefObject<{
    streamId: string | number | null;
    sampleRate: number;
    channels: number;
    bytesPerSample: number;
    firstChunkAtMs: number;
    totalSamples: number;
}>;

export type AudioMetaData = {
    type?: string;
    stage?: string;
    streamId?: number;
    sampleRate?: number;
    channels?: number;
    format?: string;
}

export type AudioStreamSession = {
    baseUrl?: string,
    binaryType: "arraybuffer" | "blob",
    userId?: string, 
    sessionId?: string
}

export const META_DATA_KEY = "audio_meta";
export const AUDIO_END_KEY = "done";
export const EVENT_TYPE_INTERRUPTION = "interruption";
export const EVENT_STAGE_WAITING = "waiting";
export const EVENT_STAGE_FINISHED = "finished";
export const EVENT_STAGE_PENDING = "pending";
export const EVENT_STAGE_ENDED = "ended";
export const BINARY_TYPE = "arraybuffer";