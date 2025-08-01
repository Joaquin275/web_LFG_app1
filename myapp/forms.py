from django import forms
from django.core.exceptions import ValidationError
from .models import (
    Cliente, DisponibilidadPlato, Plato, CarritoItem, 
    Produccion, Inventario, MovimientoInventario
)

# ==================== FORMULARIOS BÁSICOS ====================

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = '__all__'

class DisponibilidadPlatoForm(forms.ModelForm):
    class Meta:
        model = DisponibilidadPlato
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        plato = cleaned_data.get('plato')
        dia = cleaned_data.get('dia')

        if plato and dia:
            # Excluir el objeto actual si estamos editando
            qs = DisponibilidadPlato.objects.filter(plato=plato, dia=dia)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError("Este plato ya está asignado para ese día.")

        return cleaned_data

class CarritoItemForm(forms.ModelForm):
    class Meta:
        model = CarritoItem
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Verificamos si el objeto existe y tiene plato asignado
        if self.instance and self.instance.pk and self.instance.plato:
            plato = self.instance.plato
            try:
                # Obtenemos los días disponibles para ese plato
                dias_disponibles = DisponibilidadPlato.objects.filter(plato=plato).values_list('dia', flat=True)
                # Filtramos el campo dia_semana para mostrar solo los días disponibles
                self.fields['dia_semana'].choices = [
                    (dia, label) for dia, label in self.fields['dia_semana'].choices if dia in dias_disponibles
                ]
            except Exception:
                # Si hay algún error, mantenemos todas las opciones
                pass

# ==================== FORMULARIOS DE PRODUCCIÓN ====================

class ProduccionForm(forms.ModelForm):
    class Meta:
        model = Produccion
        fields = '__all__'

class InventarioForm(forms.ModelForm):
    class Meta:
        model = Inventario
        fields = '__all__'

class MovimientoInventarioForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = '__all__'





