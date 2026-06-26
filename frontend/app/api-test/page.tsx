'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';

type HealthResponse = {
  status: string;
  database?: string;
};

export default function ApiTest() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<HealthResponse>('/health')
      .then((res) => {
        setHealth(res.data);
        setLoading(false);
      })
      .catch((err: Error) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">API Connection Test</h1>

        <div className="bg-white rounded-lg shadow-md p-6 mb-4">
          <h2 className="text-xl font-semibold mb-4">Backend Health Check</h2>

          {loading && <div className="text-gray-600">Loading...</div>}

          {health && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="text-green-800 font-semibold">Connected successfully</div>
              <pre className="text-sm text-green-700 bg-green-100 p-3 rounded mt-2 overflow-auto">
                {JSON.stringify(health, null, 2)}
              </pre>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="text-red-800 font-semibold">Connection failed</div>
              <p className="text-red-700 mt-2">Error: {error}</p>
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Quick Links</h2>
          <div className="space-y-2">
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="block text-blue-600 hover:text-blue-800 hover:underline"
            >
              Backend API docs
            </a>

            <Link href="/" className="block text-blue-600 hover:text-blue-800 hover:underline">
              Back to home
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
