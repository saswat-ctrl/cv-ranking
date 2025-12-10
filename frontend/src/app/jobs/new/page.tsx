'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api_client';
import { Job, getErrorMessage } from '@/types/api';

export default function NewJobPage() {
    const router = useRouter();
    const [title, setTitle] = useState('');
    const [jdText, setJdText] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            // For MVP, we'll send text directly. 
            // In future, we might upload a file to /api/v1/jobs/upload
            const response = await api.post<Job>('/jobs', {
                title,
                description: jdText,
            });

            router.push(`/jobs/${response.data.id}/upload`);
        } catch (err: unknown) {
            console.error('Job creation error:', err);
            setError(getErrorMessage(err));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-2xl mx-auto p-6">
            <h1 className="text-2xl font-bold mb-6">Create New Job</h1>

            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                    {error}
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium mb-1">Job Title</label>
                    <input
                        type="text"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        className="w-full p-2 border rounded"
                        required
                        placeholder="e.g. Senior Product Manager"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium mb-1">Job Description</label>
                    <textarea
                        value={jdText}
                        onChange={(e) => setJdText(e.target.value)}
                        className="w-full p-2 border rounded h-64 font-mono text-sm"
                        required
                        placeholder="Paste the full job description here..."
                    />
                </div>

                <button
                    type="submit"
                    disabled={loading}
                    className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
                >
                    {loading ? 'Creating...' : 'Next: Upload CVs'}
                </button>
            </form>
        </div>
    );
}
