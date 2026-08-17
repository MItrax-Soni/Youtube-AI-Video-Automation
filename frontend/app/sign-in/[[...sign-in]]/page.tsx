import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <div className="auth-page">
      <div className="auth-container">
        <SignIn
          appearance={{
            elements: {
              rootBox: "clerk-root",
              card: "clerk-card",
            },
          }}
        />
      </div>
    </div>
  );
}
