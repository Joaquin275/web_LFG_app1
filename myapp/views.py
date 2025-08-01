import requests
import json
import hashlib
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError
from .forms import ClienteForm
from .models import Plato, DisponibilidadPlato, CarritoItem, Cliente,  Recibo, ReciboItem, Empresa, PedidoHistorico
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models import F
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.urls import reverse


# Create your views here.

def helloword(request):
    return render(request, 'home.html')

def register(request):

    if request.method == 'GET':
        return render(request, 'singup.html', {
        'form': UserCreationForm()
    })
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                #register user
                user = User.objects.create_user(username=request.POST['username'],
                password=request.POST['password1'])
                user.save()
                login(request, user)
                return redirect('create_cliente')
            except IntegrityError:
                return render(request, 'singup.html', {
                'form': UserCreationForm(),
                'error': 'El usuario ya existe'
                })
        return render(request, 'singup.html', {
                'form': UserCreationForm(),
                'error': 'Su contraseña no coincide'
                })


def main(request):
    return render(request, 'main.html')    

def signout(request):
    logout(request)
    return redirect('home')

def signin(request):
    if request.method == "GET":
        return render(request, 'signin.html',
                    {'form': AuthenticationForm
                    })
    else:
        user = authenticate(
            request, username=request.POST['username'], password=request.POST['password'])
        if user is None:
            return render(request, 'signin.html',
                    {'form': AuthenticationForm,
                     'error': 'Usuario o Contraseña incorrecta'
                    })
        else:
            login(request, user)
            return redirect('main')

#Asi se hacen todos        
def create_cliente(request):

    if request.method == 'GET':
        return render(request, 'cliente.html', {
            'form': ClienteForm
        })
    else:
        try:
            form = ClienteForm(request.POST)
            new_cliente = form.save(commit=False)
            new_cliente.usuario =request.user
            new_cliente.save()
            return redirect('main')
        except ValueError:
            return render(request, 'cliente.html', {
                'form': ClienteForm,
                'error': 'Ingrese valores validos'
            })


#Continuamos la logica
@login_required(login_url='signin')
def main(request):
    # 1. Diccionario de días
    dias_semana = dict(DisponibilidadPlato.DIAS_SEMANA)

    # 2. Día actual (por defecto LUN) y grupo (por defecto todos)
    dia_actual = request.GET.get('dia', 'LUN')
    grupo_actual = request.GET.get('grupo', '')

    # 3. POST → Agregar al carrito
    if request.method == 'POST':
        plato_id   = request.POST.get('plato_id')
        cantidad   = int(request.POST.get('cantidad', 1))
        dia_semana = request.POST.get('dia_semana', dia_actual)

        plato = get_object_or_404(Plato, id=plato_id)

        item, creado = CarritoItem.objects.get_or_create(
            usuario=request.user,
            plato=plato,
            dia_semana=dia_semana,
            defaults={'cantidad': cantidad}
        )
        if not creado:
            item.cantidad = F('cantidad') + cantidad
            item.save()

        return redirect(f"{request.path}?dia={dia_actual}&grupo={grupo_actual}")

    # 4. Obtener platos disponibles para el día (OPTIMIZADO)
    disponibles = DisponibilidadPlato.objects.filter(
        dia=dia_actual
    ).select_related('plato')

    if grupo_actual:
        disponibles = disponibles.filter(plato__grupo=grupo_actual)

    # 5. Obtener carrito del usuario (OPTIMIZADO)
    carrito_items = CarritoItem.objects.filter(
        usuario=request.user
    ).select_related('plato', 'usuario')
    
    # Usar agregación para calcular el total más eficientemente
    from django.db.models import Sum, F
    total_carrito = CarritoItem.objects.filter(
        usuario=request.user
    ).aggregate(
        total=Sum(F('cantidad') * F('plato__precio'))
    )['total'] or 0

    # 6. Grupos únicos ordenados (OPTIMIZADO con cache)
    from django.core.cache import cache
    grupos = cache.get('platos_grupos')
    if grupos is None:
        grupos = sorted(set(Plato.objects.values_list('grupo', flat=True)))
        cache.set('platos_grupos', grupos, 3600)  # Cache por 1 hora

    return render(request, 'main.html', {
        'dias_semana': dias_semana,
        'dia_actual': dia_actual,
        'dia_actual_nombre': dias_semana.get(dia_actual, ''),
        'disponibles': disponibles,
        'carrito_items': carrito_items,
        'total_carrito': total_carrito,
        'grupo_actual': grupo_actual,
        'grupos': grupos,
    })

