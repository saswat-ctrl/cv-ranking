'use client';

import { useEffect } from 'react';
import FullScreenLoader from '@/components/FullScreenLoader';

export default function DashboardPage() {
    useEffect(() => {
        window.location.href = '/dashboard.html';
    }, []);

    return <FullScreenLoader />;
}
