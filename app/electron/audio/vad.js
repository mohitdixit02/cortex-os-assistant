const { RealTimeVAD } = require('@ericedouard/vad-node-realtime');

const thresholdConfig = {
    positiveSpeechThreshold: 0.6,
    negativeSpeechThreshold: 0.3,
    sampleRate: 16000,
    frameSize: 1600
};

export class VAD{
    constructor() {
        RealTimeVAD.new({
            onSpeechStart: () => {
                console.log("Speech started");
            },
            onSpeechEnd: () => {
                console.log("Speech ended");
            },
            ...thresholdConfig
        }).then((vad) => {
            this.vad = vad;
        }).catch((error) => {
            console.error("Failed to initialize VAD:", error);
        });
    }

    start() {
        this.vad.start();
    }

    pause() {
        this.vad.pause();
    }

    async processAudioChunk(chunk) {
        await this.vad.processAudio(chunk);
    }

    async destroy() {
        await this.vad.flush();
        this.vad.destroy();
    }
}