# ----------PAGO------------
@login_required(login_url='signin')
def pago(request):
    recibo_id = request.session.get('recibo_id')

    if not recibo_id:
        messages.error(request, "No se encontró ningún recibo.")
        return redirect('main')

    recibo = get_object_or_404(Recibo, id=recibo_id, usuario=request.user)
    items = ReciboItem.objects.filter(recibo=recibo)

    return render(request, 'pago.html', {
        'recibo': recibo,
        'items': items,
    })

# ---------REDIRIGIR A PAGO -------
@login_required
def procesar_pago(request):
    recibo_id = request.session.get('recibo_id')
    if not recibo_id:
        messages.error(request, "No se encontró ningún recibo.")
        return redirect('main')

    recibo = get_object_or_404(Recibo, id=recibo_id, usuario=request.user)
    order = str(recibo.id)
    amount = str(int(recibo.total * 100))  # en céntimos

    # Construir la firma (signature)
    signature_string = (
        settings.PAYCOMET_CLIENT_CODE +
        settings.PAYCOMET_TERMINAL +
        order +
        amount +
        settings.PAYCOMET_CURRENCY +
        settings.PAYCOMET_PASSWORD
    )
    signature = hashlib.sha512(signature_string.encode('utf-8')).hexdigest().upper()

    # Guardar datos opcionales en el recibo
    recibo.referencia_pago = order
    recibo.save()

    context = {
        "MERCHANT_MERCHANTCODE": settings.PAYCOMET_CLIENT_CODE,
        "MERCHANT_TERMINAL": settings.PAYCOMET_TERMINAL,
        "MERCHANT_ORDER": order,
        "MERCHANT_AMOUNT": amount,
        "MERCHANT_CURRENCY": settings.PAYCOMET_CURRENCY,
        "MERCHANT_SIGNATURE": signature,
        "URLOK": request.build_absolute_uri(reverse('pago_exitoso')),
        "URLKO": request.build_absolute_uri(reverse('pago_fallido')),
        "LANGUAGE": settings.PAYCOMET_LANGUAGE,
    }

    return render(request, "formulario_pago_terminal.html", context)

#---------VISTAS DE ÉXITO Y FALLO------
@login_required
def pago_exitoso(request):
    recibo_id = request.session.get('recibo_id')

    if recibo_id:
        recibo = Recibo.objects.filter(id=recibo_id, usuario=request.user).first()
        if recibo and not recibo.pagado:
            recibo.pagado = True
            recibo.fecha_pago = timezone.now()
            recibo.estado_pago = 'completado'
            recibo.metodo_pago = 'Paycomet Terminal'
            recibo.save()

    messages.success(request, "Pago realizado con éxito.")
    return render(request, 'pago_exitoso.html')

@login_required
def pago_fallido(request):
    recibo_id = request.session.get('recibo_id')

    if recibo_id:
        recibo = Recibo.objects.filter(id=recibo_id, usuario=request.user).first()
        if recibo and not recibo.pagado:
            recibo.estado_pago = 'fallido'
            recibo.save()

    messages.error(request, "El pago fue cancelado o falló.")
    return render(request, 'pago_fallido.html')

#----- Eliminar_seleccion -----

@login_required(login_url='signin')
@require_POST
def eliminar_carrito_item(request, item_id):
    item = get_object_or_404(CarritoItem, id=item_id, usuario=request.user)
    item.delete()
    return redirect('main')


