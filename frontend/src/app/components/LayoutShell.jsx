"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import Button from "./ui/Button";
import { clearUser, getUser } from "@/lib/session";
import { cn } from "@/lib/utils";

const navItems = [
  { label: "Главная", href: "/" },
  { label: "Эксперименты", href: "/experiments" },
  { label: "Новый эксперимент", href: "/experiments/new" },
  { label: "Проверка по фото", href: "/predict" },
];

function NavLink({ href, label, active }) {
  return (
    <Link
      href={href}
      className={cn(
        "rounded-lg px-3 py-2 text-sm font-semibold transition-colors",
        active
          ? "bg-blue-50 text-blue-700"
          : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
      )}
    >
      {label}
    </Link>
  );
}

export default function LayoutShell({ children }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [checkingAuth, setCheckingAuth] = useState(true);

  const showChrome = pathname !== "/login";

  const resolveActive = (href) => {
    if (href === "/") return pathname === href;
    if (href === "/experiments/new") return pathname === href;
    if (href === "/experiments" && pathname === "/experiments/new") return false;
    return pathname === href || pathname.startsWith(`${href}/`);
  };

  useEffect(() => {
    const stored = getUser();
    setUser(stored);

    if (pathname === "/login") {
      if (stored) {
        router.replace("/");
        return;
      }
      setCheckingAuth(false);
      return;
    }

    if (!stored) {
      setCheckingAuth(true);
      router.replace("/login");
      return;
    }

    setCheckingAuth(false);
  }, [pathname, router]);

  const handleLogout = () => {
    clearUser();
    setUser(null);
    router.push("/login");
  };

  const activeNav = useMemo(
    () =>
      navItems.map((item) => ({
        ...item,
        active: resolveActive(item.href),
      })),
    [pathname]
  );

  if (showChrome && (checkingAuth || !user)) {
    return (
      <div className="min-h-screen flex items-center justify-center text-slate-600">
        Загружаем интерфейс...
      </div>
    );
  }

  return (
    <div className="min-h-screen text-slate-900">
      {showChrome && (
        <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
            <Link href="/" className="flex items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-600 text-white font-black tracking-tight shadow-lg shadow-blue-200">
                SN
              </div>
              <div>
                <p className="text-sm font-semibold uppercase text-slate-500">
                  SniffNet
                </p>
              </div>
            </Link>

            <nav className="flex items-center gap-2">
              {activeNav.map((item) => (
                <NavLink key={item.href} {...item} />
              ))}
            </nav>

            <div className="flex items-center gap-3">
              {user && (
                <div className="hidden text-right sm:block">
                  <p className="text-sm font-semibold text-slate-800">
                    {user.username}
                  </p>
                  <p className="text-xs text-slate-500">id: {user.user_id}</p>
                </div>
              )}
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                Выйти
              </Button>
            </div>
          </div>
        </header>
      )}

      <main className="mx-auto max-w-6xl px-6 py-10">{children}</main>
    </div>
  );
}
