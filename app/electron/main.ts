import { app, BrowserWindow, shell, protocol, net } from "electron";
import * as path from "path";
import { pathToFileURL } from "url";
import { registerIpcHandlers, audioManager } from "./api";

const isDev = !!process.env.ELECTRON_START_URL;
const startUrl = process.env.ELECTRON_START_URL || "http://localhost:3000";

// Register custom protocol scheme
if (!isDev) {
  protocol.registerSchemesAsPrivileged([
    { scheme: "app", privileges: { secure: true, standard: true, supportFetchAPI: true } },
  ]);
}

// Hot Reload (Development only)
if (isDev) {
  const electronBinary = path.join(
    process.cwd(),
    "node_modules",
    ".bin",
    process.platform === "win32" ? "electron.cmd" : "electron"
  );

  try {
    const reloadModule = "electron-reload";
    require(reloadModule)(__dirname, {
      electron: electronBinary,
      hardResetMethod: "exit",
    });
  } catch (err) {
    console.log("electron-reload not available, skipping.");
  }
}

// Set App ID for Windows Notifications
if (process.platform === 'win32') {
  app.setAppUserModelId("com.memoryawareai.app");
}

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 560,
    minHeight: 320,
    icon: path.join(__dirname, "../public/assets/icon.png"),
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (isDev) {
    mainWindow.loadURL(startUrl);
    mainWindow.webContents.openDevTools({ mode: "detach" });
  } else {
    mainWindow.loadURL("app://./index.html");
  }

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

// Deep linking registration
if (process.defaultApp) {
  if (process.argv.length >= 2) {
    app.setAsDefaultProtocolClient("cortex-ai", process.execPath, [path.resolve(process.argv[1])]);
  }
} else {
  app.setAsDefaultProtocolClient("cortex-ai");
}

// Handle deep links (macOS)
app.on("open-url", (event, url) => {
  event.preventDefault();
  if (mainWindow) {
    mainWindow.webContents.send("auth:redirect", url);
  }
});

// Handle deep links (Windows/Linux)
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  app.quit();
} else {
  app.on("second-instance", (event, commandLine) => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();

      // Find the URL in the command line
      const url = commandLine.find((arg) => arg.startsWith("cortex-ai://"));
      if (url) {
        mainWindow.webContents.send("auth:redirect", url);
      }
    }
  });

  app.whenReady().then(() => {
    if (!isDev) {
      protocol.handle("app", (request) => {
        let url = request.url.replace("app://", "");
        if (url === "" || url === "/") {
          url = "index.html";
        }

        const extension = path.extname(url);
        if (!extension) {
          url = path.join(url, "index.html");
        }

        const filePath = path.join(__dirname, "../out", url);
        return net.fetch(pathToFileURL(filePath).toString());
      });
    }

    registerIpcHandlers();
    createWindow();

    app.on("activate", () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
      }
    });
  });
}

app.on("before-quit", async () => {
  await audioManager.stopMicRecorder();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

export {};
