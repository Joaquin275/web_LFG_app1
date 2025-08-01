from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import timedelta, date
from .models import (Cliente, Empresa, Plato, CarritoItem, Recibo, ReciboItem, 
                     PedidoHistorico, Produccion, Inventario, MovimientoInventario)
from .serializers import (
    PlatoSerializer, ClienteSerializer, EmpresaSerializer, 
    CarritoItemSerializer, ReciboSerializer, PedidoHistoricoSerializer,
    DashboardStatsSerializer
)
from rest_framework.decorators import api_view


class PlatoViewSet(viewsets.ModelViewSet):
    queryset = Plato.objects.all()
    serializer_class = PlatoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Plato.objects.all()
        grupo = self.request.query_params.get('grupo', None)
        estado = self.request.query_params.get('estado', None)
        
        if grupo:
            queryset = queryset.filter(grupo=grupo)
        if estado:
            queryset = queryset.filter(estado=estado)
            
        return queryset.order_by('nombre')
    
    @action(detail=False, methods=['get'])
    def mas_vendidos(self, request):
        """Obtiene los platos más vendidos"""
        platos_vendidos = PedidoHistorico.objects.values('plato__nombre').annotate(
            total_vendido=Sum('cantidad')
        ).order_by('-total_vendido')[:10]
        
        return Response(platos_vendidos)


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def activos(self, request):
        """Obtiene clientes activos (con pedidos en los últimos 30 días)"""
        fecha_limite = timezone.now() - timedelta(days=30)
        clientes_activos = Cliente.objects.filter(
            usuario__pedidohistorico__fecha_emision__gte=fecha_limite
        ).distinct()
        
        serializer = self.get_serializer(clientes_activos, many=True)
        return Response(serializer.data)


class CarritoViewSet(viewsets.ModelViewSet):
    serializer_class = CarritoItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CarritoItem.objects.filter(usuario=self.request.user)
    
    @action(detail=False, methods=['get'])
    def resumen(self, request):
        """Obtiene resumen del carrito"""
        items = self.get_queryset()
        total = sum(item.subtotal() for item in items)
        
        return Response({
            'total_items': items.count(),
            'total_precio': total,
            'items': CarritoItemSerializer(items, many=True).data
        })
    
    @action(detail=False, methods=['delete'])
    def limpiar(self, request):
        """Limpia todo el carrito"""
        self.get_queryset().delete()
        return Response({'message': 'Carrito limpiado exitosamente'})


class ReciboViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ReciboSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Recibo.objects.all()
        return Recibo.objects.filter(usuario=self.request.user)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Obtiene estadísticas de recibos"""
        queryset = self.get_queryset()
        
        stats = {
            'total_recibos': queryset.count(),
            'total_ventas': queryset.aggregate(Sum('total'))['total__sum'] or 0,
            'recibos_pagados': queryset.filter(pagado=True).count(),
            'recibos_pendientes': queryset.filter(pagado=False).count(),
        }
        
        return Response(stats)


class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Obtiene estadísticas generales del dashboard"""
        # Fechas para filtros
        hoy = timezone.now().date()
        hace_30_dias = hoy - timedelta(days=30)
        hace_7_dias = hoy - timedelta(days=7)
        
        # Estadísticas generales
        total_pedidos = PedidoHistorico.objects.count()
        total_ventas = Recibo.objects.filter(pagado=True).aggregate(Sum('total'))['total__sum'] or 0
        pedidos_pendientes = Recibo.objects.filter(pagado=False).count()
        pedidos_completados = Recibo.objects.filter(pagado=True).count()
        
        # Platos más vendidos
        platos_mas_vendidos = list(PedidoHistorico.objects.values('plato__nombre').annotate(
            total=Sum('cantidad')
        ).order_by('-total')[:5])
        
        # Ventas por día (últimos 7 días)
        ventas_por_dia = []
        for i in range(7):
            fecha = hoy - timedelta(days=i)
            ventas_dia = Recibo.objects.filter(
                fecha_compra__date=fecha,
                pagado=True
            ).aggregate(Sum('total'))['total__sum'] or 0
            
            ventas_por_dia.append({
                'fecha': fecha.strftime('%Y-%m-%d'),
                'ventas': float(ventas_dia)
            })
        
        # Clientes activos
        clientes_activos = Cliente.objects.filter(
            usuario__pedidohistorico__fecha_emision__gte=hace_30_dias
        ).distinct().count()
        
        data = {
            'total_pedidos': total_pedidos,
            'total_ventas': float(total_ventas),
            'pedidos_pendientes': pedidos_pendientes,
            'pedidos_completados': pedidos_completados,
            'platos_mas_vendidos': platos_mas_vendidos,
            'ventas_por_dia': ventas_por_dia,
            'clientes_activos': clientes_activos,
        }
        
        serializer = DashboardStatsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def ventas_mensuales(self, request):
        """Obtiene ventas de los últimos 12 meses"""
        ventas_mensuales = []
        hoy = timezone.now().date()
        
        for i in range(12):
            # Calcular el primer día del mes
            if hoy.month - i <= 0:
                mes = 12 + (hoy.month - i)
                año = hoy.year - 1
            else:
                mes = hoy.month - i
                año = hoy.year
            
            # Ventas del mes
            ventas_mes = Recibo.objects.filter(
                fecha_compra__year=año,
                fecha_compra__month=mes,
                pagado=True
            ).aggregate(Sum('total'))['total__sum'] or 0
            
            ventas_mensuales.append({
                'mes': f"{año}-{mes:02d}",
                'ventas': float(ventas_mes)
            })
        
        return Response(ventas_mensuales[::-1])  # Invertir para orden cronológico


