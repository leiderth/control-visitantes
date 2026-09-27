import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import { getApiErrorMessage } from '@/lib/api';
import { riskApi } from './api';
import type {
  AccionCorrectiva,
  EvaluacionRiesgo,
  EstadoIncidente,
  IncidenteRiesgo,
  NivelRiesgo,
  SeveridadIncidente,
  Sede,
} from './types';

type Tab = 'evaluaciones' | 'incidentes';
type FormKind = 'evaluacion' | 'incidente' | null;

const nivelLabels: Record<NivelRiesgo, string> = {
  bajo: 'Bajo',
  medio: 'Medio',
  alto: 'Alto',
  critico: 'Crítico',
};

const severidadLabels: Record<SeveridadIncidente, string> = {
  baja: 'Baja',
  media: 'Media',
  alta: 'Alta',
  critica: 'Crítica',
};

const estadoLabels: Record<EstadoIncidente, string> = {
  abierto: 'Abierto',
  en_seguimiento: 'En seguimiento',
  resuelto: 'Resuelto',
  cerrado: 'Cerrado',
};

const accionEstadoLabels: Record<AccionCorrectiva['estado'], string> = {
  pendiente: 'Pendiente',
  en_progreso: 'En progreso',
  completada: 'Completada',
};

function getErrorMessage(error: unknown) {
  return getApiErrorMessage(
    error,
    'No fue posible completar la operación. Revisa tu conexión e inténtalo de nuevo.',
  );
}

function formatDate(date: string | null) {
  if (!date) return 'Sin fecha';
  return new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium' }).format(new Date(`${date}T12:00:00`));
}

function localDateTimeValue() {
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  return now.toISOString().slice(0, 16);
}

