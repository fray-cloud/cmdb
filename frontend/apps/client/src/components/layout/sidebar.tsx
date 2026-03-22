"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  ChevronDown,
  Globe,
  Hash,
  Home,
  Layers,
  Network,
  Server,
  Shield,
  Target,
  Cable,
  FolderTree,
} from "lucide-react";

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
}

const ipamItems: NavItem[] = [
  { label: "Prefixes", href: "/ipam/prefixes", icon: Network },
  { label: "IP Addresses", href: "/ipam/ip-addresses", icon: Hash },
  { label: "IP Ranges", href: "/ipam/ip-ranges", icon: Cable },
  { label: "VRFs", href: "/ipam/vrfs", icon: Layers },
  { label: "VLANs", href: "/ipam/vlans", icon: Server },
  { label: "VLAN Groups", href: "/ipam/vlan-groups", icon: FolderTree },
  { label: "ASNs", href: "/ipam/asns", icon: Globe },
  { label: "RIRs", href: "/ipam/rirs", icon: Shield },
  { label: "Route Targets", href: "/ipam/route-targets", icon: Target },
];

export function Sidebar({ className }: { className?: string }) {
  const pathname = usePathname();
  const [ipamOpen, setIpamOpen] = useState(
    pathname.startsWith("/ipam"),
  );

  return (
    <aside
      className={cn(
        "flex h-full w-64 flex-col border-r bg-sidebar text-sidebar-foreground",
        className,
      )}
    >
      <div className="flex h-14 items-center border-b px-4">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <Network className="h-5 w-5" />
          <span>CMDB</span>
        </Link>
      </div>

      <nav className="flex-1 overflow-y-auto p-3">
        <ul className="space-y-1">
          <li>
            <Link
              href="/"
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                pathname === "/" &&
                  "bg-sidebar-accent text-sidebar-accent-foreground",
              )}
            >
              <Home className="h-4 w-4" />
              Dashboard
            </Link>
          </li>

          <li>
            <button
              onClick={() => setIpamOpen(!ipamOpen)}
              className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
            >
              <Network className="h-4 w-4" />
              IPAM
              <ChevronDown
                className={cn(
                  "ml-auto h-4 w-4 transition-transform",
                  ipamOpen && "rotate-180",
                )}
              />
            </button>
            {ipamOpen && (
              <ul className="ml-4 mt-1 space-y-1 border-l pl-3">
                {ipamItems.map((item) => (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={cn(
                        "flex items-center gap-3 rounded-md px-3 py-1.5 text-sm transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                        pathname === item.href &&
                          "bg-sidebar-accent font-medium text-sidebar-accent-foreground",
                      )}
                    >
                      <item.icon className="h-4 w-4" />
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </li>
        </ul>
      </nav>
    </aside>
  );
}
