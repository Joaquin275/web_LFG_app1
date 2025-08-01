from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from django.urls import path
from django.shortcuts import render
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta, date
import pandas as pd

from .models import (
    Cliente, Empresa, Plato, DisponibilidadPlato, CarritoItem, 
    Recibo, ReciboItem, PedidoHistorico, Produccion, Inventario, MovimientoInventario
)
from .forms import DisponibilidadPlatoForm, CarritoItemForm

# ==================== VISTAS PERSONALIZADAS ====================

def dashboard_view(request):
    """Vista personalizada para el dashboard principal"""
    return render(request, 'admin/dashboard.html')

def production_dashboard_view(request):
    """Vista personalizada para el dashboard de producción"""
    context = {
        'producciones_activas': Produccion.objects.filter(estado__in=['PLANIFICADA', 'EN_PROCESO']).count(),
        'producciones_completadas_hoy': Produccion.objects.filter(
            estado='COMPLETADA', 
            fecha_completada__date=date.today()
        ).count(),
        'inventario_critico': Inventario.objects.filter(
            Q(cantidad_disponible__lte=10) | 
            Q(fecha_vencimiento__lte=date.today() + timedelta(days=2))
        ).count(),
    }
    return render(request, 'admin/production_dashboard.html', context)

# ==================== ADMINISTRACIÓN DE MODELOS BÁSICOS ====================

class ClienteAdmin(admin.ModelAdmin):
    list_display = ('Nombre_Completo', 'usuario', 'empresa', 'es_particular', 'celular', 'correo')
    list_filter = ('es_particular', 'empresa', 'importante')
    search_fields = ('Nombre_Completo', 'usuario__username', 'celular', 'dni', 'correo')
    readonly_fields = ('Creacion_cuenta',)
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('Nombre_Completo', 'usuario', 'celular', 'dni', 'correo')
        }),
        ('Tipo de Cliente', {
            'fields': ('es_particular', 'empresa', 'direccion_particular')
        }),
        ('Configuración', {
            'fields': ('importante', 'Creacion_cuenta'),
            'classes': ('collapse',)
        }),
    )

class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'cif', 'direccion')
    search_fields = ('codigo', 'nombre', 'cif')
    ordering = ('codigo',)

class PlatoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'grupo', 'precio', 'precio_sin_iva', 'estado', 'imagen_preview')
    list_filter = ('grupo', 'estado')
    search_fields = ('codigo', 'nombre', 'ingredientes', 'alergenos')
    readonly_fields = ('precio_sin_iva', 'imagen_preview')
    list_per_page = 20
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion', 'grupo', 'estado')
        }),
        ('Imagen', {
            'fields': ('imagen', 'imagen_preview'),
            'description': 'Sube una imagen para el plato. Se mostrará en el sitio web.'
        }),
        ('Precios', {
            'fields': ('precio', 'precio_sin_iva')
        }),
        ('Detalles del Producto', {
            'fields': ('kilogramos', 'ingredientes', 'alergenos', 'vida_util'),
            'classes': ('collapse',)
        }),
        ('Información Nutricional', {
            'fields': ('calorias', 'proteinas', 'grasa', 'carbohidratos', 'sodio'),
            'classes': ('collapse',)
        }),
    )
    
    def imagen_preview(self, obj):
        if obj.imagen:
            return format_html(
                '<img src="{}" style="width: 100px; height: 70px; object-fit: cover; border-radius: 5px;" />',
                obj.imagen.url
            )
        return "Sin imagen"
    imagen_preview.short_description = "Vista previa"

class DisponibilidadPlatoAdmin(admin.ModelAdmin):
    form = DisponibilidadPlatoForm
    list_display = ('plato', 'dia_display', 'plato_grupo', 'plato_precio')
    list_filter = ('dia', 'plato__grupo', 'plato__estado')
    search_fields = ('plato__nombre', 'plato__codigo')
    list_per_page = 50
    
    # Permitir edición inline más fácil
    list_editable = ()  # Quitamos edición inline para evitar problemas
    
    def dia_display(self, obj):
        return obj.get_dia_display()
    dia_display.short_description = 'Día'
    
    def plato_grupo(self, obj):
        return obj.plato.get_grupo_display()
    plato_grupo.short_description = 'Grupo'
    
    def plato_precio(self, obj):
        return f"€{obj.plato.precio}"
    plato_precio.short_description = 'Precio'
    
    # Mejorar el formulario de cambio
    fieldsets = (
        (None, {
            'fields': ('plato', 'dia'),
            'description': 'Selecciona el plato y el día de la semana en que estará disponible.'
        }),
    )

class CarritoItemAdmin(admin.ModelAdmin):
    form = CarritoItemForm
    list_display = ('usuario', 'plato', 'cantidad', 'dia_semana', 'fecha_agregado')
    list_filter = ('dia_semana', 'fecha_agregado')
    search_fields = ('usuario__username', 'plato__nombre')

class ReciboAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'empresa', 'total', 'pagado', 'estado_pago', 'fecha_compra')
    list_filter = ('pagado', 'estado_pago', 'fecha_compra')
    search_fields = ('usuario__username', 'empresa__nombre')
    readonly_fields = ('fecha_compra',)

