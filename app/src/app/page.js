import styles from "./page.module.css";
import Home from "./Home";

export default function Index() {
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
        <Home />
      </main>
    </div>
  );
}
