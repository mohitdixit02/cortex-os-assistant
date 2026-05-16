import React from "react";

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
export const BINARY_TYPE = "arraybuffer";