export function RiskPage() {
  const [tab, setTab] = useState<Tab>('evaluaciones');
  const [form, setForm] = useState<FormKind>(null);
  const [evaluaciones, setEvaluaciones] = useState<EvaluacionRiesgo[]>([]);
  const [incidentes, setIncidentes] = useState<IncidenteRiesgo[]>([]);
  const [sedes, setSedes] = useState<Sede[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [nivelFiltro, setNivelFiltro] = useState('todos');
  const [expandedIncident, setExpandedIncident] = useState<number | null>(null);
  const [actionFormIncident, setActionFormIncident] = useState<number | null>(null);

  const cargar = useCallback(async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const [evaluacionesResponse, incidentesResponse, sedesResponse] = await Promise.all([
        riskApi.listEvaluaciones(),
        riskApi.listIncidentes(),
        riskApi.listSedes(),
      ]);
      if (
        !Array.isArray(evaluacionesResponse.data)
        || !Array.isArray(incidentesResponse.data)
        || !Array.isArray(sedesResponse.data)
      ) {
        throw new Error('La API no devolvió listas de riesgo válidas. Revisa la conexión del frontend con el backend.');
      }
      setEvaluaciones(evaluacionesResponse.data);
      setIncidentes(incidentesResponse.data);
      setSedes(sedesResponse.data);
      setError('');
    } catch {
      setError(
        'No se pudieron cargar los datos. Verifica que exista una empresa activa y que tu sesión tenga su tenant seleccionado.',
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  const metrics = useMemo(() => {
    const highRisk = evaluaciones.filter((item) => item.nivel === 'alto' || item.nivel === 'critico').length;
    const openIncidents = incidentes.filter((item) => item.estado !== 'cerrado').length;
    const correctiveActions = incidentes.flatMap((item) => item.acciones);
    const overdueActions = correctiveActions.filter(
      (item) => item.estado !== 'completada' && item.fecha_limite && item.fecha_limite < new Date().toISOString().slice(0, 10),
    ).length;
    return { highRisk, openIncidents, overdueActions, total: evaluaciones.length };
  }, [evaluaciones, incidentes]);

  const evaluacionesVisibles = evaluaciones.filter((item) => {
    const coincideTexto = `${item.cliente_nombre} ${item.vulnerabilidad}`.toLowerCase().includes(search.toLowerCase());
    return coincideTexto && (nivelFiltro === 'todos' || item.nivel === nivelFiltro);
  });

  const incidentesVisibles = incidentes.filter((item) =>
    `${item.cliente_nombre} ${item.titulo} ${item.sede_nombre ?? ''}`.toLowerCase().includes(search.toLowerCase()),
  );

  const ejecutar = async (operacion: () => Promise<unknown>) => {
    setError('');
    setSaving(true);
    try {
      await operacion();
      await cargar(false);
      setForm(null);
      setActionFormIncident(null);
    } catch (operationError) {
      setError(getErrorMessage(operationError));
    } finally {
      setSaving(false);
    }
  };

  const crearEvaluacion = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    void ejecutar(() => riskApi.createEvaluacion({
      cliente_nombre: data.get('cliente_nombre'),
      sede: data.get('sede') || null,
      vulnerabilidad: data.get('vulnerabilidad'),
      descripcion: data.get('descripcion'),
      probabilidad: Number(data.get('probabilidad')),
      impacto: Number(data.get('impacto')),
      plan_mitigacion: data.get('plan_mitigacion'),
      revisado_en: data.get('revisado_en') || null,
    }));
  };

  const crearIncidente = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    void ejecutar(() => riskApi.createIncidente({
      cliente_nombre: data.get('cliente_nombre'),
      sede: data.get('sede') || null,
      evaluacion: data.get('evaluacion') || null,
      titulo: data.get('titulo'),
      descripcion: data.get('descripcion'),
      severidad: data.get('severidad'),
      ocurrido_en: new Date(String(data.get('ocurrido_en'))).toISOString(),
    }));
  };

  const crearAccion = (event: FormEvent<HTMLFormElement>, incidenteId: number) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    void ejecutar(() => riskApi.createAccion({
      incidente: incidenteId,
      titulo: data.get('titulo'),
      descripcion: data.get('descripcion'),
      fecha_limite: data.get('fecha_limite') || null,
    }));
  };

  const actualizarIncidente = (id: number, estado: EstadoIncidente) => {
    const acciones: Partial<Record<EstadoIncidente, () => Promise<unknown>>> = {
      abierto: () => riskApi.iniciarSeguimiento(id),
      en_seguimiento: () => riskApi.resolverIncidente(id),
      resuelto: () => riskApi.cerrarIncidente(id),
    };
    const accion = acciones[estado];
    if (accion) void ejecutar(accion);
  };

  return (
    <main className="risk-page">
      <header className="page-heading">
        <div>
          <div className="eyebrow"><span className="eyebrow-dot" /> GESTIÓN DE SEGURIDAD</div>
          <h1>Riesgo e incidentes</h1>
          <p>Identifica vulnerabilidades y lleva cada incidente hasta su cierre.</p>
        </div>
        <button
          className="button button-primary"
          type="button"
          onClick={() => setForm(tab === 'evaluaciones' ? 'evaluacion' : 'incidente')}
        >
          <span aria-hidden="true">＋</span>
          {tab === 'evaluaciones' ? 'Nueva evaluación' : 'Reportar incidente'}
        </button>
      </header>

      {error && (
        <div className="notice notice-error" role="alert">
          <span>{error}</span>
          <button className="notice-dismiss" type="button" onClick={() => setError('')} aria-label="Cerrar aviso">×</button>
        </div>
      )}

      <section className="metric-grid" aria-label="Resumen de riesgo">
        <MetricCard label="Evaluaciones registradas" value={metrics.total} detail="Vulnerabilidades en la matriz" icon="01" />
        <MetricCard label="Riesgos altos" value={metrics.highRisk} detail="Nivel alto o crítico" icon="!" tone="amber" />
        <MetricCard label="Incidentes abiertos" value={metrics.openIncidents} detail="En seguimiento o por atender" icon="↗" tone="blue" />
        <MetricCard label="Acciones vencidas" value={metrics.overdueActions} detail="Requieren atención prioritaria" icon="◷" tone="red" />
      </section>

      <section className="risk-workspace">
        <div className="workspace-toolbar">
          <div className="tabs" role="tablist" aria-label="Secciones de riesgo">
            <button
              className={`tab-button ${tab === 'evaluaciones' ? 'is-active' : ''}`}
              id="tab-evaluaciones"
              role="tab"
              aria-selected={tab === 'evaluaciones'}
              type="button"
              onClick={() => { setTab('evaluaciones'); setForm(null); setSearch(''); }}
            >
              Matriz de riesgo <span className="tab-count">{evaluaciones.length}</span>
            </button>
            <button
              className={`tab-button ${tab === 'incidentes' ? 'is-active' : ''}`}
              id="tab-incidentes"
              role="tab"
              aria-selected={tab === 'incidentes'}
              type="button"
              onClick={() => { setTab('incidentes'); setForm(null); setSearch(''); }}
            >
              Incidentes <span className="tab-count">{incidentes.length}</span>
            </button>
          </div>
          <div className="toolbar-filters">
            <label className="search-field">
              <span aria-hidden="true">⌕</span>
              <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Buscar cliente o riesgo" />
            </label>
            {tab === 'evaluaciones' && (
              <select className="filter-select" value={nivelFiltro} onChange={(event) => setNivelFiltro(event.target.value)} aria-label="Filtrar por nivel de riesgo">
                <option value="todos">Todos los niveles</option>
                <option value="critico">Crítico</option>
                <option value="alto">Alto</option>
                <option value="medio">Medio</option>
                <option value="bajo">Bajo</option>
              </select>
            )}
          </div>
        </div>

        {form && (
          <div className="form-panel">
            <div className="form-panel-heading">
              <div>
                <span className="eyebrow">{form === 'evaluacion' ? 'MATRIZ DE RIESGO' : 'GESTIÓN DE INCIDENTES'}</span>
                <h2>{form === 'evaluacion' ? 'Registrar vulnerabilidad' : 'Reportar incidente'}</h2>
              </div>
              <button className="icon-button" type="button" onClick={() => setForm(null)} aria-label="Cerrar formulario">×</button>
            </div>
            {form === 'evaluacion' ? (
              <form className="data-form" onSubmit={crearEvaluacion}>
                <label>Cliente<input name="cliente_nombre" required maxLength={150} placeholder="Nombre del cliente" /></label>
                <label>Sede
                  <select name="sede" defaultValue="">
                    <option value="">Sin sede específica</option>
                    {sedes.map((sede) => <option key={sede.id} value={sede.id}>{sede.nombre}</option>)}
                  </select>
                </label>
                <label className="form-span-2">Vulnerabilidad<input name="vulnerabilidad" required maxLength={180} placeholder="Ej. Perímetro sin cobertura nocturna" /></label>
                <label>Probabilidad
                  <select name="probabilidad" defaultValue="3">
                    <option value="1">1 · Rara</option><option value="2">2 · Improbable</option>
                    <option value="3">3 · Posible</option><option value="4">4 · Probable</option><option value="5">5 · Casi segura</option>
                  </select>
                </label>
                <label>Impacto
                  <select name="impacto" defaultValue="3">
                    <option value="1">1 · Insignificante</option><option value="2">2 · Menor</option>
                    <option value="3">3 · Moderado</option><option value="4">4 · Mayor</option><option value="5">5 · Catastrófico</option>
                  </select>
                </label>
                <label className="form-span-2">Descripción<textarea name="descripcion" rows={2} placeholder="Contexto y consecuencias potenciales" /></label>
                <label className="form-span-2">Plan de mitigación<textarea name="plan_mitigacion" required rows={3} placeholder="Medidas preventivas y responsables" /></label>
                <label>Próxima revisión<input name="revisado_en" type="date" /></label>
                <div className="form-actions form-span-2">
                  <button className="button button-secondary" type="button" onClick={() => setForm(null)}>Cancelar</button>
                  <button className="button button-primary" disabled={saving}>{saving ? 'Guardando…' : 'Guardar evaluación'}</button>
                </div>
              </form>
            ) : (
              <form className="data-form" onSubmit={crearIncidente}>
                <label>Cliente<input name="cliente_nombre" required maxLength={150} placeholder="Nombre del cliente" /></label>
                <label>Sede
                  <select name="sede" defaultValue="">
                    <option value="">Sin sede específica</option>
                    {sedes.map((sede) => <option key={sede.id} value={sede.id}>{sede.nombre}</option>)}
                  </select>
                </label>
                <label className="form-span-2">Título<input name="titulo" required maxLength={180} placeholder="Resumen del incidente" /></label>
                <label>Severidad
                  <select name="severidad" defaultValue="media">
                    <option value="baja">Baja</option><option value="media">Media</option>
                    <option value="alta">Alta</option><option value="critica">Crítica</option>
                  </select>
                </label>
                <label>Evaluación relacionada
                  <select name="evaluacion" defaultValue="">
                    <option value="">Sin evaluación relacionada</option>
                    {evaluaciones.map((item) => <option key={item.id} value={item.id}>{item.vulnerabilidad}</option>)}
                  </select>
                </label>
                <label>Fecha y hora<input name="ocurrido_en" type="datetime-local" defaultValue={localDateTimeValue()} required /></label>
                <label className="form-span-2">Descripción<textarea name="descripcion" required rows={3} placeholder="Qué ocurrió, dónde y qué medidas inmediatas se tomaron" /></label>
                <div className="form-actions form-span-2">
                  <button className="button button-secondary" type="button" onClick={() => setForm(null)}>Cancelar</button>
                  <button className="button button-primary" disabled={saving}>{saving ? 'Guardando…' : 'Registrar incidente'}</button>
                </div>
              </form>
            )}
          </div>
        )}

        {loading ? (
          <div className="empty-state"><span className="loading-spinner" />Cargando información de riesgo…</div>
        ) : tab === 'evaluaciones' ? (
          <div className="assessment-grid" role="tabpanel" aria-labelledby="tab-evaluaciones">
            {evaluacionesVisibles.map((item) => (
              <AssessmentCard key={item.id} item={item} sede={sedes.find((sede) => sede.id === item.sede)?.nombre} />
            ))}
            {!evaluacionesVisibles.length && <EmptyState title="Aún no hay evaluaciones" detail="Registra una vulnerabilidad para empezar a construir la matriz de riesgo." />}
          </div>
        ) : (
          <div className="incident-list" role="tabpanel" aria-labelledby="tab-incidentes">
            {incidentesVisibles.map((item) => (
              <IncidentCard
                key={item.id}
                item={item}
                expanded={expandedIncident === item.id}
                actionFormOpen={actionFormIncident === item.id}
                busy={saving}
                onToggle={() => setExpandedIncident(expandedIncident === item.id ? null : item.id)}
                onTransition={() => actualizarIncidente(item.id, item.estado)}
                onOpenActionForm={() => setActionFormIncident(actionFormIncident === item.id ? null : item.id)}
                onCreateAction={(event) => crearAccion(event, item.id)}
                onStartAction={(id) => void ejecutar(() => riskApi.iniciarAccion(id))}
                onCompleteAction={(id) => void ejecutar(() => riskApi.completarAccion(id))}
              />
            ))}
            {!incidentesVisibles.length && <EmptyState title="Sin incidentes registrados" detail="Cuando se reporte un incidente, podrás seguir aquí su atención y acciones correctivas." />}
          </div>
        )}
      </section>
      <footer className="risk-footnote">Los niveles se calculan en el servidor con una matriz de probabilidad × impacto (escala 1–5).</footer>
    </main>
  );
}

