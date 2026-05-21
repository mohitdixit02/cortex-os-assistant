const path = require("path");
const AudioRecorder = require("node-audiorecorder");
const soxPath = require("sox-bin");
const { VAD } = require("./vad");

const soxDir = path.dirname(soxPath);
process.env.PATH = `${soxDir};${process.env.PATH}`;
process.env.AUDIODRIVER = 'waveaudio';

type MicStreamOptions = {
    recorderOptions: Record<string, any>;
    event: Electron.IpcMainInvokeEvent;
    streamRendererEndPoint: string;
    errorRendererEndPoint: string;
}

const MAX_SPEECH_DURATION_MS = Number(process.env.MAX_SPEECH_DURATION_MS) || 35000;

export class AudioManager {
    // Types
    micRecorder: typeof AudioRecorder | null;
    micStream: NodeJS.ReadableStream | null;
    micOwnerWebContents: Electron.WebContents | null;
    vad: any;
    isUserSpeaking: boolean;
    maxSpeechTimer: NodeJS.Timeout | null;

    constructor() {
        this.micRecorder = null;
        this.micStream = null;
        this.micOwnerWebContents = null;
        this.vad = new VAD();
        this.isUserSpeaking = false;
        this.maxSpeechTimer = null;
    }

    async stopMicRecorder() {
        if (this.maxSpeechTimer) {
            clearTimeout(this.maxSpeechTimer);
            this.maxSpeechTimer = null;
        }

        if (this.micStream) {
            this.micStream.removeAllListeners("data");
            this.micStream.removeAllListeners("error");
            this.micStream = null;
        }

        if (this.micRecorder) {
            try {
                this.micRecorder.stop();
            } catch (error) {
                console.error("Failed to stop microphone recorder:", error);
            }
            this.micRecorder = null;
        }
        this.micOwnerWebContents = null;
        this.vad.pause();
    }

    async startMicStream({
        recorderOptions,
        event,
        streamRendererEndPoint,
        errorRendererEndPoint
    }: MicStreamOptions) {
        this.micRecorder = new AudioRecorder(recorderOptions, console).start();
        this.micStream = this.micRecorder.stream();
        this.micOwnerWebContents = event.sender;

        if (!this.micStream) {
            throw new Error("Microphone stream is not available");
        }

        // Handlers for VAD events
        const handleSpeechEnd = () => {
            if (this.maxSpeechTimer) {
                clearTimeout(this.maxSpeechTimer);
                this.maxSpeechTimer = null;
            }

            if (!this.isUserSpeaking) return;

            this.isUserSpeaking = false;
            console.log("[VAD] Detected speech end");
            if (this.micOwnerWebContents && !this.micOwnerWebContents.isDestroyed()) {
                this.micOwnerWebContents.send(streamRendererEndPoint, { event: "speech-end" });
            }
        }

        const handleSpeechStart = () => {
            if (this.isUserSpeaking) return;

            this.isUserSpeaking = true;
            console.log("[VAD] Detected speech start");
            
            // Start safety timeout
            if (this.maxSpeechTimer) clearTimeout(this.maxSpeechTimer);
            this.maxSpeechTimer = setTimeout(() => {
                console.warn("[AudioManager] Max speech duration reached (35s). Forcing speech end.");
                handleSpeechEnd();
            }, MAX_SPEECH_DURATION_MS);

            if (this.micOwnerWebContents && !this.micOwnerWebContents.isDestroyed()) {
                this.micOwnerWebContents.send(streamRendererEndPoint, { event: "speech-start" });
            }
        }
        
        // Start VAD processing loop
        await this.vad.initialize(
            handleSpeechStart,
            handleSpeechEnd
        );
        if(this.vad.isReady()) {
            console.log("[AudioManager] VAD is ready");
        }
        else{
            console.error("[AudioManager] VAD failed to initialize");
            return;
        }

        this.micStream.on("data", async (chunk: Buffer) => {
            if (!this.micOwnerWebContents || this.micOwnerWebContents.isDestroyed()) {
                return;
            }
            try {
                console.log("[Electron Audio Manager] Received mic chunk of size:", chunk.length);
                await this.vad.processAudioChunk(chunk);
                if (this.isUserSpeaking) { // for now, send all chunks regardless of VAD state
                    if (this.micOwnerWebContents && !this.micOwnerWebContents.isDestroyed()) {
                        this.micOwnerWebContents.send(streamRendererEndPoint, { event: "speech-data", chunk: chunk });
                    }
                }
            } catch (error) {
                console.error("[AudioManager] VAD processing error:", error);
                if (this.micOwnerWebContents && !this.micOwnerWebContents.isDestroyed()) {
                    this.micOwnerWebContents.send(errorRendererEndPoint, String(error));
                }
            }
        });

        this.micStream.on("error", (error: Error) => {
            if (this.micOwnerWebContents && !this.micOwnerWebContents.isDestroyed()) {
                this.micOwnerWebContents.send(errorRendererEndPoint, String(error));
            }
        });

        this.micRecorder.on("error", (error: Error) => {
            if (this.micOwnerWebContents && !this.micOwnerWebContents.isDestroyed()) {
                this.micOwnerWebContents.send(errorRendererEndPoint, String(error));
            }
        });
    }
}