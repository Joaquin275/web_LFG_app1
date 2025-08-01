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

@admin.register(Cliente)
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

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'cif', 'direccion')
    search_fields = ('codigo', 'nombre', 'cif')
    ordering = ('codigo',)

@admin.register(Plato)
class PlatoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'grupo', 'precio', 'precio_sin_iva', 'estado')
    list_filter = ('grupo', 'estado')
    search_fields = ('codigo', 'nombre', 'ingredientes', 'alergenos')
    readonly_fields = ('precio_sin_iva',)
    list_per_page = 20
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion', 'grupo', 'estado')
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
        ('Imagen', {
            'fields': ('imagen',),
            'classes': ('collapse',)
        }),
    )

@admin.register(DisponibilidadPlato)
class DisponibilidadPlatoAdmin(admin.ModelAdmin):
    list_display = ('plato', 'dia_display')
    list_filter = ('dia', 'plato__grupo')
    search_fields = ('plato__nombre', 'plato__codigo')
    
    def dia_display(self, obj):
        return obj.get_dia_display()
    dia_display.short_description = 'Día'

@admin.register(CarritoItem)
class CarritoItemAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'plato', 'cantidad', 'dia_semana', 'fecha_agregado')
    list_filter = ('dia_semana', 'fecha_agregado')
    search_fields = ('usuario__username', 'plato__nombre')

@admin.register(Recibo)
class ReciboAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'empresa', 'total', 'pagado', 'estado_pago', 'fecha_compra')
    list_filter = ('pagado', 'estado_pago', 'fecha_compra')
    search_fields = ('usuario__username', 'empresa__nombre')
    readonly_fields = ('fecha_compra',)

@admin.register(ReciboItem)
class ReciboItemAdmin(admin.ModelAdmin):
    list_display = ('recibo', 'plato', 'cantidad', 'precio_unitario', 'subtotal_display')
    search_fields = ('recibo__id', 'plato__nombre')
    
    def subtotal_display(self, obj):
        return f"€{obj.subtotal():.2f}"
    subtotal_display.short_description = 'Subtotal'

# ==================== ADMINISTRACIÓN DE PRODUCCIÓN ====================

@admin.register(Produccion)
class ProduccionAdmin(admin.ModelAdmin):
    list_display = ('plato', 'cantidad_planificada', 'cantidad_producida', 'fecha_planificada', 
                   'estado', 'responsable', 'costo_total_display')
    list_filter = ('estado', 'fecha_planificada', 'responsable', 'plato__grupo')
    search_fields = ('plato__nombre', 'plato__codigo', 'responsable__username')
    date_hierarchy = 'fecha_planificada'
    
    fieldsets = (
        ('Información General', {
            'fields': ('plato', 'cantidad_planificada', 'cantidad_producida', 'estado', 'responsable')
        }),
        ('Fechas', {
            'fields': ('fecha_planificada', 'fecha_inicio', 'fecha_completada')
        }),
        ('Costos', {
            'fields': ('costo_ingredientes', 'costo_mano_obra', 'otros_costos'),
            'classes': ('collapse',)
        }),
        ('Notas', {
            'fields': ('notas',),
            'classes': ('collapse',)
        }),
    )
    
    def costo_total_display(self, obj):
        return format_html('€{:.2f}', obj.costo_total)
    costo_total_display.short_description = 'Costo Total'

@admin.register(Inventario)
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

@admin.register(MovimientoInventario)
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

@admin.register(PedidoHistorico)
class PedidoHistoricoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'plato', 'cantidad', 'dia_semana', 'fecha_emision')
    list_filter = ('dia_semana', 'fecha_emision', 'plato__grupo')
    search_fields = ('usuario__username', 'plato__nombre')
    actions = [exportar_pedidos_excel]

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

# Crear instancia personalizada del admin (opcional, Jazzmin maneja esto)
# admin_site = FamiliaGastroAdminSite(name='familia_gastro_admin')