'use client';
import { useEffect } from 'react';
import FullScreenLoader from '@/components/FullScreenLoader';

export default function ProfileRedirect() {
    useEffect(() => {
        window.location.href = '/profile.html';
    }, []);
    return <FullScreenLoader />;
}
