const { RealTimeVAD } = require("@ericedouard/vad-node-realtime");

const thresholdConfig = {
    positiveSpeechThreshold: 0.6,
    negativeSpeechThreshold: 0.3,
    sampleRate: 16000,
    frameSize: 1600
};

class VAD {
    // types
    vad: any;
    ready: Promise<void> | null;
    initialized: boolean;
    
    constructor() {
        this.vad = null;
        this.ready = null;
        this.initialized = false;
    }

    async initialize(
        onSpeechStart: () => void,
        onSpeechEnd: () => void
    ) {
        if (this.initialized) {
            return;
        }

        this.ready = RealTimeVAD.new({
            onSpeechStart: () => {
                console.log("[VAD] Speech started");
                onSpeechStart();
            },
            onSpeechEnd: () => {
                console.log("[VAD] Speech ended");
                onSpeechEnd();
            },
            ...thresholdConfig,
        }).then((vad: any) => {
            this.vad = vad;
            this.vad.start();
            this.initialized = true;
            console.log("[VAD] Initialized and started");
        });

        await this.ready;
    }

    pause() {
        if (this.vad) {
            this.vad.pause();
        }
    }

    private pcm16leBufferToFloat32(buffer: Buffer): Float32Array {
        const sampleCount = Math.floor(buffer.length / 2);
        const float32 = new Float32Array(sampleCount);
        for (let i = 0; i < sampleCount; i++) {
            const int16 = buffer.readInt16LE(i * 2);
            float32[i] = int16 / 32768;
        }
        return float32;
    }

    async processAudioChunk(chunk: Float32Array | Buffer) {
        if (!this.initialized || !this.vad) {
            throw new Error("VAD is not initialized");
        }
        if (chunk instanceof Buffer) {
            chunk = this.pcm16leBufferToFloat32(chunk);
        }
        await this.vad.processAudio(chunk);
    }

    async destroy() {
        if (!this.vad) {
            return;
        }
        await this.vad.flush();
        this.vad.destroy();
        this.vad = null;
        this.ready = null;
        this.initialized = false;
    }
}

module.exports = {
    VAD,
};

export {};