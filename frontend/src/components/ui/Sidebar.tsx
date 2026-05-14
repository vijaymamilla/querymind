"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  MessageSquare,
  Table2,
  BookOpen,
  ScrollText,
  Shield,
  Settings2,
  Zap,
} from "lucide-react";
import { clsx } from "clsx";

const NAV_ITEMS = [
  { href: "/query", label: "Query", icon: MessageSquare },
  { href: "/admin/schema", label: "Schema", icon: Table2 },
  { href: "/admin/examples", label: "Examples", icon: BookOpen },
  { href: "/admin/logs", label: "Logs", icon: ScrollText },
  { href: "/admin/guardrails", label: "Guardrails", icon: Shield },
  { href: "/admin/config", label: "Model Config", icon: Settings2 },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 bg-gray-900 text-gray-100 flex flex-col flex-shrink-0">
      {/* Logo */}
      <div className="px-4 py-5 flex items-center gap-2 border-b border-gray-700">
        <Zap className="w-5 h-5 text-sky-400" />
        <span className="font-semibold text-sm tracking-wide">QueryMind AI</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 px-2 space-y-1">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                active
                  ? "bg-sky-600 text-white"
                  : "text-gray-400 hover:bg-gray-800 hover:text-white"
              )}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="px-4 py-3 border-t border-gray-700 text-xs text-gray-500">
        v0.1.0
      </div>
    </aside>
  );
}
