import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
  return (
    <div className="auth-page-bg auth-mesh-bg flex items-center justify-center min-h-screen">
      <SignUp />
    </div>
  );
}
