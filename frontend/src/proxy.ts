import { clerkMiddleware } from "@clerk/nextjs/server";

// Auth protection is handled directly in each page/layout using auth() from "@clerk/nextjs/server".
// This proxy file just initializes Clerk middleware so session context is available everywhere.
export default clerkMiddleware();

export const config = {
  matcher: [
    // Skip Next.js internals and all static files, unless found in search params
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // Always run for API routes
    '/(api|trpc)(.*)',
  ],
};
