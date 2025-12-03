'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function HomePage() {
    const router = useRouter();

    useEffect(() => {
        // Check if user is authenticated
        const token = localStorage.getItem('token');

        if (token) {
            // User is authenticated, redirect to dashboard
            router.push('/dashboard');
        } else {
            // User is not authenticated, redirect to login
            router.push('/login');
        }
    }, [router]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <div className="text-gray-600">Redirecting...</div>
        </div>
    );
}
