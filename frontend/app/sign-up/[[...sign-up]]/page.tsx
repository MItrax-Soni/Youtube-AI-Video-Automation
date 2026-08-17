import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
  return (
    <div className="auth-page">
      <div className="auth-container">
        <SignUp
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
