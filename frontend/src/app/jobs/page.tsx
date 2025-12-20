'use client';
import { useEffect } from 'react';
import FullScreenLoader from '@/components/FullScreenLoader';

export default function JobsRedirect() {
    useEffect(() => {
        window.location.href = '/jobs.html';
    }, []);
    return <FullScreenLoader />;
}
