import PCMPlayer from "pcm-player";
import { useCallback, useEffect, useMemo, useRef } from "react";
import { AudioConfig } from "./AudioInterface";

type PcmCodec = "Int16" | "Float32";

export const usePCMPlayer = () => {
    // Audio Player
    const playerRef = useRef<PCMPlayer | null>(null);
    
    // Audio Configuration for incoming audio (Default in case AudioManager doesn't provide config)
    const audioConfigRef = useRef<AudioConfig>({
        codec: "Float32" as PcmCodec,
        sampleRate: 24000,
        channels: 1,
    });

    const reInitializePlayer = useCallback(async (audioConfig?: AudioConfig) => {
        console.log("Resetting PCM Player");
        if (playerRef.current) {
            playerRef.current.destroy();
            playerRef.current = null;
        }

        // Update audio configuration if provided
        if (audioConfig) {
            audioConfigRef.current = audioConfig;
            console.log("Audio Config Ref:", audioConfigRef.current);
        }
    }, []);

    const ensurePlayer = useCallback(() => {
        if (playerRef.current) {
            return;
        }

        playerRef.current = new PCMPlayer({
            inputCodec: audioConfigRef.current.codec,
            channels: audioConfigRef.current.channels,
            sampleRate: audioConfigRef.current.sampleRate,
            flushTime: 120,
            fftSize: 2048,
        });
    }, []);

    const feedPcm = useCallback(async (chunk: ArrayBuffer) => {
        ensurePlayer();
        if (!playerRef.current) {
            return;
        }

        playerRef.current.feed(chunk);
    }, [ensurePlayer]);

    return {
        reInitializePlayer,
        feedPcm,
        ensurePlayer
    };
}