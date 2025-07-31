from django.contrib import admin
from .models import Cliente, Empresa, Plato, DisponibilidadPlato, CarritoItem, Recibo, ReciboItem, PedidoHistorico
from .forms import DisponibilidadPlatoForm, CarritoItemForm
import pandas as pd
from django.http import HttpResponse
from django.urls import path
from django.shortcuts import render
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta

# Vista personalizada para el dashboard
def dashboard_view(request):
    return render(request, 'admin/dashboard.html')

# Personalizar el AdminSite
class FamiliaGastroAdminSite(admin.AdminSite):
    site_header = "Familia Gastro - Administración"
    site_title = "Familia Gastro Admin"
    index_title = "Panel de Control"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(dashboard_view), name='dashboard'),
        ]
        return custom_urls + urls

# Crear instancia personalizada del admin
admin_site = FamiliaGastroAdminSite(name='familia_gastro_admin')
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


class PedidoHistoricoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'plato', 'cantidad', 'dia_semana', 'fecha_emision']
    actions = [exportar_pedidohistorico_excel, exportar_datos_envio_excel]




# Registros estándar
admin.site.register(Cliente, myappAdmin)
admin.site.register(Empresa)

@admin.register(Plato)
class PlatoAdmin(admin.ModelAdmin):
    list_display = ('codigo','nombre', 'grupo', 'precio', 'precio_sin_iva', 'estado')
    list_filter = ('grupo', 'estado')
    search_fields = ('nombre', 'ingredientes', 'alergenos')
    readonly_fields = ('precio_sin_iva',)

admin.site.register(DisponibilidadPlato, DisponibilidadPlatoAdmin)  # Usando el admin personalizado
admin.site.register(CarritoItem, CarritoItemAdmin)
admin.site.register(ReciboItem)
admin.site.register(PedidoHistorico, PedidoHistoricoAdmin)

class ReciboAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'empresa', 'total', 'pagado', 'estado_pago', 'metodo_pago', 'fecha_pago')
    list_filter = ('pagado', 'estado_pago', 'fecha_pago')
    search_fields = ('usuario__username', 'empresa__nombre', 'referencia_pago')
    readonly_fields = ('fecha_compra', 'fecha_pago', 'url_iframe', 'referencia_pago', 'estado_pago', 'metodo_pago')
admin.site.register(Recibo, ReciboAdmin)