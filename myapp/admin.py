from django.contrib import admin
from .models import (Cliente, Empresa, Plato, DisponibilidadPlato, CarritoItem, 
                     Recibo, ReciboItem, PedidoHistorico, Produccion, Inventario, MovimientoInventario)
from .forms import DisponibilidadPlatoForm, CarritoItemForm
import pandas as pd
from django.http import HttpResponse
from django.urls import path
from django.shortcuts import render
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta, date
from django.utils.html import format_html
from django.contrib.admin import SimpleListFilter

# Vista personalizada para el dashboard
def dashboard_view(request):
    return render(request, 'admin/dashboard.html')

# Vista para el dashboard de producción
def production_dashboard_view(request):
    # Estadísticas de producción
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
        'eficiencia_promedio': Produccion.objects.filter(
            estado='COMPLETADA',
            fecha_completada__gte=timezone.now() - timedelta(days=30)
        ).aggregate(
            promedio=models.Avg('eficiencia')
        )['promedio'] or 0,
    }
    return render(request, 'admin/production_dashboard.html', context)

# Filtros personalizados
class EstadoFrescuraFilter(SimpleListFilter):
    title = 'Estado de Frescura'
    parameter_name = 'frescura'

    def lookups(self, request, model_admin):
        return (
            ('fresco', 'Fresco'),
            ('advertencia', 'Advertencia'),
            ('critico', 'Crítico'),
            ('vencido', 'Vencido'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'fresco':
            return queryset.filter(fecha_vencimiento__gt=date.today() + timedelta(days=2))
        elif self.value() == 'advertencia':
            return queryset.filter(
                fecha_vencimiento__gt=date.today() + timedelta(days=1),
                fecha_vencimiento__lte=date.today() + timedelta(days=2)
            )
        elif self.value() == 'critico':
            return queryset.filter(
                fecha_vencimiento__gt=date.today(),
                fecha_vencimiento__lte=date.today() + timedelta(days=1)
            )
        elif self.value() == 'vencido':
            return queryset.filter(fecha_vencimiento__lte=date.today())

# Personalizar el AdminSite
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

# Crear instancia personalizada del admin
admin_site = FamiliaGastroAdminSite(name='familia_gastro_admin')

# ==================== ADMINISTRACIÓN DE PRODUCCIÓN ====================

@admin.register(Produccion)
class ProduccionAdmin(admin.ModelAdmin):
    list_display = ('plato', 'cantidad_planificada', 'cantidad_producida', 'fecha_planificada', 
                   'estado', 'responsable', 'porcentaje_completado_display', 'costo_total_display')
    list_filter = ('estado', 'fecha_planificada', 'responsable', 'plato__grupo')
    search_fields = ('plato__nombre', 'plato__codigo', 'responsable__username', 'notas')
    date_hierarchy = 'fecha_planificada'
    readonly_fields = ('created_at', 'updated_at', 'porcentaje_completado_display', 
                      'costo_total_display', 'eficiencia_display')
    
    fieldsets = (
        ('Información General', {
            'fields': ('plato', 'cantidad_planificada', 'cantidad_producida', 'estado', 'responsable')
        }),
        ('Fechas', {
            'fields': ('fecha_planificada', 'fecha_inicio', 'fecha_completada')
        }),
        ('Costos de Producción', {
            'fields': ('costo_ingredientes', 'costo_mano_obra', 'otros_costos', 'costo_total_display'),
            'classes': ('collapse',)
        }),
        ('Métricas', {
            'fields': ('porcentaje_completado_display', 'eficiencia_display'),
            'classes': ('collapse',)
        }),
        ('Notas', {
            'fields': ('notas',),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def porcentaje_completado_display(self, obj):
        porcentaje = obj.porcentaje_completado
        if porcentaje >= 100:
            color = 'green'
        elif porcentaje >= 50:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, porcentaje
        )
    porcentaje_completado_display.short_description = 'Progreso'
    
    def costo_total_display(self, obj):
        return format_html('€{:.2f}', obj.costo_total)
    costo_total_display.short_description = 'Costo Total'
    
    def eficiencia_display(self, obj):
        eficiencia = obj.eficiencia
        if eficiencia >= 80:
            color = 'green'
        elif eficiencia >= 60:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, eficiencia
        ) if eficiencia > 0 else '-'
    eficiencia_display.short_description = 'Eficiencia'

@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ('plato', 'cantidad_disponible', 'cantidad_reservada', 'cantidad_total_display',
                   'fecha_produccion', 'fecha_vencimiento', 'dias_hasta_vencimiento_display', 
                   'estado_frescura_display', 'ubicacion')
    list_filter = ('ubicacion', EstadoFrescuraFilter, 'fecha_produccion', 'plato__grupo')
    search_fields = ('plato__nombre', 'plato__codigo', 'ubicacion', 'produccion__id')
    date_hierarchy = 'fecha_vencimiento'
    readonly_fields = ('cantidad_total_display', 'dias_hasta_vencimiento_display', 
                      'estado_frescura_display', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Información del Producto', {
            'fields': ('plato', 'produccion', 'ubicacion')
        }),
        ('Cantidades', {
            'fields': ('cantidad_disponible', 'cantidad_reservada', 'cantidad_total_display')
        }),
        ('Fechas', {
            'fields': ('fecha_produccion', 'fecha_vencimiento', 'dias_hasta_vencimiento_display', 'estado_frescura_display')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def cantidad_total_display(self, obj):
        return obj.cantidad_total
    cantidad_total_display.short_description = 'Total'
    
    def dias_hasta_vencimiento_display(self, obj):
        dias = obj.dias_hasta_vencimiento
        if dias < 0:
            return format_html('<span style="color: red; font-weight: bold;">Vencido ({} días)</span>', abs(dias))
        elif dias <= 1:
            return format_html('<span style="color: red; font-weight: bold;">{} días</span>', dias)
        elif dias <= 2:
            return format_html('<span style="color: orange; font-weight: bold;">{} días</span>', dias)
        else:
            return format_html('<span style="color: green;">{} días</span>', dias)
    dias_hasta_vencimiento_display.short_description = 'Días hasta vencimiento'
    
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
    list_filter = ('tipo_movimiento', 'fecha_movimiento', 'usuario_responsable')
    search_fields = ('inventario__plato__nombre', 'motivo', 'usuario_responsable__username')
    date_hierarchy = 'fecha_movimiento'
    readonly_fields = ('fecha_movimiento',)
    
    def cantidad_display(self, obj):
        color = 'green' if obj.cantidad >= 0 else 'red'
        signo = '+' if obj.cantidad >= 0 else ''
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{}</span>',
            color, signo, obj.cantidad
        )
    cantidad_display.short_description = 'Cantidad'

# ==================== ADMINISTRACIÓN EXISTENTE MEJORADA ====================

class DisponibilidadPlatoAdmin(admin.ModelAdmin):
    form = DisponibilidadPlatoForm
    list_display = ('plato', 'display_dias_semana')
    list_filter = ('plato',)
    search_fields = ('plato__nombre',)

    def display_dias_semana(self, obj):
        return obj.get_dia_display()
    display_dias_semana.short_description = "Día disponible"

class CarritoItemAdmin(admin.ModelAdmin):
    form = CarritoItemForm
    list_display = ('usuario', 'plato', 'cantidad', 'dia_semana')

class myappAdmin(admin.ModelAdmin):
    readonly_fields = ("Creacion_cuenta",)

# ==================== ACCIONES DE EXPORTACIÓN ====================

def exportar_pedidohistorico_excel(modeladmin, request, queryset):
    # Vamos a tomar solo los pedidos seleccionados (queryset)
    # Si quieres que exporte todos los pedidos, cambia queryset por PedidoHistorico.objects.all()

    data = []
    for pedido in queryset.select_related('plato'):
        data.append({
            'Dia': pedido.get_dia_semana_display(),
            'Plato': pedido.plato.nombre,
            'Cantidad': pedido.cantidad,
        })

    df = pd.DataFrame(data)

    # Crear tabla pivote donde filas son días y columnas platos
    tabla_pivot = pd.pivot_table(
        df,
        index='Dia',
        columns='Plato',
        values='Cantidad',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    # Ordenar días de la semana
    dias_orden = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
    tabla_pivot['Dia'] = pd.Categorical(tabla_pivot['Dia'], categories=dias_orden, ordered=True)
    tabla_pivot = tabla_pivot.sort_values('Dia')

    # Crear respuesta HTTP con Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=pedido_historico.xlsx'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        tabla_pivot.to_excel(writer, index=False, sheet_name='Pedidos')

    return response

exportar_pedidohistorico_excel.short_description = "Exportar pedidos históricos seleccionados a Excel"

def exportar_datos_envio_excel(modeladmin, request, queryset):
    data = []

    for pedido in queryset.select_related('usuario', 'plato'):
        try:
            cliente = Cliente.objects.get(usuario=pedido.usuario)
            empresa = cliente.empresa
        except Cliente.DoesNotExist:
            cliente = None
            empresa = None

        data.append({
            'Nombre del Usuario': cliente.Nombre_Completo if cliente else pedido.usuario.username,
            'Celular': cliente.celular if cliente else '',
            'Empresa': empresa.nombre if empresa else ('Particular' if cliente and cliente.es_particular else ''),
            'Dirección': (
                cliente.direccion_particular if cliente and cliente.es_particular
                else (empresa.direccion if empresa else '')
            ),
            'Plato': pedido.plato.nombre,
            'Cantidad': pedido.cantidad,
            'Día': pedido.get_dia_semana_display(),
        })

    df = pd.DataFrame(data)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=datos_envio.xlsx'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos de Envío')

    return response

exportar_datos_envio_excel.short_description = "Exportar datos de envío seleccionados a Excel"

def exportar_produccion_excel(modeladmin, request, queryset):
    """Exportar datos de producción a Excel"""
    data = []
    for produccion in queryset.select_related('plato', 'responsable'):
        data.append({
            'Plato': produccion.plato.nombre,
            'Código Plato': produccion.plato.codigo,
            'Cantidad Planificada': produccion.cantidad_planificada,
            'Cantidad Producida': produccion.cantidad_producida,
            'Fecha Planificada': produccion.fecha_planificada,
            'Estado': produccion.get_estado_display(),
            'Responsable': produccion.responsable.username if produccion.responsable else '',
            'Costo Ingredientes': float(produccion.costo_ingredientes),
            'Costo Mano de Obra': float(produccion.costo_mano_obra),
            'Otros Costos': float(produccion.otros_costos),
            'Costo Total': float(produccion.costo_total),
            'Porcentaje Completado': produccion.porcentaje_completado,
            'Eficiencia': produccion.eficiencia,
        })

    df = pd.DataFrame(data)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=produccion.xlsx'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Producción')

    return response

exportar_produccion_excel.short_description = "Exportar producción seleccionada a Excel"

# Agregar la acción a ProduccionAdmin
ProduccionAdmin.actions = [exportar_produccion_excel]

class PedidoHistoricoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'plato', 'cantidad', 'dia_semana', 'fecha_emision']
    actions = [exportar_pedidohistorico_excel, exportar_datos_envio_excel]

# ==================== REGISTROS DE MODELOS ====================

# Registros estándar
admin.site.register(Cliente, myappAdmin)
admin.site.register(Empresa)

@admin.register(Plato)
class PlatoAdmin(admin.ModelAdmin):
    list_display = ('codigo','nombre', 'grupo', 'precio', 'precio_sin_iva', 'estado')
    list_filter = ('grupo', 'estado')
    search_fields = ('nombre', 'ingredientes', 'alergenos')
    readonly_fields = ('precio_sin_iva',)

admin.site.register(DisponibilidadPlato, DisponibilidadPlatoAdmin)
admin.site.register(CarritoItem, CarritoItemAdmin)
admin.site.register(ReciboItem)
admin.site.register(PedidoHistorico, PedidoHistoricoAdmin)

class ReciboAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'empresa', 'total', 'pagado', 'estado_pago', 'metodo_pago', 'fecha_pago')
    list_filter = ('pagado', 'estado_pago', 'fecha_pago')
    search_fields = ('usuario__username', 'empresa__nombre', 'referencia_pago')
    readonly_fields = ('fecha_compra', 'fecha_pago', 'url_iframe', 'referencia_pago', 'estado_pago', 'metodo_pago')

admin.site.register(Recibo, ReciboAdmin)