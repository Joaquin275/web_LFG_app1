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
