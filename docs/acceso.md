# Acceso y onboarding

Este documento describe el flujo inicial de autenticación y alta de tenant
disponible desde la Fase 8.

## Inicio local

1. Copia `.env.example` a `.env` si aún no existe y ejecuta
   `docker compose up --build`.
2. Abre `http://localhost:5173/` y elige **Registrar empresa**.
3. Define nombre e identificador de empresa, y las credenciales del primer
   administrador.
4. El alta crea de forma atómica el tenant, usuario con rol `admin_empresa`
   y los flags de los módulos ya implementados. La sesión inicia al terminar.
5. Para las próximas sesiones, usa el identificador de tenant, usuario y
   contraseña en **Iniciar sesión**.

No se crean cuentas ni contraseñas de demostración. Las contraseñas nuevas
deben cumplir la política de Django, incluida una longitud mínima de 12
caracteres. El alta pública limita solicitudes por dirección IP; el login
tiene una cuota más estricta. El inicio devuelve un access token y un refresh
token JWT; el frontend renueva el access token y vuelve al login si la
renovación falla.

## API

| Método | Ruta | Propósito |
|---|---|---|
| POST | `/api/auth/onboarding/` | Crear tenant, primer administrador y módulos predeterminados |
| POST | `/api/auth/login/` | Autenticar usuario dentro del identificador de tenant |
| POST | `/api/auth/refresh/` | Renovar el access token |
| GET | `/health/` | Verificar que Django y la conexión de base de datos responden |

El frontend almacena access/refresh token y el tenant activo en el navegador.
Para las llamadas de API protegidas envía `Authorization: Bearer <token>` y
`X-Tenant-Id: <id>`. El permiso común rechaza usuarios cuyo tenant no coincide
con el encabezado y aplica una lista de acciones permitidas por rol. Las
consultas y relaciones de sedes respetan la asignación del usuario cuando no
tiene acceso global al tenant. El encabezado no sustituye la autenticación.

El RBAC inicial permite administración de catálogos y configuración a
`admin_empresa`/`supervisor`; a `recepcionista` le permite la operación de
visitas, invitados e invitaciones; a `operador_central` la lectura operativa
y atención/cierre de alarmas y pánicos; y a `guardia` el acceso a visitas,
GPS, checkpoints y servicios que tenga asignados. Las sedes asignadas filtran
consultas y relaciones. `cliente_final` aún no tiene portal/permisos de
cliente implementados y se deniega por defecto. Estos permisos son una matriz
inicial del producto, no sustituyen una futura consola de permisos
personalizables ni pruebas externas de autorización.

## Entorno local y producción

El Compose de desarrollo publica la interfaz y el backend solo en
`127.0.0.1`; PostgreSQL no publica un puerto al host. Usa una contraseña de
desarrollo única en `.env` y no la compartas. `.gitignore` excluye `.env`.
El entorno local inicia `runserver`, `DEBUG=True` y Vite, por lo que no debe
exponerse en redes públicas. La configuración `config.settings.prod` requiere
una clave secreta robusta, dominios permitidos y configuración de base de
datos explícita; además activa HTTPS/HSTS y `DEBUG=False`. El despliegue real
aún requiere un proxy TLS confiable y un servidor WSGI/ASGI de producción.

## Administración y límites

El superusuario de Django se provisiona de forma manual con
`python manage.py createsuperuser` dentro del servicio backend. La interfaz
de administración se sirve en `/admin/`; los usuarios operativos adicionales
y sus asignaciones a sedes se gestionan allí.

El identificador por subdominio está soportado por el middleware, pero la
configuración DNS/TLS y un proxy de producción no forman parte de Compose.
El onboarding público requiere límites adicionales, verificación de correo,
protección contra abuso, aceptación contractual y un proceso de baja antes de
abrirse al Internet público. Las cuotas por plan, facturación y selección
configurable de módulos siguen pendientes.

## Pendiente antes de producción

- Añadir e instalar políticas RLS reales en PostgreSQL y pruebas de aislamiento
  que las ejerciten (el filtrado actual es de aplicación).
- Configurar `config.settings.prod`, secretos, dominios, HTTPS/proxy,
  almacenamiento de estáticos y archivos subidos, copias/restauración y
  monitoreo. Esta configuración falla al iniciar si faltan secretos o hosts.
- Revisar permisos por rol para cada operación, no solo pertenencia al tenant.
- Añadir verificación de correo y controles antifraude para el onboarding.
- Implementar gestión de invitaciones de usuarios, recuperación de contraseña
  y revocación/rotación de refresh tokens.
