import { auth, clerkClient } from '@clerk/nextjs/server';
import { redirect } from 'next/navigation';
import DashboardLayoutClient from './client-layout';

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  try {
    const { userId } = await auth();

    if (userId) {
      const client = await clerkClient();
      const user = await client.users.getUser(userId);
      const role = user.publicMetadata?.role;

      if (!role) {
        redirect('/onboarding');
      }
    }
  } catch (err) {
    // Graceful fallback when Clerk API keys are unconfigured in environment
  }

  // Pass children to the client-side layout component
  return <DashboardLayoutClient>{children}</DashboardLayoutClient>;
}
