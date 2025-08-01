from django.db.models import Count, Sum, Q
from datetime import date, timedelta
from .models import Plato, DisponibilidadPlato, Cliente, Recibo, ReciboItem, Produccion, Inventario

def admin_stats(request):
    """
    Context processor mejorado para proporcionar estadísticas completas del negocio
    """
    # Solo agregar stats si estamos en el admin
    if not request.path.startswith('/admin/'):
        return {}
    
    try:
        # Fechas para cálculos
        hoy = date.today()
        hace_una_semana = hoy - timedelta(days=7)
        hace_un_mes = hoy - timedelta(days=30)
        
        # Estadísticas principales
        platos_activos = Plato.objects.filter(estado='disponible').count()
        total_disponibilidades = DisponibilidadPlato.objects.count()
        total_clientes = Cliente.objects.count()
        
        # Pedidos y ventas
        pedidos_hoy = Recibo.objects.filter(fecha_compra__date=hoy).count()
        pedidos_semana = Recibo.objects.filter(fecha_compra__date__gte=hace_una_semana).count()
        
        # Ingresos
        ingresos_hoy = Recibo.objects.filter(
            fecha_compra__date=hoy, 
            pagado=True
        ).aggregate(total=Sum('total'))['total'] or 0
        
        ingresos_semana = Recibo.objects.filter(
            fecha_compra__date__gte=hace_una_semana,
            pagado=True
        ).aggregate(total=Sum('total'))['total'] or 0
        
        # Platos más populares
        platos_populares = ReciboItem.objects.values('plato__nombre').annotate(
            cantidad_total=Sum('cantidad')
        ).order_by('-cantidad_total')[:3]
        
        # Disponibilidades por día
        disponibilidades_por_dia = {}
        for dia_code, dia_name in DisponibilidadPlato.DIAS_SEMANA:
            count = DisponibilidadPlato.objects.filter(dia=dia_code).count()
            disponibilidades_por_dia[dia_name] = count
        
        # Día con más disponibilidades
        dia_mas_activo = max(disponibilidades_por_dia.items(), key=lambda x: x[1]) if disponibilidades_por_dia else ('N/A', 0)
        
        # Estado del inventario
        inventario_bajo = Inventario.objects.filter(cantidad_disponible__lt=10).count()
        produccion_pendiente = Produccion.objects.filter(estado='planificada').count()
        
        # Clientes por tipo
        clientes_particulares = Cliente.objects.filter(es_particular=True).count()
        clientes_empresas = Cliente.objects.filter(es_particular=False).count()
        
        stats = {
            # Estadísticas principales
            'platos_count': platos_activos,
            'disponibilidades_count': total_disponibilidades,
            'clientes_count': total_clientes,
            'pedidos_hoy': pedidos_hoy,
            
            # Estadísticas extendidas
            'pedidos_semana': pedidos_semana,
            'ingresos_hoy': round(float(ingresos_hoy), 2),
            'ingresos_semana': round(float(ingresos_semana), 2),
            'platos_populares': list(platos_populares),
            'disponibilidades_por_dia': disponibilidades_por_dia,
            'dia_mas_activo': dia_mas_activo[0],
            'inventario_bajo': inventario_bajo,
            'produccion_pendiente': produccion_pendiente,
            'clientes_particulares': clientes_particulares,
            'clientes_empresas': clientes_empresas,
            
            # Métricas de rendimiento
            'ticket_promedio': round(float(ingresos_semana / pedidos_semana), 2) if pedidos_semana > 0 else 0,
            'ocupacion_semanal': round((total_disponibilidades / (7 * platos_activos)) * 100, 1) if platos_activos > 0 else 0,
        }
        
        return stats
        
    except Exception as e:
        # Si hay algún error, devolver valores por defecto
        return {
            'platos_count': 0,
            'disponibilidades_count': 0,
            'clientes_count': 0,
            'pedidos_hoy': 0,
            'pedidos_semana': 0,
            'ingresos_hoy': 0,
            'ingresos_semana': 0,
            'platos_populares': [],
            'disponibilidades_por_dia': {},
            'dia_mas_activo': 'N/A',
            'inventario_bajo': 0,
            'produccion_pendiente': 0,
            'clientes_particulares': 0,
            'clientes_empresas': 0,
            'ticket_promedio': 0,
            'ocupacion_semanal': 0,
        }