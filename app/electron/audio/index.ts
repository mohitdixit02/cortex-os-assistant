const path = require("path");
const AudioRecorder = require("node-audiorecorder");
const soxPath = require("sox-bin");
const { VAD } = require("./vad");

const soxDir = path.dirname(soxPath);
process.env.PATH = `${soxDir};${process.env.PATH}`;
process.env.AUDIODRIVER = 'waveaudio';

interface MicStreamOptions {
    recorderOptions: Record<string, any>;
    event: Electron.IpcMainInvokeEvent;
    streamRendererEndPoint: string;
    errorRendererEndPoint: string;
}

class AudioManager {
    // Types
    micRecorder: typeof AudioRecorder | null;
    micStream: NodeJS.ReadableStream | null;
    micOwnerWebContents: Electron.WebContents | null;
    vad: any;

    constructor() {
        this.micRecorder = null;
        this.micStream = null;
        this.micOwnerWebContents = null;
        this.vad = new VAD();
    }

    stopMicRecorder() {
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

        // Start VAD processing loop
        await this.vad.initialize(
            () => {
                console.log("[AudioManager] VAD detected speech start");
            },
            () => {
                console.log("[AudioManager] VAD detected speech end");
            }
        );
        console.log("[AudioManager] Mic stream started; VAD ready");

        this.micStream.on("data", async (chunk: Buffer) => {
            if (!this.micOwnerWebContents || this.micOwnerWebContents.isDestroyed()) {
                return;
            }
            try {
                await this.vad.processAudioChunk(chunk);
            } catch (error) {
                console.error("[AudioManager] VAD processing error:", error);
                if (this.micOwnerWebContents && !this.micOwnerWebContents.isDestroyed()) {
                    this.micOwnerWebContents.send(errorRendererEndPoint, String(error));
                }
            }

            // this.micOwnerWebContents.send(streamRendererEndPoint, chunk);
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

module.exports = {
    AudioManager,
};

export {};