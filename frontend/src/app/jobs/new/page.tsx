'use client';
import { useEffect } from 'react';

export default function NewJobRedirect() {
    useEffect(() => {
        window.location.href = '/create-job.html';
    }, []);
    return null;
}
