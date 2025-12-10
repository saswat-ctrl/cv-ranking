'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function HomePage() {
    const router = useRouter();

    useEffect(() => {
        // Check if user is authenticated
        const token = localStorage.getItem('token');

        if (token) {
            // Redirect authenticated users to dashboard
            router.push('/dashboard');
        } else {
            // Redirect to the static landing page for non-authenticated users
            window.location.href = '/landing.html';
        }
    }, [router]);

    return (
        <div className="flex items-center justify-center min-h-screen">
            <p>Redirecting...</p>
        </div>
    );
}
