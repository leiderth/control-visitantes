import uuid

from django.db import models

from apps.tenants.mixins import TenantScopedModel


class Sede(TenantScopedModel):
    """Una ubicación física del cliente final de una empresa de seguridad."""

    nombre = models.CharField(max_length=150)
    direccion = models.CharField(max_length=255, blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Host(TenantScopedModel):
    """Anfitrión interno que recibe visitantes en una sede."""

    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name="hosts")
    nombre_completo = models.CharField(max_length=150)
    email = models.EmailField()
    telefono = models.CharField(max_length=30, blank=True)
    notificar_por = models.JSONField(
        default=list,
        help_text="Canales activos: ['push', 'sms', 'email']",
    )

    def __str__(self):
        return f"{self.nombre_completo} ({self.sede})"


class Visitor(TenantScopedModel):
    """Persona que visita una o más sedes. Es global al tenant (no por sede)."""

    class Categoria(models.TextChoices):
        NORMAL = "normal", "Visitante normal"
        CONTRATISTA = "contratista", "Contratista"
        PROVEEDOR = "proveedor", "Proveedor"
        MENSAJERIA = "mensajeria", "Mensajería / delivery"
        VIP = "vip", "VIP"
        TEMPORAL = "temporal", "Personal temporal"

    documento_tipo = models.CharField(max_length=10, default="CC")
    documento_numero = models.CharField(max_length=30, db_index=True)
    nombre_completo = models.CharField(max_length=150)
    empresa = models.CharField(max_length=150, blank=True)
    categoria = models.CharField(
        max_length=20, choices=Categoria.choices, default=Categoria.NORMAL
    )
    foto = models.ImageField(upload_to="visitantes/fotos/", blank=True, null=True)
    documento_escaneado = models.FileField(
        upload_to="visitantes/documentos/", blank=True, null=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "documento_tipo", "documento_numero"],
                name="unique_documento_por_tenant",
            )
        ]

    def __str__(self):
        return f"{self.nombre_completo} ({self.documento_numero})"


class WatchlistEntry(TenantScopedModel):
    """Lista negra / lista de vigilancia, compartida entre todas las sedes del tenant."""

    class Tipo(models.TextChoices):
        BLACKLIST = "blacklist", "Lista negra"
        WATCHLIST = "watchlist", "Lista de vigilancia"

    documento_numero = models.CharField(max_length=30, db_index=True)
    nombre_completo = models.CharField(max_length=150)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    motivo = models.TextField()
    registrado_por = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True
    )

    def __str__(self):
        return f"[{self.tipo}] {self.nombre_completo}"


class Visit(TenantScopedModel):
    """Un ingreso concreto: check-in / check-out de un visitante a una sede."""

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente de aprobación"
        AUTORIZADA = "autorizada", "Autorizada"
        EN_CURSO = "en_curso", "En curso (check-in hecho)"
        FINALIZADA = "finalizada", "Finalizada (check-out hecho)"
        EXCEDIDA = "excedida", "Tiempo excedido"
        RECHAZADA = "rechazada", "Rechazada"

    codigo_qr = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name="visitas")
    visitante = models.ForeignKey(
        Visitor, on_delete=models.CASCADE, related_name="visitas"
    )
    anfitrion = models.ForeignKey(
        Host, on_delete=models.SET_NULL, null=True, related_name="visitas"
    )
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.PENDIENTE
    )
    hora_autorizada_desde = models.DateTimeField()
    hora_autorizada_hasta = models.DateTimeField()
    check_in_at = models.DateTimeField(null=True, blank=True)
    check_out_at = models.DateTimeField(null=True, blank=True)
    documento_firmado = models.FileField(
        upload_to="visitantes/firmas/", blank=True, null=True
    )
    firmado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-hora_autorizada_desde"]
        indexes = [
            models.Index(fields=["tenant", "sede", "estado"]),
        ]

    def __str__(self):
        return f"{self.visitante} → {self.sede} ({self.estado})"


class Invitacion(TenantScopedModel):
    """
    Pre-registro creado por un anfitrión. Se envía como link/QR
    (email o WhatsApp) y el visitante la confirma sin necesidad de login.
    Al confirmarse (o al llegar) genera la Visit correspondiente.
    """

    class Estado(models.TextChoices):
        ENVIADA = "enviada", "Enviada"
        CONFIRMADA = "confirmada", "Confirmada por el visitante"
        USADA = "usada", "Usada (visita creada)"
        EXPIRADA = "expirada", "Expirada"

    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name="invitaciones")
    anfitrion = models.ForeignKey(Host, on_delete=models.CASCADE, related_name="invitaciones")
    visitante_nombre = models.CharField(max_length=150)
    visitante_documento = models.CharField(max_length=30, blank=True)
    visitante_email = models.EmailField(blank=True)
    visitante_telefono = models.CharField(max_length=30, blank=True)
    requiere_aprobacion_manual = models.BooleanField(default=False)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ENVIADA)
    valida_desde = models.DateTimeField()
    valida_hasta = models.DateTimeField()
    visita_generada = models.ForeignKey(
        Visit, on_delete=models.SET_NULL, null=True, blank=True, related_name="invitacion_origen"
    )

    def __str__(self):
        return f"Invitación a {self.visitante_nombre} ({self.estado})"


class DocumentoLegal(TenantScopedModel):
    """Plantilla de documento (NDA, política de seguridad, exención) a firmar en el ingreso."""

    nombre = models.CharField(max_length=150)
    contenido = models.TextField(help_text="Texto o referencia a plantilla del documento")
    obligatorio_para = models.JSONField(
        default=list,
        help_text="Categorías de visitante que deben firmarlo, ej: ['contratista', 'proveedor']",
    )
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class FirmaDocumento(TenantScopedModel):
    """Registro de la firma electrónica de un DocumentoLegal en una Visit concreta."""

    visita = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name="firmas")
    documento = models.ForeignKey(DocumentoLegal, on_delete=models.PROTECT, related_name="firmas")
    firma_imagen = models.ImageField(upload_to="visitantes/firmas/trazo/")
    ip_origen = models.GenericIPAddressField(null=True, blank=True)
    firmado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["visita", "documento"], name="unique_firma_por_documento_y_visita"
            )
        ]

    def __str__(self):
        return f"Firma de {self.documento} en {self.visita}"
