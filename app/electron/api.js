const { ipcMain } = require("electron");
ipcMain.handle("assistant:ping-backend", async (_event, backendUrl) => {
  const base = (backendUrl || "http://127.0.0.1:8000").replace(/\/$/, "");
    console.log(`Pinging backend at ${base}/health...`);

  try {
    // const response = await fetch(`${base}/health`, {
    //   method: "GET",
    // });

    // return {
    //   ok: response.ok,
    //   status: response.status,
    //   url: `${base}/health`,
    // };
    return {
        ok: true,
        status: 200,
        url: `${base}/health`,
        type: "mock",
    }
  } catch (error) {
    return {
      ok: false,
      status: null,
      url: `${base}/health`,
      error: error instanceof Error ? error.message : String(error),
    };
  }
});


/*
    Audio Stream Input - Microphone
*/
ipcMain.handle("assistant:audio-input-stream", async (_event) => {
    const { Readable } = require("stream");
    const { spawn } = require("child_process");
    const micProcess = spawn("ffmpeg", [
        "-f", "dshow",
        "-i", "audio=Microphone (Realtek(R) Audio)",
        "-f", "s16le",
        "-ac", "1",
        "-ar", "16000",
        "-"
    ]);

    const audioStream = new Readable().wrap(micProcess.stdout);

    micProcess.stderr.on("data", (data) => {
        console.error(`FFmpeg error: ${data}`);
    });
});
