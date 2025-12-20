'use client';
import { useEffect } from 'react';
import FullScreenLoader from '@/components/FullScreenLoader';

export default function SettingsRedirect() {
    useEffect(() => {
        window.location.href = '/settings.html';
    }, []);
    return <FullScreenLoader />;
}
