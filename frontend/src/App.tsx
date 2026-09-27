import { BrowserRouter, Navigate, NavLink, Route, Routes } from 'react-router-dom';
import { AuthPage } from '@/features/auth/AuthPage';
import { clearAuthSession } from '@/lib/api';
import { MonitoringPage } from '@/features/alarms/MonitoringPage';
import { EscortsPage } from '@/features/escorts/EscortsPage';
import { TrackingPage } from '@/features/gps/TrackingPage';
import { RiskPage } from '@/features/risk/RiskPage';
import { VisitorsPage } from '@/features/visitors/VisitorsPage';

const navigation = [
  { to: '/risk', label: 'Riesgo e incidentes', icon: '◈' },
  { to: '/monitoring', label: 'Central de monitoreo', icon: '⌁' },
  { to: '/visitors', label: 'Visitantes', icon: '◎' },
  { to: '/escorts', label: 'Escoltas', icon: '↗' },
  { to: '/tracking', label: 'Rastreo GPS', icon: '⌖' },
];

function AppShell() {
  const tenantName = localStorage.getItem('tenant_name') || 'Empresa';
  const operatorName = localStorage.getItem('user_name') || 'Operador';

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <NavLink className="brand-lockup" to="/risk" aria-label="Plataforma Centinela">
          <span className="brand-mark">C</span>
          <span><strong>centinela</strong><small>PLATAFORMA DE SEGURIDAD</small></span>
        </NavLink>
        <div className="sidebar-caption">OPERACIONES</div>
        <nav className="primary-navigation" aria-label="Navegación principal">
          {navigation.map((item) => (
            <NavLink className={({ isActive }) => `navigation-link ${isActive ? 'navigation-link-active' : ''}`} key={item.to} to={item.to}>
              <span className="navigation-icon" aria-hidden="true">{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="tenant-mark">{tenantName.slice(0, 2).toUpperCase()}</div>
          <div><strong>{tenantName}</strong><span>Espacio de trabajo</span></div>
          <span className="tenant-menu" aria-hidden="true">···</span>
        </div>
      </aside>
      <div className="app-main">
        <header className="app-topbar">
          <div className="breadcrumbs"><span>Operaciones</span><span aria-hidden="true">/</span><strong>Seguridad</strong></div>
          <div className="topbar-actions">
            <span className="system-status"><span /> Operaciones</span>
            <button className="topbar-icon" type="button" aria-label="Notificaciones">♧<i /></button>
            <div className="operator-avatar" aria-label="Perfil de operador">{operatorName.slice(0, 2).toUpperCase()}</div>
            <div className="operator-name"><strong>{operatorName}</strong><span>Central de seguridad</span></div>
            <button
              className="logout-button"
              type="button"
              onClick={() => { clearAuthSession(); window.location.assign('/login'); }}
            >
              Cerrar sesión
            </button>
          </div>
        </header>
        <Routes>
          <Route path="/" element={<Navigate to="/risk" replace />} />
          <Route path="/risk" element={<RiskPage />} />
          <Route path="/monitoring" element={<MonitoringPage />} />
          <Route path="/visitors" element={<VisitorsPage />} />
          <Route path="/escorts" element={<EscortsPage />} />
          <Route path="/tracking" element={<TrackingPage />} />
          <Route path="*" element={<Navigate to="/risk" replace />} />
        </Routes>
      </div>
    </div>
  );
}

function AuthenticatedApp() {
  if (!localStorage.getItem('access_token')) return <Navigate to="/login" replace />;
  return <AppShell />;
}

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={localStorage.getItem('access_token') ? <Navigate to="/risk" replace /> : <AuthPage />} />
        <Route path="*" element={<AuthenticatedApp />} />
      </Routes>
    </BrowserRouter>
  );
}
