'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function DashboardPage() {
    const router = useRouter();

    useEffect(() => {
        // Redirect to the static dashboard HTML
        window.location.href = '/dashboard.html';
    }, []);

    return (
        <div className="flex items-center justify-center min-h-screen">
            <p>Redirecting to dashboard...</p>
        </div>
    );
}
