// Server-side proxy for PDF export: authenticates to the FastAPI backend and
// streams back the generated conversation-transcript PDF.
import { NextRequest } from "next/server";
import { auth } from "@clerk/nextjs/server";

const BACKEND_URL =
  process.env.BACKEND_URL ??
  (process.env.NEXT_PUBLIC_API_URL ? process.env.NEXT_PUBLIC_API_URL.replace(/\/api\/v1\/?$/, "") : "https://crimerakshak-backend-50044226161.development.catalystappsail.in");

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ conversationId: string }> },
) {
  let token: string | null = null;
  try {
    const authRes = await auth();
    if (authRes?.getToken) {
      token = await authRes.getToken();
    }
  } catch (e) {
    // Clerk fallback
  }

  const { conversationId } = await params;
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/chat/${conversationId}/pdf`, {
      headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    });
    if (!res.ok) {
      const text = await res.text();
      return Response.json({ error: `backend ${res.status}`, detail: text }, { status: 502 });
    }
    const blob = await res.arrayBuffer();
    return new Response(blob, {
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `attachment; filename="conversation_${conversationId}.pdf"`,
      },
    });
  } catch (err) {
    return Response.json({ error: "proxy failure", detail: String(err) }, { status: 500 });
  }
}
