import { AlertCircle, ArrowRight, Fingerprint, LockKeyhole, ShieldCheck } from "lucide-react";
import { useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { login } from "@/api";
import type { AuthUser } from "@/data";

export function LoginPage({ onLogin }: { onLogin: (user: AuthUser) => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  return (
    <main className="auth-page">
      <section className="auth-brand-panel">
        <a className="auth-brand" href="/">
          <span><ShieldCheck /></span>
          PreventA
        </a>
        <div className="auth-brand-copy">
          <Badge variant="secondary">CONTROLLED ENGINEERING SYSTEM</Badge>
          <h1>Risk decisions deserve more than a spreadsheet.</h1>
          <p>
            Run HAZOP and LOPA studies with evidence, role controls and a complete
            decision trail. AI output remains a reviewable candidate, never a decision.
          </p>
        </div>
        <div className="auth-trust-grid">
          <div><strong>RBAC</strong><span>Capability by role</span></div>
          <div><strong>CITED AI</strong><span>Evidence required</span></div>
          <div><strong>ON-PREM</strong><span>Your data boundary</span></div>
        </div>
      </section>

      <section className="auth-form-panel">
        <Card className="auth-card">
          <CardHeader>
            <div className="auth-icon"><Fingerprint /></div>
            <CardTitle>Enter the workspace</CardTitle>
            <CardDescription>
              Continue with your organization account. Sessions expire after 12 hours.
            </CardDescription>
          </CardHeader>
          <form
            onSubmit={async (event) => {
              event.preventDefault();
              setPending(true);
              setError(null);
              try {
                const session = await login(email, password);
                onLogin(session.user);
                window.history.replaceState({}, "", "/app");
              } catch {
                setError("The email or password could not be verified.");
              } finally {
                setPending(false);
              }
            }}
          >
            <CardContent>
              <FieldGroup>
                <Field data-invalid={Boolean(error)}>
                  <FieldLabel htmlFor="email">Email</FieldLabel>
                  <Input
                    id="email"
                    type="email"
                    autoComplete="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    aria-invalid={Boolean(error)}
                    required
                  />
                </Field>
                <Field data-invalid={Boolean(error)}>
                  <FieldLabel htmlFor="password">Password</FieldLabel>
                  <Input
                    id="password"
                    type="password"
                    autoComplete="current-password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    aria-invalid={Boolean(error)}
                    required
                  />
                  <FieldDescription>
                    Your account and role are managed by your system administrator.
                  </FieldDescription>
                </Field>
              </FieldGroup>
              {error && (
                <Alert variant="destructive" className="auth-alert">
                  <AlertCircle />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
            </CardContent>
            <CardFooter>
              <Button type="submit" size="lg" disabled={pending} className="auth-submit">
                {pending ? "Authenticating..." : "Continue securely"}
                <ArrowRight data-icon="inline-end" />
              </Button>
            </CardFooter>
          </form>
        </Card>
        <p className="auth-footnote">
          <LockKeyhole size={13} /> Access is protected by an encrypted session cookie.
        </p>
      </section>
    </main>
  );
}
