'use client';

import { useEffect } from 'react';

export default function SignupRedirect() {
    useEffect(() => {
        window.location.href = '/';
    }, []);

    return (
        <div className="flex items-center justify-center min-h-screen">
            <p>Redirecting to home page...</p>
        </div>
    );
}
