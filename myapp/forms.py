from django.forms import ModelForm
from .models import (Cliente, DisponibilidadPlato, Plato, CarritoItem, 
                     Produccion, Inventario, MovimientoInventario)
from django import forms
from django.core.exceptions import ValidationError

class Cliente_creacion(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['Nombre_Completo', 'es_particular', 'direccion_particular', 'celular', 'dni', 'correo', 'empresa']
        widgets = {
            'Nombre_Completo': forms.TextInput(attrs={'class': 'form-control'}),
            'es_particular': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_es_particular'}),
            'direccion_particular': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Dirección si es particular',
                'id': 'id_direccion_particular'
            }),
            'celular': forms.TextInput(attrs={'class': 'form-control'}),
            'dni': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese su NIE o DNI'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese su correo electrónico'}),
            'empresa': forms.Select(attrs={'class': 'form-select', 'id': 'id_empresa'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['empresa'].required = False

# --------------- PLATO DISPONIBILIDAD----------

class DisponibilidadPlatoForm(forms.ModelForm):
    class Meta:
        model = DisponibilidadPlato
        fields = '__all__'
        widgets = {
            'plato': forms.Select(attrs={'class': 'form-control'}),
            'dia': forms.Select(attrs={'class': 'form-control'}),
        }

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
        widgets = {
            'usuario': forms.Select(attrs={'class': 'form-control'}),
            'plato': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'dia_semana': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Verificamos si el objeto existe y tiene plato asignado
        if self.instance and self.instance.pk and self.instance.plato:
            plato = self.instance.plato
            # Obtenemos los días disponibles para ese plato
            try:
                dias_disponibles = DisponibilidadPlato.objects.filter(plato=plato).values_list('dia', flat=True)
                # Filtramos el campo dia_semana para mostrar solo los días disponibles
                self.fields['dia_semana'].choices = [
                    (dia, label) for dia, label in self.fields['dia_semana'].choices if dia in dias_disponibles
                ]
            except:
                # Si hay algún error, mantenemos todas las opciones
                pass

# ==================== FORMULARIOS DE PRODUCCIÓN ====================

class ProduccionForm(forms.ModelForm):
    class Meta:
        model = Produccion
        fields = '__all__'
        widgets = {
            'plato': forms.Select(attrs={'class': 'form-control'}),
            'cantidad_planificada': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'cantidad_producida': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'fecha_planificada': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_inicio': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'fecha_completada': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'costo_ingredientes': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'costo_mano_obra': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'otros_costos': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'responsable': forms.Select(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class InventarioForm(forms.ModelForm):
    class Meta:
        model = Inventario
        fields = '__all__'
        widgets = {
            'plato': forms.Select(attrs={'class': 'form-control'}),
            'cantidad_disponible': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'cantidad_reservada': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'fecha_produccion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_vencimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
            'produccion': forms.Select(attrs={'class': 'form-control'}),
        }

class MovimientoInventarioForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = '__all__'
        widgets = {
            'inventario': forms.Select(attrs={'class': 'form-control'}),
            'tipo_movimiento': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'motivo': forms.TextInput(attrs={'class': 'form-control'}),
            'recibo': forms.Select(attrs={'class': 'form-control'}),
            'usuario_responsable': forms.Select(attrs={'class': 'form-control'}),
        }





