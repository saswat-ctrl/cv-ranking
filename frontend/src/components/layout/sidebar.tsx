"use client"

import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"

export function Sidebar() {
    const pathname = usePathname()
    const router = useRouter()

    const handleLogout = (e: React.MouseEvent) => {
        e.preventDefault()
        localStorage.removeItem('token')
        document.cookie = 'token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;'
        router.push('/login')
    }

    return (
        <aside className="w-20 flex flex-col items-center border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950">
            <div className="h-16 flex items-center justify-center border-b border-slate-200 dark:border-slate-800 w-full">
                <img src="/images/logo.png" alt="HR Dashboard Logo" className="w-12 h-12 object-contain" />
            </div>
            <nav className="flex-1 flex flex-col items-center w-full py-6 space-y-4">
                <Link
                    href="/dashboard"
                    className={`nav-item flex items-center justify-center p-3 rounded ${pathname === '/dashboard'
                        ? 'text-primary bg-green-100 dark:bg-green-900/50'
                        : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
                        }`}
                >
                    <span className="material-symbols-outlined text-2xl">dashboard</span>
                    <span className="sr-only">Dashboard</span>
                    <span className="tooltip">Dashboard</span>
                </Link>
                <Link
                    href="/jobs"
                    className={`nav-item flex items-center justify-center p-3 rounded ${pathname?.startsWith('/jobs')
                        ? 'text-primary bg-green-100 dark:bg-green-900/50'
                        : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
                        }`}
                >
                    <span className="material-symbols-outlined text-2xl">work</span>
                    <span className="sr-only">Jobs</span>
                    <span className="tooltip">Jobs</span>
                </Link>
                <Link
                    href="/settings"
                    className={`nav-item flex items-center justify-center p-3 rounded ${pathname?.startsWith('/settings')
                        ? 'text-primary bg-green-100 dark:bg-green-900/50'
                        : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
                        }`}
                >
                    <span className="material-symbols-outlined text-2xl">settings</span>
                    <span className="sr-only">Settings</span>
                    <span className="tooltip">Settings</span>
                </Link>
            </nav>
            <div className="py-4 border-t border-slate-200 dark:border-slate-800 w-full flex justify-center">
                <a
                    href="#"
                    onClick={handleLogout}
                    className="nav-item flex items-center justify-center p-3 rounded text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                    <span className="material-symbols-outlined text-2xl">logout</span>
                    <span className="sr-only">Logout</span>
                    <span className="tooltip">Logout</span>
                </a>
            </div>
        </aside>
    )
}
