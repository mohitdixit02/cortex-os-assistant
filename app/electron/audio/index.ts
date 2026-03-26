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

class AudioManager {
    // Types
    micRecorder: typeof AudioRecorder | null;
    micStream: NodeJS.ReadableStream | null;
    micOwnerWebContents: Electron.WebContents | null;
    vad: any;
    isUserSpeaking: boolean;

    constructor() {
        this.micRecorder = null;
        this.micStream = null;
        this.micOwnerWebContents = null;
        this.vad = new VAD();
        this.isUserSpeaking = false;
    }

    async stopMicRecorder() {
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
        const handleSpeechStart = () => {
            this.isUserSpeaking = true;
            console.log("[VAD] Detected speech start");
            if (this.micOwnerWebContents && !this.micOwnerWebContents.isDestroyed()) {
                this.micOwnerWebContents.send(streamRendererEndPoint, { event: "speech-start" });
            }
        }

        const handleSpeechEnd = () => {
            this.isUserSpeaking = false;
            console.log("[VAD] Detected speech end");
            if (this.micOwnerWebContents && !this.micOwnerWebContents.isDestroyed()) {
                this.micOwnerWebContents.send(streamRendererEndPoint, { event: "speech-end" });
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
                // console.log("[AudioManager] Received mic chunk of size:", chunk.length);
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

module.exports = {
    AudioManager,
};

export { };