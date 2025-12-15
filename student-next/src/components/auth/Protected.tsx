"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

export function Protected({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, loading } = useAuth();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      const redirect = pathname ? `?next=${encodeURIComponent(pathname)}` : "";
      router.replace(`/login${redirect}`);
    }
  }, [isAuthenticated, loading, pathname, router]);

  if (loading) {
    return (
      <div className="mx-auto max-w-6xl rounded-xl bg-white p-6 shadow-soft">
        <p className="text-slate-600">Проверяем авторизацию...</p>
      </div>
    );
  }

  if (!isAuthenticated) return null;
  return <>{children}</>;
}

export default Protected;
