"use client"

import { usePathname } from "next/navigation"
import Link from "next/link"
import { useEffect, useState } from "react"

export function Topbar() {
    const pathname = usePathname()
    const [userInitial, setUserInitial] = useState("N")

    useEffect(() => {
        // Try to get user's first name initial
        const userDataStr = localStorage.getItem("user")
        if (userDataStr) {
            try {
                const userData = JSON.parse(userDataStr)
                if (userData.full_name) {
                    setUserInitial(userData.full_name.charAt(0).toUpperCase())
                }
            } catch (e) {
                console.error("Error parsing user data", e)
            }
        }
    }, [])

    return (
        <header className="sticky top-0 z-10 flex items-center justify-between h-16 px-8 border-b border-slate-200 dark:border-slate-800 bg-background-light/80 dark:bg-background-dark/80 backdrop-blur-sm">
            <div>
                <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
                    {pathname === '/dashboard' ? 'Activity Dashboard' : pathname.split("/").filter(Boolean).map(seg => seg.charAt(0).toUpperCase() + seg.slice(1)).join(" / ")}
                </h2>
                {pathname === '/dashboard' && (
                    <p className="text-sm text-slate-500 dark:text-slate-400">Here's a summary of your hiring activity.</p>
                )}
            </div>
            <div className="flex items-center gap-4">
                <button className="p-2 rounded-full text-slate-500 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary focus:ring-offset-background-light dark:focus:ring-offset-background-dark">
                    <span className="material-symbols-outlined">notifications</span>
                </button>
                <Link href="/profile">
                    <div className="w-10 h-10 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center font-bold text-slate-600 dark:text-slate-300">
                        {userInitial}
                    </div>
                </Link>
            </div>
        </header>
    )
}