class ReciboItemAdmin(admin.ModelAdmin):
    list_display = ('recibo', 'plato', 'cantidad', 'precio_unitario', 'subtotal_display')
    search_fields = ('recibo__id', 'plato__nombre')
    
    def subtotal_display(self, obj):
        return f"€{obj.subtotal():.2f}"
    subtotal_display.short_description = 'Subtotal'

# ==================== ADMINISTRACIÓN DE PRODUCCIÓN ====================

class ProduccionAdmin(admin.ModelAdmin):
    list_display = ('plato', 'cantidad_planificada', 'cantidad_producida', 'fecha_planificada', 
                   'estado', 'responsable', 'costo_total_display')
    list_filter = ('estado', 'fecha_planificada', 'responsable', 'plato__grupo')
    search_fields = ('plato__nombre', 'plato__codigo', 'responsable__username')
    date_hierarchy = 'fecha_planificada'
    
    def costo_total_display(self, obj):
        return format_html('€{:.2f}', obj.costo_total)
    costo_total_display.short_description = 'Costo Total'

class InventarioAdmin(admin.ModelAdmin):
    list_display = ('plato', 'cantidad_disponible', 'cantidad_reservada', 'fecha_produccion', 
                   'fecha_vencimiento', 'estado_frescura_display', 'ubicacion')
    list_filter = ('ubicacion', 'fecha_produccion', 'plato__grupo')
    search_fields = ('plato__nombre', 'plato__codigo', 'ubicacion')
    date_hierarchy = 'fecha_vencimiento'
    
    def estado_frescura_display(self, obj):
        estado = obj.estado_frescura
        colors = {
            'FRESCO': 'green',
            'ADVERTENCIA': 'orange', 
            'CRITICO': 'red',
            'VENCIDO': 'darkred'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(estado, 'black'), estado
        )
    estado_frescura_display.short_description = 'Estado'

class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('inventario', 'tipo_movimiento', 'cantidad_display', 'motivo', 
                   'usuario_responsable', 'fecha_movimiento')
    list_filter = ('tipo_movimiento', 'fecha_movimiento')
    search_fields = ('inventario__plato__nombre', 'motivo')
    readonly_fields = ('fecha_movimiento',)
    
    def cantidad_display(self, obj):
        color = 'green' if obj.cantidad >= 0 else 'red'
        signo = '+' if obj.cantidad >= 0 else ''
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{}</span>',
            color, signo, obj.cantidad
        )
    cantidad_display.short_description = 'Cantidad'

# ==================== PEDIDOS HISTÓRICOS ====================

def exportar_pedidos_excel(modeladmin, request, queryset):
    """Exportar pedidos históricos a Excel"""
    data = []
    for pedido in queryset.select_related('plato', 'usuario'):
        data.append({
            'Usuario': pedido.usuario.username,
            'Plato': pedido.plato.nombre,
            'Cantidad': pedido.cantidad,
            'Día': pedido.get_dia_semana_display(),
            'Fecha': pedido.fecha_emision,
        })

    df = pd.DataFrame(data)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=pedidos_historicos.xlsx'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Pedidos')

    return response

exportar_pedidos_excel.short_description = "Exportar pedidos seleccionados a Excel"

class PedidoHistoricoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'plato', 'cantidad', 'dia_semana', 'fecha_emision')
    list_filter = ('dia_semana', 'fecha_emision', 'plato__grupo')
    search_fields = ('usuario__username', 'plato__nombre')
    actions = [exportar_pedidos_excel]

# ==================== ACTIONS PERSONALIZADAS ====================

def duplicar_disponibilidad_semana(modeladmin, request, queryset):
    """Duplicar disponibilidades para todos los días de la semana"""
    platos_seleccionados = set()
    for disp in queryset:
        platos_seleccionados.add(disp.plato)
    
    dias_semana = ['LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB', 'DOM']
    creados = 0
    
    for plato in platos_seleccionados:
        for dia in dias_semana:
            _, created = DisponibilidadPlato.objects.get_or_create(
                plato=plato,
                dia=dia
            )
            if created:
                creados += 1
    
    modeladmin.message_user(request, f"Se crearon {creados} nuevas disponibilidades.")

duplicar_disponibilidad_semana.short_description = "Hacer disponible toda la semana"

# Agregar la acción al admin
DisponibilidadPlatoAdmin.actions = [duplicar_disponibilidad_semana]

# ==================== SITIO ADMIN PERSONALIZADO ====================

class FamiliaGastroAdminSite(admin.AdminSite):
    site_header = "Familia Gastro - Administración"
    site_title = "Familia Gastro Admin"
    index_title = "Panel de Control"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(dashboard_view), name='dashboard'),
            path('production-dashboard/', self.admin_view(production_dashboard_view), name='production_dashboard'),
        ]
        return custom_urls + urls

# ==================== REGISTROS ====================

admin.site.register(Cliente, ClienteAdmin)
admin.site.register(Empresa, EmpresaAdmin)
admin.site.register(Plato, PlatoAdmin)
admin.site.register(DisponibilidadPlato, DisponibilidadPlatoAdmin)
admin.site.register(CarritoItem, CarritoItemAdmin)
admin.site.register(Recibo, ReciboAdmin)
admin.site.register(ReciboItem, ReciboItemAdmin)
admin.site.register(PedidoHistorico, PedidoHistoricoAdmin)
admin.site.register(Produccion, ProduccionAdmin)
admin.site.register(Inventario, InventarioAdmin)
admin.site.register(MovimientoInventario, MovimientoInventarioAdmin)