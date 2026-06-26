// frontend/src/lib/api.ts
function getApiBaseUrl(): string {
  const base = process.env.NEXT_PUBLIC_API_URL;
  
  // Proxy ANY railway.app URL through Next.js to avoid ISP blocks
  if (base && base.includes('railway.app')) {
    return '/api/backend';
  }
  
  if (!base) {
    throw new Error("NEXT_PUBLIC_API_URL is required");
  }
  return base;
}

function getAuthHeaders(endpoint?: string): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token =
    window.localStorage.getItem("token") ||
    window.sessionStorage.getItem("token");
  if (!token) {
    console.warn(`[API] No token found when requesting ${endpoint || 'unknown'}`);
  }
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function buildUrl(endpoint: string, params?: Record<string, string | number | boolean | undefined>): string {
  const baseUrl = getApiBaseUrl();
  const fullPath = `${baseUrl}${endpoint}`;
  const isAbsolute = fullPath.startsWith('http');
  
  const url = new URL(fullPath, isAbsolute ? undefined : 'http://dummy.local');
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, String(value));
      }
    });
  }
  
  return isAbsolute ? url.toString() : url.pathname + url.search;
}

async function parseError(response: Response): Promise<Error> {
  let detail = `API error: ${response.status} ${response.statusText}`;
  try {
    const body = await response.json();
    if (typeof body?.detail === "string") {
      detail = body.detail;
    } else if (Array.isArray(body?.detail)) {
      detail = body.detail
        .map((item: { msg?: string } | string) =>
          typeof item === "string" ? item : item?.msg || JSON.stringify(item)
        )
        .join(", ");
    }
  } catch {
    // Keep default detail when body is not JSON
  }
  return new Error(detail);
}

function handleAuthError(response: Response): void {
  if (response.status === 401 && typeof window !== "undefined") {
    localStorage.removeItem("token");
    sessionStorage.removeItem("token");
    window.location.href = "/login";
  }
}

async function parseJsonSafe<T>(response: Response): Promise<T | null> {
  if (response.status === 204 || response.status === 205) return null;
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new Error(`Invalid JSON response: ${text.slice(0, 100)}`);
  }
}

class ApiClient {
  async get<T>(
    endpoint: string,
    options?: { params?: Record<string, string | number | boolean | undefined> }
  ): Promise<{ data: T }> {
    const response = await fetch(buildUrl(endpoint, options?.params), {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(endpoint),
      },
    });

    if (!response.ok) {
      handleAuthError(response);
      throw await parseError(response);
    }

    const data = await parseJsonSafe<T>(response);
    return { data: data as T };
  }
  async getBlob(
  endpoint: string,
  options?: { params?: Record<string, string | number | boolean | undefined> }
): Promise<Blob> {
  const response = await fetch(buildUrl(endpoint, options?.params), {
    method: "GET",
    headers: {
      ...getAuthHeaders(endpoint),
    },
  });

  if (!response.ok) {
    handleAuthError(response);
    throw await parseError(response);
  }

  return await response.blob();
}

  async post<T, B = unknown>(endpoint: string, body: B): Promise<{ data: T }> {
    const response = await fetch(`${getApiBaseUrl()}${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(endpoint),
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      handleAuthError(response);
      throw await parseError(response);
    }

    const data = await parseJsonSafe<T>(response);
    return { data: data as T };
  }

  async postForm<T>(endpoint: string, formData: FormData): Promise<{ data: T }> {
    const response = await fetch(`${getApiBaseUrl()}${endpoint}`, {
      method: "POST",
      headers: {
        ...getAuthHeaders(endpoint),
      },
      body: formData,
    });

    if (!response.ok) {
      handleAuthError(response);
      throw await parseError(response);
    }

    const data = await parseJsonSafe<T>(response);
    return { data: data as T };
  }

  async patch<T, B = unknown>(endpoint: string, body: B): Promise<{ data: T }> {
    const response = await fetch(`${getApiBaseUrl()}${endpoint}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(endpoint),
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      handleAuthError(response);
      throw await parseError(response);
    }

    const data = await parseJsonSafe<T>(response);
    return { data: data as T };
  }

  async delete(endpoint: string): Promise<void> {
    const response = await fetch(`${getApiBaseUrl()}${endpoint}`, {
      method: "DELETE",
      headers: {
        ...getAuthHeaders(endpoint),
      },
    });

    if (!response.ok) {
      handleAuthError(response);
      throw await parseError(response);
    }
  }
}

const api = new ApiClient();
export default api;
