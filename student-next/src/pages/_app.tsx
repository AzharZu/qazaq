import type { AppProps } from "next/app";
import { useEffect } from "react";
import Navbar from "@/components/Navbar";
import { useAuthStore } from "@/store/authStore";
import "@/styles/globals.css";

export default function App({ Component, pageProps }: AppProps) {
  const loadUser = useAuthStore((s) => s.loadUser);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  return (
    <div className="min-h-screen bg-night text-ink">
      <Navbar />
      <main className="mx-auto max-w-6xl px-6 py-10">
        <Component {...pageProps} />
      </main>
    </div>
  );
}
