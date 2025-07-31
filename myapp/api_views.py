from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from .models import Plato, Cliente, Empresa, CarritoItem, Recibo, ReciboItem, PedidoHistorico
from .serializers import (
    PlatoSerializer, ClienteSerializer, EmpresaSerializer, 
    CarritoItemSerializer, ReciboSerializer, PedidoHistoricoSerializer,
    DashboardStatsSerializer
)


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