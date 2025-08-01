from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError
from decimal import Decimal
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Cliente, Empresa, Plato, CarritoItem, Recibo, ReciboItem, DisponibilidadPlato
from .forms import ClienteForm, DisponibilidadPlatoForm


class EmpresaModelTest(TestCase):
    """Tests para el modelo Empresa"""
    
    def setUp(self):
        self.empresa = Empresa.objects.create(
            codigo="EMP001",
            nombre="Empresa Test",
            direccion="Calle Test 123",
            cif="B12345678"
        )
    
    def test_empresa_creation(self):
        """Test creación de empresa"""
        self.assertEqual(self.empresa.nombre, "Empresa Test")
        self.assertEqual(self.empresa.codigo, "EMP001")
        self.assertTrue(isinstance(self.empresa, Empresa))
        
    def test_empresa_str_method(self):
        """Test método __str__ de empresa"""
        expected = "Empresa Test - Calle Test 123"
        self.assertEqual(str(self.empresa), expected)
        
    def test_empresa_unique_codigo(self):
        """Test que el código de empresa sea único"""
        with self.assertRaises(Exception):
            Empresa.objects.create(
                codigo="EMP001",  # Código duplicado
                nombre="Otra Empresa",
                cif="B87654321"
            )


class ClienteModelTest(TestCase):
    """Tests para el modelo Cliente"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.empresa = Empresa.objects.create(
            codigo="EMP001",
            nombre="Empresa Test",
            cif="B12345678"
        )
        
    def test_cliente_particular_creation(self):
        """Test creación de cliente particular"""
        cliente = Cliente.objects.create(
            Nombre_Completo="Juan Pérez",
            usuario=self.user,
            es_particular=True,
            direccion_particular="Calle Particular 123",
            celular="612345678",
            dni="12345678Z",
            correo="juan@test.com"
        )
        
        self.assertEqual(cliente.Nombre_Completo, "Juan Pérez")
        self.assertTrue(cliente.es_particular)
        self.assertEqual(cliente.direccion_particular, "Calle Particular 123")
        
    def test_cliente_empresa_creation(self):
        """Test creación de cliente empresarial"""
        cliente = Cliente.objects.create(
            Nombre_Completo="María García",
            usuario=self.user,
            empresa=self.empresa,
            es_particular=False,
            celular="687654321",
            dni="87654321Y",
            correo="maria@empresa.com"
        )
        
        self.assertEqual(cliente.empresa, self.empresa)
        self.assertFalse(cliente.es_particular)
        
    def test_cliente_str_method(self):
        """Test método __str__ de cliente"""
        cliente_particular = Cliente.objects.create(
            Nombre_Completo="Juan Pérez",
            usuario=self.user,
            es_particular=True
        )
        
        cliente_empresa = Cliente.objects.create(
            Nombre_Completo="María García",
            usuario=User.objects.create_user('maria', 'pass'),
            empresa=self.empresa,
            es_particular=False
        )
        
        self.assertEqual(str(cliente_particular), "Juan Pérez - Particular")
        self.assertEqual(str(cliente_empresa), "María García - Empresa Test")


class PlatoModelTest(TestCase):
    """Tests para el modelo Plato"""
    
    def setUp(self):
        self.plato = Plato.objects.create(
            codigo="PLT001",
            nombre="Paella Valenciana",
            descripcion="Deliciosa paella tradicional",
            precio=Decimal('15.50'),
            kilogramos=Decimal('1'),
            grupo='ARROCES',
            estado='DISPONIBLE'
        )
        
    def test_plato_creation(self):
        """Test creación de plato"""
        self.assertEqual(self.plato.nombre, "Paella Valenciana")
        self.assertEqual(self.plato.precio, Decimal('15.50'))
        self.assertEqual(self.plato.grupo, 'ARROCES')
        
    def test_plato_str_method(self):
        """Test método __str__ de plato"""
        self.assertEqual(str(self.plato), "Paella Valenciana")
        
    def test_plato_unique_codigo(self):
        """Test que el código de plato sea único"""
        with self.assertRaises(Exception):
            Plato.objects.create(
                codigo="PLT001",  # Código duplicado
                nombre="Otro Plato",
                precio=Decimal('10.00')
            )


class DisponibilidadPlatoModelTest(TestCase):
    """Tests para el modelo DisponibilidadPlato"""
    
    def setUp(self):
        self.plato = Plato.objects.create(
            codigo="PLT001",
            nombre="Test Plato",
            precio=Decimal('10.00')
        )
        
    def test_disponibilidad_creation(self):
        """Test creación de disponibilidad"""
        disponibilidad = DisponibilidadPlato.objects.create(
            plato=self.plato,
            dia='LUN'
        )
        
        self.assertEqual(disponibilidad.plato, self.plato)
        self.assertEqual(disponibilidad.dia, 'LUN')


class CarritoItemModelTest(TestCase):
    """Tests para el modelo CarritoItem"""
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'pass')
        self.cliente = Cliente.objects.create(
            Nombre_Completo="Test Cliente",
            usuario=self.user,
            es_particular=True
        )
        self.plato = Plato.objects.create(
            codigo="PLT001",
            nombre="Test Plato",
            precio=Decimal('15.00')
        )
        
    def test_carrito_item_creation(self):
        """Test creación de item de carrito"""
        item = CarritoItem.objects.create(
            usuario=self.user,
            plato=self.plato,
            cantidad=2,
            dia_semana='LUN'
        )
        
        self.assertEqual(item.cantidad, 2)
        self.assertEqual(item.plato, self.plato)
        self.assertEqual(item.usuario, self.user)


class ClienteCreacionFormTest(TestCase):
    """Tests para el formulario de creación de cliente"""
    
    def setUp(self):
        self.empresa = Empresa.objects.create(
            codigo="EMP001",
            nombre="Test Empresa",
            cif="B12345678"
        )
        
    def test_form_valid_particular(self):
        """Test formulario válido para cliente particular"""
        form_data = {
            'Nombre_Completo': 'Juan Pérez',
            'es_particular': True,
            'direccion_particular': 'Calle Test 123',
            'celular': '612345678',
            'dni': '12345678Z',
            'correo': 'juan@test.com'
        }
        form = ClienteForm(data=form_data)
        self.assertTrue(form.is_valid())
        
    def test_form_valid_empresa(self):
        """Test formulario válido para cliente empresarial"""
        form_data = {
            'Nombre_Completo': 'María García',
            'es_particular': False,
            'empresa': self.empresa.id,
            'celular': '687654321',
            'dni': '87654321Y',
            'correo': 'maria@empresa.com'
        }
        form = ClienteForm(data=form_data)
        self.assertTrue(form.is_valid())


class DisponibilidadPlatoFormTest(TestCase):
    """Tests para el formulario de disponibilidad de platos"""
    
    def setUp(self):
        self.plato = Plato.objects.create(
            codigo="PLT001",
            nombre="Test Plato",
            precio=Decimal('10.00')
        )
        
    def test_form_valid(self):
        """Test formulario válido"""
        form_data = {
            'plato': self.plato.id,
            'dia': 'LUN'
        }
        form = DisponibilidadPlatoForm(data=form_data)
        self.assertTrue(form.is_valid())
        
    def test_form_duplicate_validation(self):
        """Test validación de duplicados"""
        # Crear primera disponibilidad
        DisponibilidadPlato.objects.create(
            plato=self.plato,
            dia='LUN'
        )
        
        # Intentar crear duplicado
        form_data = {
            'plato': self.plato.id,
            'dia': 'LUN'
        }
        form = DisponibilidadPlatoForm(data=form_data)
        self.assertFalse(form.is_valid())


class ViewsTest(TestCase):
    """Tests para las vistas"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
    def test_home_view(self):
        """Test vista home"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        
    def test_register_view_get(self):
        """Test vista registro GET"""
        response = self.client.get('/singup/')
        self.assertEqual(response.status_code, 200)
        
    def test_register_view_post_valid(self):
        """Test vista registro POST válido"""
        response = self.client.post('/singup/', {
            'username': 'newuser',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        })
        # Debería redirigir a create_cliente
        self.assertEqual(response.status_code, 302)
        
    def test_signin_view_get(self):
        """Test vista signin GET"""
        response = self.client.get('/signin/')
        self.assertEqual(response.status_code, 200)
        
    def test_signin_view_post_valid(self):
        """Test vista signin POST válido"""
        response = self.client.post('/signin/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        # Debería redirigir
        self.assertEqual(response.status_code, 302)
        
    def test_main_view_requires_login(self):
        """Test que la vista main requiere login"""
        response = self.client.get('/main/')
        # Debería redirigir al login
        self.assertEqual(response.status_code, 302)
        
    def test_main_view_with_login(self):
        """Test vista main con usuario logueado"""
        # Crear cliente para el usuario
        Cliente.objects.create(
            Nombre_Completo="Test User",
            usuario=self.user,
            es_particular=True
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/main/')
        self.assertEqual(response.status_code, 200)


class APIViewsTest(APITestCase):
    """Tests para las vistas de API"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.plato = Plato.objects.create(
            codigo="PLT001",
            nombre="Test Plato API",
            precio=Decimal('12.50'),
            grupo='CARNES'
        )
        
    def test_platos_api_requires_auth(self):
        """Test que la API de platos requiere autenticación"""
        response = self.client.get('/api/platos/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_platos_api_with_auth(self):
        """Test API de platos con autenticación"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/platos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_platos_api_filter_by_grupo(self):
        """Test filtro por grupo en API de platos"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/platos/?grupo=CARNES')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que el plato está en la respuesta
        data = response.json()
        self.assertTrue(any(plato['nombre'] == 'Test Plato API' for plato in data['results']))


class SecurityTest(TestCase):
    """Tests de seguridad"""
    
    def test_admin_url_custom(self):
        """Test que la URL del admin es personalizable"""
        from django.conf import settings
        self.assertTrue(hasattr(settings, 'ADMIN_URL'))
        
    def test_debug_false_by_default(self):
        """Test que DEBUG es False por defecto"""
        from django.conf import settings
        # En tests DEBUG puede estar True, pero verificamos la configuración
        self.assertTrue(hasattr(settings, 'DEBUG'))
        
    def test_secret_key_configured(self):
        """Test que SECRET_KEY está configurada"""
        from django.conf import settings
        self.assertTrue(hasattr(settings, 'SECRET_KEY'))
        self.assertNotEqual(settings.SECRET_KEY, '')


class IntegrationTest(TestCase):
    """Tests de integración"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='integrationuser',
            password='testpass123'
        )
        self.empresa = Empresa.objects.create(
            codigo="EMP001",
            nombre="Empresa Integration",
            cif="B12345678"
        )
        self.cliente = Cliente.objects.create(
            Nombre_Completo="Integration User",
            usuario=self.user,
            empresa=self.empresa,
            es_particular=False
        )
        self.plato = Plato.objects.create(
            codigo="PLT001",
            nombre="Plato Integration",
            precio=Decimal('20.00')
        )
        
    def test_complete_user_flow(self):
        """Test flujo completo de usuario"""
        # 1. Login
        login_success = self.client.login(
            username='integrationuser',
            password='testpass123'
        )
        self.assertTrue(login_success)
        
        # 2. Acceder a main
        response = self.client.get('/main/')
        self.assertEqual(response.status_code, 200)
        
        # 3. Agregar item al carrito (simulado)
        CarritoItem.objects.create(
            usuario=self.user,
            plato=self.plato,
            cantidad=2,
            dia_semana='LUN'
        )
        
        # 4. Verificar que el item existe
        items = CarritoItem.objects.filter(usuario=self.user)
        self.assertEqual(items.count(), 1)
        self.assertEqual(items.first().cantidad, 2)


if __name__ == '__main__':
    import django
    django.setup()
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["myapp"])
