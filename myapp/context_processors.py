from django.db.models import Count
from datetime import date
from .models import Plato, DisponibilidadPlato, Cliente, Recibo

def admin_stats(request):
    """
    Context processor para proporcionar estadísticas al dashboard del admin
    """
    # Solo agregar stats si estamos en el admin
    if not request.path.startswith('/admin/'):
        return {}
    
    try:
        # Obtener estadísticas básicas
        stats = {
            'platos_count': Plato.objects.filter(estado='disponible').count(),
            'disponibilidades_count': DisponibilidadPlato.objects.count(),
            'clientes_count': Cliente.objects.count(),
            'pedidos_hoy': Recibo.objects.filter(fecha_compra__date=date.today()).count(),
        }
        
        return stats
    except Exception as e:
        # Si hay algún error, devolver valores por defecto
        return {
            'platos_count': 0,
            'disponibilidades_count': 0,
            'clientes_count': 0,
            'pedidos_hoy': 0,
        }