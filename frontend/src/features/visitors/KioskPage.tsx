import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Field } from '@/components/ui/Field';
import { visitorsApi } from './api';

/**
 * Pantalla de tablet en recepción: interfaz táctil simplificada de un solo
 * paso por pantalla, pensada para que la use el visitante sin asistencia.
 * A diferencia de VisitorsPage (panel de recepcionista), aquí no hay tablas
 * ni filtros — solo el flujo lineal: documento → foto → confirmar.
 */
export function KioskPage() {
  const [paso, setPaso] = useState<'documento' | 'foto' | 'listo'>('documento');
  const [documento, setDocumento] = useState('');
  const [nombre, setNombre] = useState('');

  const confirmar = async () => {
    await visitorsApi.crearVisitante({
      documento_numero: documento,
      nombre_completo: nombre,
    });
    setPaso('listo');
  };

  if (paso === 'listo') {
    return (
      <div className="flex h-screen flex-col items-center justify-center text-center">
        <h1 className="text-3xl font-semibold">¡Bienvenido, {nombre}!</h1>
        <p className="text-muted-foreground">
          Tu anfitrión fue notificado. Por favor toma asiento mientras te recibe.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto flex h-screen max-w-md flex-col justify-center gap-6 px-6">
      <h1 className="text-center text-2xl font-semibold">Registro de visitante</h1>

      {paso === 'documento' && (
        <>
          <Field label="Número de documento">
            <input
              className="w-full rounded border p-4 text-lg"
              value={documento}
              onChange={(e) => setDocumento(e.target.value)}
              inputMode="numeric"
              autoFocus
            />
          </Field>
          <Field label="Nombre completo">
            <input
              className="w-full rounded border p-4 text-lg"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
            />
          </Field>
          <Button size="lg" onClick={() => setPaso('foto')} disabled={!documento || !nombre}>
            Continuar
          </Button>
        </>
      )}

      {paso === 'foto' && (
        <>
          {/* TODO (Fase 4): capturar foto real vía getUserMedia y subir como
              multipart antes de crear el Visitor. Por ahora se omite para no
              bloquear el flujo de datos/backend de esta entrega. */}
          <p className="text-center text-muted-foreground">
            Por favor mira a la cámara para tu foto de ingreso.
          </p>
          <Button size="lg" onClick={confirmar}>
            Confirmar ingreso
          </Button>
        </>
      )}
    </div>
  );
}
