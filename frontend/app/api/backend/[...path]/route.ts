import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const resolvedParams = await params;
  return await proxyRequest(req, resolvedParams.path);
}

export async function POST(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const resolvedParams = await params;
  return await proxyRequest(req, resolvedParams.path);
}

export async function PATCH(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const resolvedParams = await params;
  return await proxyRequest(req, resolvedParams.path);
}

export async function DELETE(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const resolvedParams = await params;
  return await proxyRequest(req, resolvedParams.path);
}

async function proxyRequest(req: NextRequest, pathArray: string[]) {
  let backendBase = process.env.NEXT_PUBLIC_API_URL || 'https://recruitcore-production.up.railway.app';
  if (!backendBase.includes('localhost') && backendBase.startsWith('http://')) {
    backendBase = backendBase.replace('http://', 'https://');
  }
  const cleanBase = backendBase.endsWith('/') ? backendBase.slice(0, -1) : backendBase;
  
  // Construct the target URL
  const path = pathArray.join('/');
  const searchParams = req.nextUrl.searchParams.toString();
  const targetUrl = `${cleanBase}/${path}${searchParams ? '?' + searchParams : ''}`;

  // Forward the request
  const headers = new Headers(req.headers);
  headers.delete("host"); // Let fetch set the correct host
  headers.delete("referer");

  try {
    const init: RequestInit = {
      method: req.method,
      headers,
      redirect: 'manual', // Manually handle redirects to preserve headers
    };

    if (req.method !== 'GET' && req.method !== 'HEAD') {
      const clonedReq = req.clone();
      init.body = await clonedReq.blob();
    }

    let response = await fetch(targetUrl, init);
    
    // Handle redirect manually to preserve Authorization headers and force HTTPS
    if ([301, 302, 307, 308].includes(response.status)) {
      let location = response.headers.get("location");
      if (location) {
        // Force HTTPS if it's hitting our backend
        if (location.startsWith("http://")) {
          location = location.replace("http://", "https://");
        }
        // Follow redirect with original headers
        response = await fetch(location, init);
      }
    }
    
    // We cannot construct NextResponse directly with response.body if it's null
    const responseHeaders = new Headers(response.headers);
    responseHeaders.set("x-proxied-by", "nextjs-api-route");
    
    // Ensure CORS headers are passed through if needed
    responseHeaders.delete("content-encoding");

    return new NextResponse(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    console.error("Proxy error:", error);
    return new NextResponse(JSON.stringify({ detail: "Internal Proxy Error", error: String(error) }), { 
      status: 500,
      headers: { "Content-Type": "application/json" }
    });
  }
}
