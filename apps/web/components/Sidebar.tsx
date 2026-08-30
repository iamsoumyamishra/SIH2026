"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  ShieldCheck,
  LayoutDashboard,
  FileText,
  BookOpen,
  Cpu,
  Package,
  ScrollText,
  Radio,
  LogOut,
} from "lucide-react";
import { clearAuth, getUser } from "@/lib/api";

const nav = [
  { href: "/", label: "Workspace", icon: LayoutDashboard },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/knowledge", label: "Knowledge", icon: BookOpen },
  { href: "/models", label: "Models", icon: Cpu },
  { href: "/artifacts", label: "Artifacts", icon: Package },
  { href: "/audit", label: "Audit", icon: ScrollText },
  { href: "/sovereignty", label: "Sovereignty", icon: Radio },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const user = getUser();

  function logout() {
    clearAuth();
    router.push("/login");
  }

  return (
    <aside className="flex w-60 flex-col border-r border-brand-900 bg-panel">
      <div className="flex items-center gap-2 border-b border-brand-900 px-4 py-4">
        <ShieldCheck className="h-6 w-6 text-brand-500" />
        <div>
          <div className="text-sm font-semibold text-white">AI Workbench</div>
          <div className="text-[11px] text-slate-400">On-Premise</div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {nav.map((item) => {
          const active =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                active
                  ? "bg-brand-600 text-white"
                  : "text-slate-300 hover:bg-sovereignbg"
              }`}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-brand-900 p-3">
        <div className="mb-2 flex items-center gap-2 px-1 text-xs text-slate-400">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          {user}
        </div>
        <button
          onClick={logout}
          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-300 hover:bg-sovereignbg"
        >
          <LogOut className="h-4 w-4" /> Sign out
        </button>
      </div>
    </aside>
  );
}
