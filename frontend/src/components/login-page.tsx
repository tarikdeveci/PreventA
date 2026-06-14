import { AlertCircle, ArrowRight, LockKeyhole, ShieldCheck } from "lucide-react";
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
          <Badge variant="secondary">Process Safety Workspace</Badge>
          <h1>Mühendislik kararları için kontrollü çalışma alanı.</h1>
          <p>
            HAZOP ve LOPA çalışmalarını kaynak, rol ve denetim iziyle yönetin.
            Yapay zekâ çıktıları karar değil, incelemeye açık taslaklardır.
          </p>
        </div>
        <div className="auth-trust-grid">
          <div><strong>RBAC</strong><span>Rol bazlı erişim</span></div>
          <div><strong>Atıflı AI</strong><span>Kaynak zorunluluğu</span></div>
          <div><strong>On-prem</strong><span>Müşteri veri sahipliği</span></div>
        </div>
      </section>

      <section className="auth-form-panel">
        <Card className="auth-card">
          <CardHeader>
            <div className="auth-icon"><LockKeyhole /></div>
            <CardTitle>Çalışma alanına giriş</CardTitle>
            <CardDescription>
              Kurumsal hesabınızla devam edin. Oturum 12 saat sonra otomatik kapanır.
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
                setError("Email veya parola doğrulanamadı.");
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
                  <FieldLabel htmlFor="password">Parola</FieldLabel>
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
                    Hesabınız ve rolünüz sistem yöneticiniz tarafından tanımlanır.
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
                {pending ? "Oturum açılıyor..." : "Giriş yap"}
                <ArrowRight data-icon="inline-end" />
              </Button>
            </CardFooter>
          </form>
        </Card>
        <p className="auth-footnote">
          Erişim sorunları için sistem yöneticinizle iletişime geçin.
        </p>
      </section>
    </main>
  );
}
