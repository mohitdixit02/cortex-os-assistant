import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AppProvider } from "../components/AppContext";
import MainLayout from "../components/MainLayout";
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "Cortex AI Assistant",
  description: "Your personal AI assistant for managing day-to-day tasks, scheduling, and more. Powered by Cortex AI.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body>
        <AppProvider>
          <MainLayout>
            {children}
          </MainLayout>
          <ToastContainer 
            position="bottom-right"
            autoClose={3000}
            hideProgressBar={false}
            newestOnTop={false}
            closeOnClick
            rtl={false}
            pauseOnFocusLoss
            draggable
            pauseOnHover
            theme="dark"
          />
        </AppProvider>
      </body>
    </html>
  );
}
