import PCMPlayer from "pcm-player";
import { useCallback, useEffect, useMemo, useRef } from "react";
import { AudioConfig } from "./AudioInterface";
import { useAppContext } from "../AppContext";

type PcmCodec = "Int16" | "Float32";

export const usePCMPlayer = () => {
    const { selectedSpeaker } = useAppContext();
    
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

    const ensurePlayer = useCallback(async () => {
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

        // Set output device if selected and supported
        if (selectedSpeaker && selectedSpeaker !== 'default' && playerRef.current && (playerRef.current as any).audioCtx) {
            const ctx = (playerRef.current as any).audioCtx;
            if (typeof ctx.setSinkId === 'function') {
                try {
                    await ctx.setSinkId(selectedSpeaker);
                    console.log("Speaker set to:", selectedSpeaker);
                } catch (err) {
                    console.error("Failed to set speaker:", err);
                }
            }
        }
    }, [selectedSpeaker]);

    // Update speaker if it changes while player is active
    useEffect(() => {
        if (playerRef.current && (playerRef.current as any).audioCtx) {
            const ctx = (playerRef.current as any).audioCtx;
            if (typeof ctx.setSinkId === 'function') {
                const sinkId = selectedSpeaker === 'default' ? '' : (selectedSpeaker || '');
                ctx.setSinkId(sinkId).catch(console.error);
            }
        }
    }, [selectedSpeaker]);

    const feedPcm = useCallback(async (chunk: ArrayBuffer) => {
        await ensurePlayer();
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
