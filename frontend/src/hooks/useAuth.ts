import { useState, useEffect } from 'react';
import Cookies from 'js-cookie';
import { useRouter } from 'next/navigation';

export function useAuth(requireAuth = true) {
    // Initialize state based on current cookie value to avoid cascading renders
    const [isAuthenticated, setIsAuthenticated] = useState(() => {
        return !!Cookies.get('token');
    });
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();

    useEffect(() => {
        const token = Cookies.get('token');
        const hasToken = !!token;

        // Only update if state differs to prevent unnecessary renders
        if (hasToken !== isAuthenticated) {
            // eslint-disable-next-line react-hooks/set-state-in-effect
            setIsAuthenticated(hasToken);
        }

        if (!hasToken && requireAuth) {
            router.push('/login');
        }

        setIsLoading(false);
    }, [requireAuth, router, isAuthenticated]);

    return { isAuthenticated, isLoading };
}
