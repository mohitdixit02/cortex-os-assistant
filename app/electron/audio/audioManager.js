const path = require("path");
import AudioRecorder from "node-audiorecorder";
import soxPath from 'sox-bin';
const soxDir = path.dirname(soxPath);
process.env.PATH = `${soxDir};${process.env.PATH}`;
process.env.AUDIODRIVER = 'waveaudio';
const { VAD } = require("./vad");

export class AudioManager {
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
    }

    startMicStream(
        recorderOptions,
        event,
        streamRendererEndPoint,
        errorRendererEndPoint
    ) {
        this.micRecorder = new AudioRecorder(recorderOptions, console).start();
        this.micStream = this.micRecorder.stream();
        this.micOwnerWebContents = event.sender;

        if (!this.micStream) {
            throw new Error("Microphone stream is not available");
        }

        this.micStream.on("data", async (chunk) => {
            if (!this.micOwnerWebContents || this.micOwnerWebContents.isDestroyed()) {
                return;
            }
            await this.vad.processAudioChunk(chunk);
            // if (this.micOwnerWebContents && !this.micOwnerWebContents.isDestroyed()) {
            //     this.micOwnerWebContents.send(errorRendererEndPoint, String(error));
            // }
            // });
            // this.micOwnerWebContents.send(streamRendererEndPoint, chunk);
        });

        this.micStream.on("error", (error) => {
            if (this.micOwnerWebContents && !this.micOwnerWebContents.isDestroyed()) {
                this.micOwnerWebContents.send(errorRendererEndPoint, String(error));
            }
        });

        this.micRecorder.on("error", (error) => {
            if (this.micOwnerWebContents && !this.micOwnerWebContents.isDestroyed()) {
                this.micOwnerWebContents.send(errorRendererEndPoint, String(error));
            }
        });
    }
}
