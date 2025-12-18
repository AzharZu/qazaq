import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { useAuthStore } from "@/store/authStore";
import { useDictionaryStore } from "@/store/dictionaryStore";

const links = [
  { href: "/", label: "Главная" },
  { href: "/courses", label: "Курсы" },
  { href: "/level-test", label: "Тест" },
  { href: "/dictionary", label: "Словарь" },
  { href: "/autochecker", label: "AutoChecker" },
  { href: "/profile", label: "Профиль" },
];

export default function Navbar() {
  const router = useRouter();
  const { user, token, logout } = useAuthStore();
  const { words } = useDictionaryStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const isAuthed = mounted && Boolean(token);

  const isActive = (href: string) => {
    if (href === "/") return router.pathname === "/";
    return router.pathname.startsWith(href);
  };

  const handleLogout = async () => {
    await logout();
  };

  return (
    <header className="sticky top-0 z-30 border-b border-slate/40 bg-midnight/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center gap-4 px-6 py-4">
        <Link href="/" className="flex items-center gap-2 rounded-xl bg-slate/50 px-4 py-2 text-sm font-semibold text-gold shadow-soft">
          <span className="text-white">Qazaq</span>
          <span className="text-gold">Mentor</span>
        </Link>
        <nav className="hidden items-center gap-2 md:flex">
          {links.map((link) => {
            const showCount = link.href === "/dictionary" && words.length > 0;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-xl px-3 py-2 text-sm font-semibold transition ${
                  isActive(link.href)
                    ? "bg-slate text-gold"
                    : "text-ink hover:bg-slate/50 hover:text-white"
                }`}
              >
                {link.label}
                {showCount ? <span className="ml-2 rounded-full bg-gold px-2 py-0.5 text-xs text-slateDeep">{words.length}</span> : null}
              </Link>
            );
          })}
        </nav>
        <div className="ml-auto flex items-center gap-2">
          {isAuthed ? (
            <>
              <Link
                href="/profile"
                className="hidden rounded-xl bg-slate/70 px-3 py-2 text-sm font-semibold text-ink hover:bg-slate sm:inline-flex"
              >
                {user?.name || user?.email || "Профиль"}
              </Link>
              <button
                onClick={handleLogout}
                className="rounded-xl bg-slate px-4 py-2 text-sm font-semibold text-ink transition hover:bg-slateDeep hover:text-white"
              >
                Выйти
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="rounded-xl bg-slate/60 px-4 py-2 text-sm font-semibold text-ink transition hover:bg-slate"
              >
                Войти
              </Link>
              <Link
                href="/register"
                className="rounded-xl bg-gold px-4 py-2 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
              >
                Регистрация
              </Link>
            </>
          )}
        </div>
      </div>
      <div className="flex gap-2 border-t border-slate/40 px-6 pb-3 pt-2 md:hidden">
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={`flex-1 rounded-lg px-3 py-2 text-center text-sm font-semibold transition ${
              isActive(link.href) ? "bg-slate text-gold" : "text-ink hover:bg-slate/50 hover:text-white"
            }`}
          >
            {link.label}
          </Link>
        ))}
      </div>
    </header>
  );
}
