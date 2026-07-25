// Server-side proxy: bridges the frontend analytics UI to the FastAPI /analytics backend.
//
// Automatically acquires & caches a backend Bearer token and forwards any GET/POST
// queries to live DuckDB telemetry endpoints over the KSP dataset.

import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";

// On Vercel, BACKEND_URL is usually unset; fall back to this deployment's own
// origin so /api/v1/* is served by the backend function (see vercel.json).
const BACKEND_URL =
  process.env.BACKEND_URL ??
  (process.env.NEXT_PUBLIC_API_URL ? process.env.NEXT_PUBLIC_API_URL.replace(/\/api\/v1\/?$/, "") : "https://crimerakshak-backend-50044226161.development.catalystappsail.in");


export async function GET(
  req: NextRequest,
  context: { params: Promise<{ endpoint: string[] }> }
) {
  try {
    let token: string | null = null;
    try {
      const authRes = await auth();
      if (authRes?.getToken) {
        token = await authRes.getToken();
      }
    } catch (e) {
      // Clerk fallback
    }

    const params = await context.params;
    const path = params.endpoint.join("/");
    const searchParams = req.nextUrl.searchParams.toString();
    const targetUrl = `${BACKEND_URL}/api/v1/analytics/${path}${
      searchParams ? `?${searchParams}` : ""
    }`;

    const res = await fetch(targetUrl, {
      method: "GET",
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        "Content-Type": "application/json",
      },
      cache: "no-store",
    });

    if (!res.ok) {
      const text = await res.text();
      return NextResponse.json(
        { error: `backend error ${res.status}`, detail: text },
        { status: res.status }
      );
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      { error: "analytics proxy failure", detail: String(err) },
      { status: 500 }
    );
  }
}

export async function POST(
  req: NextRequest,
  context: { params: Promise<{ endpoint: string[] }> }
) {
  try {
    let token: string | null = null;
    try {
      const authRes = await auth();
      if (authRes?.getToken) {
        token = await authRes.getToken();
      }
    } catch (e) {
      // Clerk fallback
    }

    const params = await context.params;
    const path = params.endpoint.join("/");
    const targetUrl = `${BACKEND_URL}/api/v1/analytics/${path}`;
    const body = await req.json();

    const res = await fetch(targetUrl, {
      method: "POST",
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const text = await res.text();
      return NextResponse.json(
        { error: `backend error ${res.status}`, detail: text },
        { status: res.status }
      );
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      { error: "analytics proxy POST failure", detail: String(err) },
      { status: 500 }
    );
  }
}
