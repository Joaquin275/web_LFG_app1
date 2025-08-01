from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.core.validators import EmailValidator
from decimal import Decimal
from django.utils import timezone

# -------------------- MODELO CLIENTE --------------------
class Cliente(models.Model):
    Nombre_Completo = models.CharField(max_length=100)
    Creacion_cuenta = models.DateTimeField(auto_now_add=True)
    importante = models.BooleanField(default=False)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    empresa = models.ForeignKey('Empresa', on_delete=models.CASCADE, null=True, blank=True)
    es_particular = models.BooleanField(default=False)  # Nuevo campo
    direccion_particular = models.TextField(blank=True, null=True)  # Nuevo campo
    celular = models.CharField(max_length=20, blank=True, null=True)
    dni = models.CharField("NIE/DNI", max_length=30, blank=True, null=True)
    correo = models.EmailField("Correo electrónico", validators=[EmailValidator()], null=True, blank=True)

    def __str__(self):
        if self.es_particular:
            return f"{self.Nombre_Completo} - Particular"
        else:
            return f"{self.Nombre_Completo} - {self.empresa.nombre if self.empresa else 'Sin empresa'}"

# -------------------- MODELO EMPRESA --------------------
class Empresa(models.Model):
    codigo = models.CharField(max_length=50, unique=True)  # nuevo campo código, único
    nombre = models.CharField(max_length=100)
    direccion = models.TextField("Dirección de entrega", blank=True, null=True)
    cif = models.CharField("CIF", max_length=20, unique=True)

    def __str__(self):
        return f"{self.nombre} - {self.direccion}"

# -------------------- MODELO PLATO --------------------
class Plato(models.Model):
    codigo = models.CharField(max_length=50, unique=True)  # nuevo campo código, único
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    imagen = models.ImageField(upload_to='platos/', blank=True, null=True)

    kilogramos = models.DecimalField(max_digits=5, decimal_places=0, default=0.5)

    GRUPOS_CHOICES = [
        ('CARNE', 'Carnes'),
        ('TORTILLAS', 'Tortillas'),
        ('PLATO DE CUCHARA', 'Platos de cucharas'),
        ('ENSALADA Y VERDURA', 'Ensalada y Verduras'),
        ('PESCADO', 'Pescados'),
        ('ARROCES Y PASTAS', 'Arroces y pastas'),
    ]
    grupo = models.CharField(max_length=20, choices=GRUPOS_CHOICES, default='OTROS')

    ingredientes = models.TextField(blank=True, help_text="Lista de ingredientes del plato")
    alergenos = models.TextField(blank=True, help_text="Alergenos presentes en el plato")
    vida_util = models.CharField(max_length=100, default="5 días")

    precio_sin_iva = models.DecimalField(max_digits=6, decimal_places=2, default=5.99)

    calorias = models.IntegerField(help_text="Cantidad de calorías", null=True, blank=True)
    proteinas = models.DecimalField(max_digits=5, decimal_places=0, null=True, blank=True)
    grasa = models.DecimalField(max_digits=5, decimal_places=0, null=True, blank=True)
    carbohidratos = models.DecimalField(max_digits=5, decimal_places=0, null=True, blank=True)
    sodio = models.DecimalField(max_digits=6, decimal_places=0, null=True, blank=True)

    ESTADO_CHOICES = [
        ('NUEVO', 'Nuevo'),
         ('PLATO DE LA SEMANA', 'Plato de la semana'),
        ('DESCUENTO', 'Descuento'),
        ('COMUN', 'Común'),
    ]
    estado = models.CharField(max_length=30, choices=ESTADO_CHOICES, default='NUEVO')

    def save(self, *args, **kwargs):
        iva = Decimal('1.10')  # IVA como Decimal
        self.precio_sin_iva = (self.precio / iva).quantize(Decimal('0.01'))  # redondeo a 2 decimales
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class DisponibilidadPlato(models.Model):
    DIAS_SEMANA = [
        ('LUN', 'Lunes'),
        ('MAR', 'Martes'),
        ('MIE', 'Miércoles'),
        ('JUE', 'Jueves'),
        ('VIE', 'Viernes'),
        ('SAB', 'Sábado'),
    ]

    plato = models.ForeignKey(Plato, on_delete=models.CASCADE)
    dia = models.CharField(max_length=3, choices=DIAS_SEMANA, default='LUN')

    class Meta:
        unique_together = ('plato', 'dia')

    def __str__(self):
        return f"{self.plato.nombre} disponible el {self.get_dia_display()}"