@api_view(['GET'])
def dashboard_estadisticas(request):
    """API endpoint para estadísticas del dashboard principal"""
    # Calcular estadísticas básicas
    total_pedidos = PedidoHistorico.objects.count()
    total_ventas = Recibo.objects.filter(pagado=True).aggregate(Sum('total'))['total__sum'] or 0
    pedidos_pendientes = Recibo.objects.filter(pagado=False).count()
    clientes_activos = Cliente.objects.filter(
        usuario__pedidohistorico__fecha_emision__gte=timezone.now() - timedelta(days=30)
    ).distinct().count()
    
    # Ventas por día (últimos 7 días)
    ventas_por_dia = []
    for i in range(7):
        fecha = date.today() - timedelta(days=i)
        ventas_dia = Recibo.objects.filter(
            pagado=True,
            fecha_pago__date=fecha
        ).aggregate(Sum('total'))['total__sum'] or 0
        ventas_por_dia.append({
            'fecha': fecha.isoformat(),
            'ventas': float(ventas_dia)
        })
    
    # Platos más vendidos
    platos_mas_vendidos = PedidoHistorico.objects.values('plato__nombre').annotate(
        total=Sum('cantidad')
    ).order_by('-total')[:5]
    
    return Response({
        'total_pedidos': total_pedidos,
        'total_ventas': float(total_ventas),
        'pedidos_pendientes': pedidos_pendientes,
        'clientes_activos': clientes_activos,
        'ventas_por_dia': list(reversed(ventas_por_dia)),
        'platos_mas_vendidos': list(platos_mas_vendidos)
    })

@api_view(['GET'])
def dashboard_ventas_mensuales(request):
    """API endpoint para ventas mensuales"""
    from django.db.models import Extract
    
    ventas_mensuales = Recibo.objects.filter(
        pagado=True,
        fecha_pago__gte=timezone.now() - timedelta(days=365)
    ).extra(
        select={'mes': "DATE_FORMAT(fecha_pago, '%%Y-%%m')"}
    ).values('mes').annotate(
        ventas=Sum('total')
    ).order_by('mes')
    
    return Response([{
        'mes': item['mes'],
        'ventas': float(item['ventas'])
    } for item in ventas_mensuales])

# ==================== NUEVAS APIs DE PRODUCCIÓN ====================

@api_view(['GET'])
def production_dashboard_stats(request):
    """API endpoint para estadísticas del dashboard de producción"""
    today = date.today()
    
    # Estadísticas básicas de producción
    producciones_activas = Produccion.objects.filter(
        estado__in=['PLANIFICADA', 'EN_PROCESO']
    ).count()
    
    producciones_completadas_hoy = Produccion.objects.filter(
        estado='COMPLETADA',
        fecha_completada__date=today
    ).count()
    
    inventario_critico = Inventario.objects.filter(
        Q(cantidad_disponible__lte=10) | 
        Q(fecha_vencimiento__lte=today + timedelta(days=2))
    ).count()
    
    eficiencia_promedio = Produccion.objects.filter(
        estado='COMPLETADA',
        fecha_completada__gte=timezone.now() - timedelta(days=30)
    ).aggregate(
        promedio=Avg('eficiencia')
    )['promedio'] or 0
    
    # Producción por estado (últimos 30 días)
    produccion_por_estado = Produccion.objects.filter(
        fecha_planificada__gte=today - timedelta(days=30)
    ).values('estado').annotate(
        cantidad=Count('id')
    ).order_by('estado')
    
    # Costos de producción por día (últimos 7 días)
    costos_por_dia = []
    for i in range(7):
        fecha = today - timedelta(days=i)
        costo_dia = Produccion.objects.filter(
            fecha_completada__date=fecha,
            estado='COMPLETADA'
        ).aggregate(
            total_costos=Sum('costo_ingredientes') + Sum('costo_mano_obra') + Sum('otros_costos')
        )['total_costos'] or 0
        costos_por_dia.append({
            'fecha': fecha.isoformat(),
            'costos': float(costo_dia)
        })
    
    # Top 5 platos por volumen de producción
    top_platos_produccion = Produccion.objects.filter(
        estado='COMPLETADA',
        fecha_completada__gte=timezone.now() - timedelta(days=30)
    ).values('plato__nombre').annotate(
        total_producido=Sum('cantidad_producida')
    ).order_by('-total_producido')[:5]
    
    return Response({
        'producciones_activas': producciones_activas,
        'producciones_completadas_hoy': producciones_completadas_hoy,
        'inventario_critico': inventario_critico,
        'eficiencia_promedio': float(eficiencia_promedio),
        'produccion_por_estado': list(produccion_por_estado),
        'costos_por_dia': list(reversed(costos_por_dia)),
        'top_platos_produccion': list(top_platos_produccion)
    })

