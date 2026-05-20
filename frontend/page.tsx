'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';

type HealthResponse = {
  status: string;
  database?: string;
};

export default function ApiTest() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    api.get<HealthResponse>('/health')
      .then((res) => setHealth(res.data))
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">API Connection Test</h1>
      {health && (
        <div className="bg-green-100 p-4 rounded">
          <pre>{JSON.stringify(health, null, 2)}</pre>
        </div>
      )}
      {error && (
        <div className="bg-red-100 p-4 rounded">
          Error: {error}
        </div>
      )}
    </div>
  );
}
