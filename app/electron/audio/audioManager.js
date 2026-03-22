// let micRecorder = null;
// let micStream = null;
// let micOwnerWebContents = null;

// const vad = new RealTimeVAD({
//   onSpeechStart: () => {
//     console.log("Speech started");
//   },
//   onSpeechEnd: () => {
//     console.log("Speech ended");
//   },
//   positiveSpeechThreshold: 0.6,
//   negativeSpeechThreshold: 0.3,
//   sampleRate: 16000,
//   frameSize: 1600, // 100ms frames at 16kHz
// });

// vad.start();

const path = require("path");
const AudioRecorder = require("node-audiorecorder");
const soxPath = require('sox-bin');
const soxDir = path.dirname(soxPath);
process.env.PATH = `${soxDir};${process.env.PATH}`;
process.env.AUDIODRIVER = 'waveaudio';

export class AudioManager {
    constructor() {
        this.micRecorder = null;
        this.micStream = null;
        this.micOwnerWebContents = null;
        this.vad = null;
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

        this.micStream.on("data", (chunk) => {
            if (!this.micOwnerWebContents || this.micOwnerWebContents.isDestroyed()) {
                return;
            }
            this.micOwnerWebContents.send(streamRendererEndPoint, chunk);
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