class CarritoItem(models.Model):
    DIAS_SEMANA = [
        ('LUN', 'Lunes'),
        ('MAR', 'Martes'),
        ('MIE', 'Miércoles'),
        ('JUE', 'Jueves'),
        ('VIE', 'Viernes'),
        ('SAB', 'Sábado'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    plato = models.ForeignKey(Plato, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    dia_semana = models.CharField(max_length=3, choices=DIAS_SEMANA, default='LUN')
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    def subtotal(self):
        return self.cantidad * self.plato.precio

    def __str__(self):
        return f"{self.cantidad} x {self.plato.nombre} - {self.usuario.username} ({self.get_dia_semana_display()})"



# -------------------- RECIBO --------------------
class Recibo(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    empresa = models.ForeignKey('Empresa', null=True, blank=True, on_delete=models.SET_NULL)
    total = models.DecimalField(max_digits=8, decimal_places=2)
    fecha_compra = models.DateTimeField(default=timezone.now)

    # NUEVOS CAMPOS
    pagado = models.BooleanField(default=False)
    fecha_pago = models.DateTimeField(null=True, blank=True)
    referencia_pago = models.CharField(max_length=100, blank=True, null=True)
    metodo_pago = models.CharField(max_length=30, blank=True, null=True)
    estado_pago = models.CharField(max_length=30, default='pendiente', choices=[
        ('pendiente', 'Pendiente'),
        ('completado', 'Completado'),
        ('fallido', 'Fallido'),
    ])
    url_iframe = models.URLField(blank=True, null=True, help_text="URL del iframe de Paycomet")

    def __str__(self):
        return f"Recibo #{self.id} - {self.usuario.username}"

# -------------------- DETALLE DE RECIBO --------------------
class ReciboItem(models.Model):
    recibo = models.ForeignKey(Recibo, related_name='items', on_delete=models.CASCADE)
    plato = models.ForeignKey(Plato, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=8, decimal_places=2)

    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.cantidad} x {self.plato.nombre}"

# models.py

class PedidoHistorico(models.Model):
    DIAS_SEMANA = CarritoItem.DIAS_SEMANA  # reutilizamos los mismos días

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    plato = models.ForeignKey(Plato, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    dia_semana = models.CharField(max_length=3, choices=DIAS_SEMANA)
    fecha_emision = models.DateField(auto_now_add=True)  # fecha del pedido

    def __str__(self):
        return f"{self.cantidad} x {self.plato.nombre} - {self.usuario.username} ({self.get_dia_semana_display()}) {self.fecha_emision}"

# -------------------- MODELOS DE PRODUCCIÓN --------------------

class Produccion(models.Model):
    """Modelo para gestionar la producción de platos"""
    ESTADO_CHOICES = [
        ('PLANIFICADA', 'Planificada'),
        ('EN_PROCESO', 'En Proceso'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    plato = models.ForeignKey(Plato, on_delete=models.CASCADE, related_name='producciones')
    cantidad_planificada = models.PositiveIntegerField(help_text="Cantidad planificada a producir")
    cantidad_producida = models.PositiveIntegerField(default=0, help_text="Cantidad realmente producida")
    fecha_planificada = models.DateField(help_text="Fecha planificada de producción")
    fecha_inicio = models.DateTimeField(null=True, blank=True, help_text="Fecha y hora de inicio de producción")
    fecha_completada = models.DateTimeField(null=True, blank=True, help_text="Fecha y hora de finalización")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PLANIFICADA')
    
    # Costos de producción
    costo_ingredientes = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="Costo total de ingredientes")
    costo_mano_obra = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="Costo de mano de obra")
    otros_costos = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="Otros costos de producción")
    
    # Responsable
    responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, help_text="Responsable de la producción")
    
    # Notas
    notas = models.TextField(blank=True, help_text="Notas adicionales sobre la producción")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_planificada', '-created_at']
        verbose_name = "Producción"
        verbose_name_plural = "Producciones"
    
    def __str__(self):
        return f"Producción {self.plato.nombre} - {self.fecha_planificada} ({self.get_estado_display()})"
    
    @property
    def costo_total(self):
        return self.costo_ingredientes + self.costo_mano_obra + self.otros_costos
    
    @property
    def porcentaje_completado(self):
        if self.cantidad_planificada > 0:
            return min((self.cantidad_producida / self.cantidad_planificada) * 100, 100)
        return 0
    
    @property
    def eficiencia(self):
        """Calcula la eficiencia de producción basada en tiempo planificado vs real"""
        if self.fecha_inicio and self.fecha_completada and self.estado == 'COMPLETADA':
            tiempo_real = (self.fecha_completada - self.fecha_inicio).total_seconds() / 3600  # horas
            # Asumimos 8 horas como tiempo estándar por lote
            tiempo_estandar = 8
            return min((tiempo_estandar / tiempo_real) * 100, 100) if tiempo_real > 0 else 0
        return 0

class Inventario(models.Model):
    """Modelo para gestionar el inventario de platos producidos"""
    plato = models.ForeignKey(Plato, on_delete=models.CASCADE, related_name='inventario')
    cantidad_disponible = models.PositiveIntegerField(default=0, help_text="Cantidad disponible en inventario")
    cantidad_reservada = models.PositiveIntegerField(default=0, help_text="Cantidad reservada para pedidos")
    fecha_produccion = models.DateField(help_text="Fecha de producción del lote")
    fecha_vencimiento = models.DateField(help_text="Fecha de vencimiento")
    ubicacion = models.CharField(max_length=100, blank=True, help_text="Ubicación física del inventario")
    
    # Lote de producción relacionado
    produccion = models.ForeignKey(Produccion, on_delete=models.CASCADE, related_name='inventario_generado')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['fecha_vencimiento', 'fecha_produccion']
        verbose_name = "Inventario"
        verbose_name_plural = "Inventarios"
    
    def __str__(self):
        return f"{self.plato.nombre} - {self.cantidad_disponible} unidades (Vence: {self.fecha_vencimiento})"
    
    @property
    def cantidad_total(self):
        return self.cantidad_disponible + self.cantidad_reservada
    
    @property
    def dias_hasta_vencimiento(self):
        from datetime import date
        return (self.fecha_vencimiento - date.today()).days
    
    @property
    def estado_frescura(self):
        dias = self.dias_hasta_vencimiento
        if dias < 0:
            return 'VENCIDO'
        elif dias <= 1:
            return 'CRITICO'
        elif dias <= 2:
            return 'ADVERTENCIA'
        else:
            return 'FRESCO'

class MovimientoInventario(models.Model):
    """Modelo para registrar movimientos de inventario"""
    TIPO_MOVIMIENTO_CHOICES = [
        ('ENTRADA', 'Entrada (Producción)'),
        ('SALIDA', 'Salida (Venta)'),
        ('AJUSTE', 'Ajuste de Inventario'),
        ('MERMA', 'Merma/Desperdicio'),
    ]
    
    inventario = models.ForeignKey(Inventario, on_delete=models.CASCADE, related_name='movimientos')
    tipo_movimiento = models.CharField(max_length=20, choices=TIPO_MOVIMIENTO_CHOICES)
    cantidad = models.IntegerField(help_text="Cantidad (positiva para entrada, negativa para salida)")
    motivo = models.CharField(max_length=200, help_text="Motivo del movimiento")
    
    # Referencias opcionales
    recibo = models.ForeignKey(Recibo, on_delete=models.SET_NULL, null=True, blank=True, help_text="Recibo relacionado (si es venta)")
    usuario_responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha_movimiento']
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
    
    def __str__(self):
        signo = "+" if self.cantidad >= 0 else ""
        return f"{self.inventario.plato.nombre} - {signo}{self.cantidad} ({self.get_tipo_movimiento_display()})"
