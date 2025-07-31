from rest_framework import serializers
from .models import Plato, Cliente, Empresa, CarritoItem, Recibo, ReciboItem, PedidoHistorico


class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = '__all__'


class PlatoSerializer(serializers.ModelSerializer):
    grupo_display = serializers.CharField(source='get_grupo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = Plato
        fields = '__all__'


class ClienteSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    
    class Meta:
        model = Cliente
        fields = '__all__'


class CarritoItemSerializer(serializers.ModelSerializer):
    plato_nombre = serializers.CharField(source='plato.nombre', read_only=True)
    plato_precio = serializers.DecimalField(source='plato.precio', max_digits=8, decimal_places=2, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    dia_semana_display = serializers.CharField(source='get_dia_semana_display', read_only=True)
    
    class Meta:
        model = CarritoItem
        fields = '__all__'


class ReciboItemSerializer(serializers.ModelSerializer):
    plato_nombre = serializers.CharField(source='plato.nombre', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = ReciboItem
        fields = '__all__'


class ReciboSerializer(serializers.ModelSerializer):
    items = ReciboItemSerializer(many=True, read_only=True)
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    estado_pago_display = serializers.CharField(source='get_estado_pago_display', read_only=True)
    
    class Meta:
        model = Recibo
        fields = '__all__'


class PedidoHistoricoSerializer(serializers.ModelSerializer):
    plato_nombre = serializers.CharField(source='plato.nombre', read_only=True)
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    dia_semana_display = serializers.CharField(source='get_dia_semana_display', read_only=True)
    
    class Meta:
        model = PedidoHistorico
        fields = '__all__'


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer para estadísticas del dashboard"""
    total_pedidos = serializers.IntegerField()
    total_ventas = serializers.DecimalField(max_digits=10, decimal_places=2)
    pedidos_pendientes = serializers.IntegerField()
    pedidos_completados = serializers.IntegerField()
    platos_mas_vendidos = serializers.ListField()
    ventas_por_dia = serializers.ListField()
    clientes_activos = serializers.IntegerField()