import PCMPlayer from "pcm-player";
import { useCallback, useEffect, useMemo, useRef } from "react";

type PcmCodec = "Int16" | "Float32";
interface PCMPlayerType {
    playerRef: React.RefObject<PCMPlayer | null>;
    audioConfigRef: React.RefObject<{
        codec: PcmCodec;
        sampleRate: number;
        channels: number;
    }>;
}

export const usePCMPlayer = () => {
    // Audio Player
    const playerRef = useRef<PCMPlayer | null>(null);
    
    // Audio Configuration for incoming audio
    const audioConfigRef = useRef({
        codec: "Float32" as PcmCodec,
        sampleRate: 24000,
        channels: 1,
    });

    const resetPlayer = async (audioConfig?: { codec: PcmCodec; sampleRate: number; channels: number }) => {
        console.log("Resetting PCM Player");
        if (playerRef.current) {
            playerRef.current.destroy();
            playerRef.current = null;
        }

        // Update audio configuration if provided
        if (audioConfig) {
            audioConfigRef.current = {
                codec: audioConfig.codec || audioConfigRef.current.codec,
                sampleRate: audioConfig.sampleRate || audioConfigRef.current.sampleRate,
                channels: audioConfig.channels || audioConfigRef.current.channels,
            };
        }
    };

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
    }, [audioConfigRef, playerRef]);

    const feedPcm = useCallback(async (chunk: ArrayBuffer) => {
        ensurePlayer();
        if (!playerRef.current) {
            return;
        }

        playerRef.current.feed(chunk);
    }, [ensurePlayer, playerRef]);

    return {
        resetPlayer,
        feedPcm,
        ensurePlayer
    };
}