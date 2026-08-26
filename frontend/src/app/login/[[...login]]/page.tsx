import { SignIn } from "@clerk/nextjs";

export default function LoginPage() {
  return (
    <div className="auth-page-bg auth-mesh-bg flex items-center justify-center min-h-screen">
      <SignIn />
    </div>
  );
}
