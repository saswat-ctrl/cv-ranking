"use client"

import { usePathname } from "next/navigation"
import { Bell, User } from "lucide-react"
import { Button } from "@/components/ui/button"

import Link from "next/link"

export function Topbar() {
    const pathname = usePathname()

    // Generate breadcrumb from pathname
    const pathSegments = pathname.split("/").filter(Boolean)
    const breadcrumb = pathSegments.length > 0
        ? pathSegments.map(seg => seg.charAt(0).toUpperCase() + seg.slice(1)).join(" / ")
        : "Dashboard"

    return (
        <div className="flex h-16 items-center justify-between border-b bg-background px-6">
            {/* Breadcrumb */}
            <div>
                <h2 className="text-lg font-semibold">{breadcrumb}</h2>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-4">
                <Button variant="ghost" size="icon">
                    <Bell className="h-5 w-5" />
                </Button>
                <Link href="/profile">
                    <Button variant="ghost" size="icon">
                        <User className="h-5 w-5" />
                    </Button>
                </Link>
            </div>
        </div>
    )
}
