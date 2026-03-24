const { RealTimeVAD } = require('@ericedouard/vad-node-realtime');

const thresholdConfig = {
    positiveSpeechThreshold: 0.6,
    negativeSpeechThreshold: 0.3,
    sampleRate: 16000,
    frameSize: 1600
};

class VAD {
    constructor() {
        this.vad = null;
        this.ready = RealTimeVAD.new({
            onSpeechStart: () => {
                console.log("Speech started");
            },
            onSpeechEnd: () => {
                console.log("Speech ended");
            },
            ...thresholdConfig
        }).then((vad) => {
            console.log("VAD initialized successfully");
            this.vad = vad;
        }).catch((error) => {
            console.error("Failed to initialize VAD:", error);
            throw error;
        });
    }

    start() {
        this.vad.start();
    }

    pause() {
        this.vad.pause();
    }

    async processAudioChunk(chunk) {
        // console.log("Processing audio chunk of size:", chunk.length);
        await this.vad.processAudio(chunk);
    }

    async destroy() {
        await this.vad.flush();
        this.vad.destroy();
    }
}

module.exports = {
    VAD,
};