// frontend/src/lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;
if (!API_BASE_URL) {
  throw new Error("NEXT_PUBLIC_API_URL is required");
}

function getAuthHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token =
    window.localStorage.getItem("token") ||
    window.sessionStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function buildUrl(endpoint: string, params?: Record<string, string | number | boolean | undefined>): string {
  const url = new URL(`${API_BASE_URL}${endpoint}`);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, String(value));
      }
    });
  }
  return url.toString();
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

class ApiClient {
  async get<T>(
    endpoint: string,
    options?: { params?: Record<string, string | number | boolean | undefined> }
  ): Promise<{ data: T }> {
    const response = await fetch(buildUrl(endpoint, options?.params), {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
    });

    if (!response.ok) {
      handleAuthError(response);
      throw await parseError(response);
    }

    const data: T = await response.json();
    return { data };
  }
  async getBlob(
  endpoint: string,
  options?: { params?: Record<string, string | number | boolean | undefined> }
): Promise<Blob> {
  const response = await fetch(buildUrl(endpoint, options?.params), {
    method: "GET",
    headers: {
      ...getAuthHeaders(),
    },
  });

  if (!response.ok) {
    handleAuthError(response);
    throw await parseError(response);
  }

  return await response.blob();
}

  async post<T, B = unknown>(endpoint: string, body: B): Promise<{ data: T }> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      handleAuthError(response);
      throw await parseError(response);
    }

    const data: T = await response.json();
    return { data };
  }

  async postForm<T>(endpoint: string, formData: FormData): Promise<{ data: T }> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      headers: {
        ...getAuthHeaders(),
      },
      body: formData,
    });

    if (!response.ok) {
      handleAuthError(response);
      throw await parseError(response);
    }

    const data: T = await response.json();
    return { data };
  }

  async patch<T, B = unknown>(endpoint: string, body: B): Promise<{ data: T }> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      handleAuthError(response);
      throw await parseError(response);
    }

    const data: T = await response.json();
    return { data };
  }

  async delete(endpoint: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "DELETE",
      headers: {
        ...getAuthHeaders(),
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
