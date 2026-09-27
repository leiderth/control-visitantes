import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { authApi } from './api';
import type { AuthSession } from './api';

type Mode = 'login' | 'register';

function saveSession(session: AuthSession) {
  localStorage.setItem('access_token', session.access);
  localStorage.setItem('refresh_token', session.refresh);
  localStorage.setItem('tenant_id', String(session.tenant.id));
  localStorage.setItem('tenant_name', session.tenant.name);
  localStorage.setItem('tenant_slug', session.tenant.slug);
  localStorage.setItem('user_name', session.user.name);
  localStorage.setItem('user_role', session.user.role);
}

function messageFromError(error: unknown) {
  if (!axios.isAxiosError(error)) {
    return error instanceof Error ? error.message : 'No fue posible iniciar la sesión.';
  }
  const data: unknown = error.response?.data;
  if (data && typeof data === 'object') {
    const fields = Object.entries(data);
    const detail = fields.find(([key]) => key === 'detail')?.[1];
    if (typeof detail === 'string') return detail;
    const firstError = fields.find(([key]) => key !== 'detail')?.[1];
    if (Array.isArray(firstError) && typeof firstError[0] === 'string') return firstError[0];
  }
  return 'No se pudo completar la solicitud. Revisa los datos e inténtalo de nuevo.';
}

export function AuthPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<Mode>('login');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [tenantSlug, setTenantSlug] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = mode === 'login'
        ? await authApi.login({ tenant_slug: tenantSlug, username, password })
        : await authApi.onboard({
          tenant_slug: tenantSlug,
          username,
          password,
          company_name: companyName,
          first_name: firstName,
          last_name: lastName,
          email,
        });
      saveSession(response.data);
      navigate('/risk', { replace: true });
    } catch (submissionError) {
      setError(messageFromError(submissionError));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="auth-title">
        <div className="auth-brand"><span className="brand-mark">C</span><strong>centinela</strong></div>
        <p className="auth-eyebrow">PLATAFORMA DE SEGURIDAD</p>
        <h1 id="auth-title">{mode === 'login' ? 'Bienvenido de nuevo' : 'Crea tu espacio de seguridad'}</h1>
        <p className="auth-intro">
          {mode === 'login'
            ? 'Ingresa a la central de operaciones de tu empresa.'
            : 'Registra tu empresa y configura el acceso de tu administrador.'}
        </p>

        {error && <div className="auth-error" role="alert">{error}</div>}

        <form className="auth-form" onSubmit={submit}>
          {mode === 'register' && (
            <>
              <label>Empresa
                <input autoComplete="organization" required value={companyName} onChange={(event) => setCompanyName(event.target.value)} />
              </label>
              <div className="auth-form-row">
                <label>Nombre
                  <input autoComplete="given-name" required value={firstName} onChange={(event) => setFirstName(event.target.value)} />
                </label>
                <label>Apellido
                  <input autoComplete="family-name" required value={lastName} onChange={(event) => setLastName(event.target.value)} />
                </label>
              </div>
              <label>Correo de trabajo
                <input type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} />
              </label>
            </>
          )}

          <label>Identificador de empresa
            <input
              autoComplete="organization"
              autoCapitalize="none"
              pattern="[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*"
              placeholder="ej. seguridad-horizonte"
              required
              value={tenantSlug}
              onChange={(event) => setTenantSlug(event.target.value.toLowerCase())}
            />
            <small>Usa el identificador entregado por tu administrador.</small>
          </label>
          <label>Usuario
            <input autoComplete="username" required value={username} onChange={(event) => setUsername(event.target.value)} />
          </label>
          <label>Contraseña
            <input
              type="password"
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              minLength={mode === 'register' ? 12 : undefined}
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            {mode === 'register' && <small>Al menos 12 caracteres; evita contraseñas comunes.</small>}
          </label>
          <button className="button button-primary auth-submit" type="submit" disabled={loading}>
            {loading ? 'Procesando…' : mode === 'login' ? 'Iniciar sesión' : 'Crear empresa y continuar'}
          </button>
        </form>

        <p className="auth-switch">
          {mode === 'login' ? '¿Tu empresa aún no tiene cuenta?' : '¿Ya tienes una cuenta?'}
          <button
            type="button"
            onClick={() => { setError(''); setMode(mode === 'login' ? 'register' : 'login'); }}
          >
            {mode === 'login' ? 'Registrar empresa' : 'Iniciar sesión'}
          </button>
        </p>
        <p className="auth-security">Acceso protegido con autenticación y aislamiento de datos por empresa.</p>
      </section>
    </main>
  );
}