function MetricCard({ label, value, detail, icon, tone = 'default' }: {
  label: string; value: number; detail: string; icon: string; tone?: string;
}) {
  return (
    <article className={`metric-card metric-${tone}`}>
      <div className="metric-top"><span>{label}</span><span className="metric-icon" aria-hidden="true">{icon}</span></div>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}

function AssessmentCard({ item, sede }: { item: EvaluacionRiesgo; sede?: string }) {
  return (
    <article className="assessment-card">
      <div className="assessment-card-top">
        <span className={`risk-pill risk-${item.nivel}`}>{nivelLabels[item.nivel]}</span>
        <span className="assessment-score">{item.puntaje}<small> / 25</small></span>
      </div>
      <div className="assessment-client">{item.cliente_nombre}{sede && <span> · {sede}</span>}</div>
      <h3>{item.vulnerabilidad}</h3>
      {item.descripcion && <p className="assessment-description">{item.descripcion}</p>}
      <div className="risk-scale">
        <div><span>Probabilidad</span><strong>{item.probabilidad}<small> / 5</small></strong></div>
        <div><span>Impacto</span><strong>{item.impacto}<small> / 5</small></strong></div>
      </div>
      <div className="mitigation-box"><span>PLAN DE MITIGACIÓN</span><p>{item.plan_mitigacion}</p></div>
      <div className="assessment-card-bottom">
        <span className={`status-label status-${item.estado}`}>{item.estado_display}</span>
        <span>Actualizado {formatDate(item.actualizado_en.slice(0, 10))}</span>
      </div>
    </article>
  );
}

function IncidentCard({
  item, expanded, actionFormOpen, busy, onToggle, onTransition, onOpenActionForm,
  onCreateAction, onStartAction, onCompleteAction,
}: {
  item: IncidenteRiesgo;
  expanded: boolean;
  actionFormOpen: boolean;
  busy: boolean;
  onToggle: () => void;
  onTransition: () => void;
  onOpenActionForm: () => void;
  onCreateAction: (event: FormEvent<HTMLFormElement>) => void;
  onStartAction: (id: number) => void;
  onCompleteAction: (id: number) => void;
}) {
  const nextAction: Partial<Record<EstadoIncidente, string>> = {
    abierto: 'Iniciar seguimiento',
    en_seguimiento: 'Marcar resuelto',
    resuelto: 'Cerrar incidente',
  };
  const openActions = item.acciones.filter((action) => action.estado !== 'completada').length;
  return (
    <article className={`incident-card ${expanded ? 'incident-expanded' : ''}`}>
      <button className="incident-main" type="button" onClick={onToggle} aria-expanded={expanded}>
        <span className={`severity-mark severity-${item.severidad}`} />
        <span className="incident-primary">
          <span className="incident-meta">{item.cliente_nombre} {item.sede_nombre && `· ${item.sede_nombre}`}</span>
          <strong>{item.titulo}</strong>
          <span className="incident-description">{item.descripcion}</span>
        </span>
        <span className={`severity-label severity-text-${item.severidad}`}>{severidadLabels[item.severidad]}</span>
        <span className={`status-label status-${item.estado}`}>{estadoLabels[item.estado]}</span>
        <span className="incident-date">{new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(item.ocurrido_en))}</span>
        <span className="expand-chevron" aria-hidden="true">{expanded ? '−' : '+'}</span>
      </button>
      {expanded && (
        <div className="incident-details">
          <div className="incident-detail-summary">
            <div><span>Reportado por</span><strong>{item.reportado_por_nombre ?? 'Usuario del tenant'}</strong></div>
            <div><span>Acciones abiertas</span><strong>{openActions}</strong></div>
            <div><span>Fecha del incidente</span><strong>{new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(item.ocurrido_en))}</strong></div>
            <div className="incident-controls">
              {nextAction[item.estado] && <button className="button button-small button-primary" type="button" disabled={busy} onClick={onTransition}>{nextAction[item.estado]}</button>}
              {item.estado !== 'resuelto' && item.estado !== 'cerrado' && <button className="button button-small button-secondary" type="button" onClick={onOpenActionForm}>＋ Acción correctiva</button>}
            </div>
          </div>
          <div className="action-list-heading"><strong>Seguimiento de acciones</strong><span>{item.acciones.length} acciones</span></div>
          {item.acciones.map((action) => (
            <div className="action-row" key={action.id}>
              <span className={`action-status-dot action-${action.estado}`} />
              <div className="action-copy"><strong>{action.titulo}</strong><span>{action.descripcion || 'Sin detalles adicionales'} · vence {formatDate(action.fecha_limite)}</span></div>
              <span className={`action-state action-state-${action.estado}`}>{accionEstadoLabels[action.estado]}</span>
              {action.estado === 'pendiente' && <button className="text-action" type="button" onClick={() => onStartAction(action.id)}>Iniciar</button>}
              {action.estado !== 'completada' && <button className="text-action" type="button" disabled={busy} onClick={() => onCompleteAction(action.id)}>Completar</button>}
            </div>
          ))}
          {!item.acciones.length && <p className="no-actions">Todavía no hay acciones correctivas para este incidente.</p>}
          {actionFormOpen && (
            <form className="action-form" onSubmit={onCreateAction}>
              <label>Tarea<input name="titulo" required maxLength={180} placeholder="Ej. Reforzar control de accesos" /></label>
              <label>Fecha límite<input name="fecha_limite" type="date" /></label>
              <label className="action-form-description">Detalle<input name="descripcion" placeholder="Descripción breve de la acción" /></label>
              <button className="button button-small button-primary" disabled={busy}>{busy ? 'Guardando…' : 'Añadir acción'}</button>
            </form>
          )}
        </div>
      )}
    </article>
  );
}

function EmptyState({ title, detail }: { title: string; detail: string }) {
  return <div className="empty-state empty-state-card"><span className="empty-state-icon" aria-hidden="true">◇</span><strong>{title}</strong><p>{detail}</p></div>;
}
