type PcmCodec = "Int16" | "Float32";
type RecorderStartResult = { ok: boolean; error?: string };

// Assistant APIs - Exposed by Electron main process
type AssistantAPI = {
    startMicRecording: (options?: Record<string, unknown>) => Promise<RecorderStartResult>;
    stopMicRecording: () => Promise<RecorderStartResult>;
    onMicChunk: (handler: (chunk: unknown) => void) => () => void;
    onMicError: (handler: (error: string) => void) => () => void;
    // Auth
    openExternal: (url: string) => Promise<void>;
    onAuthRedirect: (handler: (url: string) => void) => () => void;
};

type MicStreamRes = {
    event: "speech-start" | "speech-end" | "speech-data";
    chunk?: unknown;
}

export type {
    AssistantAPI,
    PcmCodec,
    RecorderStartResult,
    MicStreamRes
}

export type AudioConfig = {
    codec: PcmCodec;
    sampleRate: number;
    channels: number;
}