# Prueba
@login_required
@transaction.atomic
def procesar_pago(request):
    usuario = request.user
    carrito_items = CarritoItem.objects.filter(usuario=usuario)

    if not carrito_items.exists():
        messages.warning(request, "Tu carrito está vacío.")
        return redirect('main')

    total = sum(item.plato.precio * item.cantidad for item in carrito_items)

    try:
        cliente = Cliente.objects.get(usuario=usuario)
        empresa = cliente.empresa
    except Cliente.DoesNotExist:
        empresa = None

    recibo = Recibo.objects.create(
        usuario=usuario,
        empresa=empresa,
        total=total
    )

    for item in carrito_items:
        ReciboItem.objects.create(
            recibo=recibo,
            plato=item.plato,
            cantidad=item.cantidad,
            precio_unitario=item.plato.precio
        )

    # Aquí creamos los registros en PedidoHistorico sin pasar fecha_emision
    historico_items = [
        PedidoHistorico(
            usuario=item.usuario,
            plato=item.plato,
            cantidad=item.cantidad,
            dia_semana=item.dia_semana
        ) for item in carrito_items
    ]
    PedidoHistorico.objects.bulk_create(historico_items)

    carrito_items.delete()

    request.session['recibo_id'] = recibo.id

    return redirect('pago')

def design_demo(request):
    """Vista para mostrar el diseño corporativo actualizado"""
    from .models import Plato, DisponibilidadPlato, Cliente, Recibo
    from datetime import date
    
    # Obtener datos de muestra
    context = {
        'platos_count': Plato.objects.count(),
        'disponibilidades_count': DisponibilidadPlato.objects.count(),
        'clientes_count': Cliente.objects.count(),
        'pedidos_hoy': Recibo.objects.filter(fecha_compra__date=date.today()).count(),
        'platos_sample': Plato.objects.all()[:6],
        'disponibilidades_sample': DisponibilidadPlato.objects.select_related('plato')[:8]
    }
    
    return render(request, 'design_demo.html', context)

def test_admin_links(request):
    """Vista para probar que los enlaces del admin funcionan"""
    from django.urls import reverse
    from .models import DisponibilidadPlato
    
    # Obtener algunas disponibilidades para probar
    disponibilidades = DisponibilidadPlato.objects.all()[:5]
    
    test_data = []
    for disp in disponibilidades:
        try:
            edit_url = reverse('admin:myapp_disponibilidadplato_change', args=[disp.id])
            test_data.append({
                'id': disp.id,
                'plato': disp.plato.nombre,
                'dia': disp.get_dia_display(),
                'edit_url': edit_url,
                'full_url': f'http://localhost:8000{edit_url}'
            })
        except Exception as e:
            test_data.append({
                'id': disp.id,
                'plato': disp.plato.nombre,
                'dia': disp.get_dia_display(),
                'error': str(e)
            })
    
    return render(request, 'test_admin_links.html', {'test_data': test_data})

def admin_test(request):
    """Vista de diagnóstico para verificar el funcionamiento del admin"""
    from django.contrib.admin.sites import site
    from .models import DisponibilidadPlato, Plato
    
    # Información de diagnóstico
    diagnostics = {
        'total_platos': Plato.objects.count(),
        'total_disponibilidades': DisponibilidadPlato.objects.count(),
        'platos_con_imagen': Plato.objects.exclude(imagen__isnull=True).exclude(imagen__exact='').count(),
        'admin_registered_models': len(site._registry),
        'disponibilidades_por_dia': {}
    }
    
    # Disponibilidades por día
    for dia_code, dia_name in DisponibilidadPlato.DIAS_SEMANA:
        count = DisponibilidadPlato.objects.filter(dia=dia_code).count()
        diagnostics['disponibilidades_por_dia'][dia_name] = count
    
    return render(request, 'admin_test.html', {'diagnostics': diagnostics})

def test_images(request):
    """Vista de prueba para verificar que las imágenes funcionan"""
    platos = Plato.objects.all()
    return render(request, 'test_images.html', {'platos': platos})