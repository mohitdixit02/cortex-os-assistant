const { ipcMain } = require("electron");
const path = require("path");
const AudioRecorder = require("node-audiorecorder");
const soxPath = require('sox-bin');

const soxDir = path.dirname(soxPath);
process.env.PATH = `${soxDir};${process.env.PATH}`;
process.env.AUDIODRIVER = 'waveaudio';

console.log("Using SoX binary at:", soxPath);

let micRecorder = null;
let micStream = null;
let micOwnerWebContents = null;

function stopMicRecorder() {
  if (micStream) {
    micStream.removeAllListeners("data");
    micStream.removeAllListeners("error");
    micStream = null;
  }

  if (micRecorder) {
    try {
      micRecorder.stop();
    } catch (error) {
      console.error("Failed to stop microphone recorder:", error);
    }
    micRecorder = null;
  }

  micOwnerWebContents = null;
}

function registerIpcHandlers() {
  ipcMain.handle("assistant:ping-backend", async (_event, backendUrl) => {
    const base = (backendUrl || "http://127.0.0.1:8000").replace(/\/$/, "");

    try {
      const response = await fetch(`${base}/health`, { method: "GET" });
      return {
        ok: response.ok,
        status: response.status,
        url: `${base}/health`,
      };
    } catch (error) {
      return {
        ok: false,
        status: null,
        url: `${base}/health`,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  });

  ipcMain.handle("assistant:mic-start", async (event, options = {}) => {
    stopMicRecorder();

    const recorderOptions = {
      program: "sox",
      bits: 16,
      channels: 1,
      encoding: "signed-integer",
      rate: 16000,
      type: "wav",
      silence: 0,
      ...options,
    };

    try {
      micRecorder = new AudioRecorder(recorderOptions, console).start();
      micStream = micRecorder.stream();
      micOwnerWebContents = event.sender;

      if (!micStream) {
        throw new Error("Microphone stream is not available");
      }

      micStream.on("data", (chunk) => {
        if (!micOwnerWebContents || micOwnerWebContents.isDestroyed()) {
          return;
        }
        micOwnerWebContents.send("assistant:mic-chunk", chunk);
      });

      micStream.on("error", (error) => {
        if (micOwnerWebContents && !micOwnerWebContents.isDestroyed()) {
          micOwnerWebContents.send("assistant:mic-error", String(error));
        }
      });

      micRecorder.on("error", (error) => {
        if (micOwnerWebContents && !micOwnerWebContents.isDestroyed()) {
          micOwnerWebContents.send("assistant:mic-error", String(error));
        }
      });

      return { ok: true };
    } catch (error) {
      stopMicRecorder();
      return {
        ok: false,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  });

  ipcMain.handle("assistant:mic-stop", async () => {
    stopMicRecorder();
    return { ok: true };
  });
}

module.exports = {
  registerIpcHandlers,
  stopMicRecorder,
};