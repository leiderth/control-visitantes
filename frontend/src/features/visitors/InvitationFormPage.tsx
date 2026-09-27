import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Field } from '@/components/ui/Field';
import { invitationsApi } from './api';

/**
 * Formulario que usa el anfitrión (o recepción, en su nombre) para crear
 * una pre-invitación. Al guardar, el backend genera el `token` con el que
 * se arma el link/QR a enviar por email o WhatsApp — ese envío en sí
 * (Fase 4) queda fuera de esta pantalla.
 */
export function InvitationFormPage() {
  const [enviado, setEnviado] = useState(false);
  const [form, setForm] = useState({
    sede: '',
    anfitrion: '',
    visitante_nombre: '',
    visitante_email: '',
    valida_desde: '',
    valida_hasta: '',
  });

  const set = (campo: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [campo]: e.target.value }));

  const guardar = async () => {
    await invitationsApi.crear(form);
    setEnviado(true);
  };

  if (enviado) {
    return <p>Invitación creada. El link/QR se genera a partir de su token único.</p>;
  }

  return (
    <div className="max-w-md space-y-4">
      <h1 className="text-xl font-semibold">Nueva invitación</h1>
      <Field label="Nombre del visitante">
        <input className="w-full rounded border p-2" value={form.visitante_nombre} onChange={set('visitante_nombre')} />
      </Field>
      <Field label="Email del visitante">
        <input className="w-full rounded border p-2" value={form.visitante_email} onChange={set('visitante_email')} />
      </Field>
      <Field label="Válida desde">
        <input type="datetime-local" className="w-full rounded border p-2" value={form.valida_desde} onChange={set('valida_desde')} />
      </Field>
      <Field label="Válida hasta">
        <input type="datetime-local" className="w-full rounded border p-2" value={form.valida_hasta} onChange={set('valida_hasta')} />
      </Field>
      <Button onClick={guardar}>Crear invitación</Button>
    </div>
  );
}
