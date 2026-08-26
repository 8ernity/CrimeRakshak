// In production (e.g. Vercel) NEXT_PUBLIC_API_URL is typically unset and we fall
// back to a same-origin relative path, which the platform rewrites route to the
// backend function (see vercel.json). Local dev sets it explicitly in .env.local.
export const API_BASE = "/api/v1";


let cachedToken: string | null = null;

async function performLogin() {
  try {
    const url = `${API_BASE}/auth/login`;
    console.log("Attempting to login at:", url, "API_BASE is:", API_BASE);
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        username: "admin",
        password: "ChangeMe123!",
      }),
    });

    if (res.ok) {
      const data = await res.json();
      cachedToken = data.access_token;
      if (typeof window !== "undefined") {
        localStorage.setItem("auth_token", cachedToken as string);
      }
      return cachedToken;
    }
  } catch (error) {
    console.error("Failed to auto-login:", error);
declare global {
  interface Window {
    Clerk?: any;
  }
}

function getCookie(name: string) {
  if (typeof window === "undefined") return null;
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop()?.split(";").shift();
  return null;
}

async function getToken(): Promise<string | null> {
  // 1. Try Clerk session (primary method)
  if (typeof window !== "undefined") {
    // Wait up to 2s for Clerk to initialize if it's not ready yet
    if (window.Clerk && !window.Clerk.session) {
      await new Promise<void>((resolve) => {
        let attempts = 0;
        const interval = setInterval(() => {
          if (window.Clerk?.session || attempts > 20) {
            clearInterval(interval);
            resolve();
          }
          attempts++;
        }, 100);
      });
    }
    if (window.Clerk?.session) {
      try {
        const clerkToken = await window.Clerk.session.getToken();
        if (clerkToken) return clerkToken;
      } catch (e) {
        console.warn("Failed to get Clerk token", e);
      }
    }
  }

  // 2. Try legacy cached token
  if (cachedToken) return cachedToken;
  
  if (typeof window !== "undefined") {
    cachedToken = localStorage.getItem("auth_token") || getCookie("auth_token") || null;
    return cachedToken;
  }
  
  return null;
}

export async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  let token = await getToken();
  
  const headers: Record<string, string> = {
    ...((options.headers as Record<string, string>) || {}),
  };

  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    throw new Error(`API Error: ${res.status} ${res.statusText}`);
  }

  return res.json();
}