@api_view(['GET'])
def inventory_alerts(request):
    """API endpoint para alertas de inventario"""
    today = date.today()
    
    # Inventario con poco stock
    bajo_stock = Inventario.objects.filter(
        cantidad_disponible__lte=10
    ).select_related('plato').values(
        'plato__nombre', 'cantidad_disponible', 'ubicacion'
    )
    
    # Inventario próximo a vencer
    proximo_vencimiento = Inventario.objects.filter(
        fecha_vencimiento__lte=today + timedelta(days=3),
        fecha_vencimiento__gt=today
    ).select_related('plato').values(
        'plato__nombre', 'cantidad_disponible', 'fecha_vencimiento', 'ubicacion'
    )
    
    # Inventario vencido
    vencido = Inventario.objects.filter(
        fecha_vencimiento__lte=today
    ).select_related('plato').values(
        'plato__nombre', 'cantidad_disponible', 'fecha_vencimiento', 'ubicacion'
    )
    
    return Response({
        'bajo_stock': list(bajo_stock),
        'proximo_vencimiento': [
            {
                **item,
                'fecha_vencimiento': item['fecha_vencimiento'].isoformat()
            } for item in proximo_vencimiento
        ],
        'vencido': [
            {
                **item,
                'fecha_vencimiento': item['fecha_vencimiento'].isoformat()
            } for item in vencido
        ]
    })

@api_view(['GET'])
def production_efficiency_chart(request):
    """API endpoint para gráfico de eficiencia de producción"""
    # Eficiencia por plato (últimos 30 días)
    eficiencia_por_plato = Produccion.objects.filter(
        estado='COMPLETADA',
        fecha_completada__gte=timezone.now() - timedelta(days=30)
    ).values('plato__nombre').annotate(
        eficiencia_promedio=Avg('eficiencia'),
        total_producciones=Count('id')
    ).order_by('-eficiencia_promedio')[:10]
    
    # Evolución de eficiencia semanal
    eficiencia_semanal = []
    for i in range(4):  # Últimas 4 semanas
        inicio_semana = timezone.now() - timedelta(weeks=i+1)
        fin_semana = timezone.now() - timedelta(weeks=i)
        
        eficiencia_semana = Produccion.objects.filter(
            estado='COMPLETADA',
            fecha_completada__gte=inicio_semana,
            fecha_completada__lt=fin_semana
        ).aggregate(
            promedio=Avg('eficiencia')
        )['promedio'] or 0
        
        eficiencia_semanal.append({
            'semana': f"Semana {4-i}",
            'eficiencia': float(eficiencia_semana)
        })
    
    return Response({
        'eficiencia_por_plato': [
            {
                'plato': item['plato__nombre'],
                'eficiencia': float(item['eficiencia_promedio'] or 0),
                'producciones': item['total_producciones']
            } for item in eficiencia_por_plato
        ],
        'eficiencia_semanal': list(reversed(eficiencia_semanal))
    })

@api_view(['GET'])
def inventory_rotation_chart(request):
    """API endpoint para gráfico de rotación de inventario"""
    # Movimientos de inventario por tipo (últimos 30 días)
    movimientos_por_tipo = MovimientoInventario.objects.filter(
        fecha_movimiento__gte=timezone.now() - timedelta(days=30)
    ).values('tipo_movimiento').annotate(
        total_cantidad=Sum('cantidad'),
        total_movimientos=Count('id')
    ).order_by('tipo_movimiento')
    
    # Stock actual por grupo de plato
    stock_por_grupo = Inventario.objects.select_related('plato').values(
        'plato__grupo'
    ).annotate(
        total_stock=Sum('cantidad_disponible')
    ).order_by('-total_stock')
    
    return Response({
        'movimientos_por_tipo': [
            {
                'tipo': item['tipo_movimiento'],
                'cantidad': item['total_cantidad'],
                'movimientos': item['total_movimientos']
            } for item in movimientos_por_tipo
        ],
        'stock_por_grupo': [
            {
                'grupo': item['plato__grupo'],
                'stock': item['total_stock']
            } for item in stock_por_grupo
        ]
    })