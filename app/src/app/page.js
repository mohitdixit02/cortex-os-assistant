"use client";

import { useMemo, useState } from "react";
import styles from "./page.module.css";

export default function Home() {
  const defaultBackend = useMemo(
    () => process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000",
    []
  );
  const [backendUrl, setBackendUrl] = useState(defaultBackend);
  const [checking, setChecking] = useState(false);
  const [status, setStatus] = useState("Not checked");

  const checkBackend = async () => {
    setChecking(true);

    try {
      const api = window.assistantAPI;
      if (!api?.pingBackend) {
        setStatus("Electron bridge not ready");
        return;
      }

      const result = await api.pingBackend(backendUrl);
      if (result.ok) {
        setStatus(`Connected (${result.status})`);
      } else {
        const reason = result.error ? ` - ${result.error}` : "";
        setStatus(`Failed (${result.status ?? "no response"})${reason}`);
      }
    } catch (error) {
      const reason = error instanceof Error ? error.message : String(error);
      setStatus(`Error - ${reason}`);
    } finally {
      setChecking(false);
    }
  };

  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <div className={styles.headerBlock}>
          <p className={styles.kicker}>Desktop Assistant</p>
          <h1>Memory Aware AI Client</h1>
          <p className={styles.subtext}>
            Simple Electron + Next.js starter
          </p>
        </div>
      </main>
    </div>
  );
}
