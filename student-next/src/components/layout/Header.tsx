"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import Button from "../ui/Button";

const navItems = [
  { href: "/courses", label: "Курсы" },
  { href: "/level-test", label: "Тест уровня" },
];

export function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, user, logout, language, setLanguage } = useAuth();

  const isActive = (href: string) => pathname?.startsWith(href);
  const toggleLanguage = () => setLanguage(language === "kk" ? "ru" : "kk");

  const initial = user?.email ? user.email.charAt(0).toUpperCase() : "В";

  return (
    <header className="mb-8 border-b border-slate-200 bg-[#e5e5e5]">
      <div className="mx-auto flex max-w-6xl items-center gap-4 px-6 py-3">
        <Link href="/" className="rounded-md bg-white px-3 py-1 text-sm font-semibold text-slate-900 shadow-sm">
          Лого
        </Link>
        <nav className="flex items-center gap-2">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-md px-3 py-2 text-sm font-semibold transition ${
                isActive(item.href) ? "bg-white text-slate-900 shadow-sm" : "bg-[#d9d9d9] text-slate-800 hover:bg-[#cfcfcf]"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-3">
          <Button variant="secondary" onClick={toggleLanguage} className="px-3 py-2 text-sm">
            {language === "kk" ? "Қазақ" : "Рус"}
          </Button>
          {isAuthenticated ? (
            <div className="flex items-center gap-3">
              <Link href="/profile" className="text-sm font-medium text-slate-800 hover:text-slate-900">
                Профиль
              </Link>
              <button
                className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white"
                onClick={() => router.push("/profile")}
                title={user?.email || "Профиль"}
              >
                {initial}
              </button>
              <Button variant="ghost" className="px-3" onClick={logout}>
                Выйти
              </Button>
            </div>
          ) : (
            <Button variant="primary" href="/login" className="px-4 py-2 text-sm">
              Войти
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}

export default Header;
