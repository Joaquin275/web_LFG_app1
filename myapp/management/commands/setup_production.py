"""
Comando personalizado para configurar el entorno de producción
Uso: python manage.py setup_production
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.contrib.auth.models import User
from django.db import transaction
from myapp.models import Empresa, Cliente
import os
import secrets
import string


class Command(BaseCommand):
    help = 'Configura el entorno de producción de Familia Gastro'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-superuser',
            action='store_true',
            help='Crear usuario administrador',
        )
        parser.add_argument(
            '--load-sample-data',
            action='store_true',
            help='Cargar datos de ejemplo',
        )
        parser.add_argument(
            '--generate-secret-key',
            action='store_true',
            help='Generar nueva SECRET_KEY',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Configurando Familia Gastro para producción...\n')
        )

        try:
            # 1. Ejecutar migraciones
            self.stdout.write('📦 Ejecutando migraciones...')
            call_command('migrate', verbosity=0)
            self.stdout.write(self.style.SUCCESS('✅ Migraciones completadas\n'))

            # 2. Recopilar archivos estáticos
            self.stdout.write('📁 Recopilando archivos estáticos...')
            call_command('collectstatic', '--noinput', verbosity=0)
            self.stdout.write(self.style.SUCCESS('✅ Archivos estáticos recopilados\n'))

            # 3. Generar SECRET_KEY si se solicita
            if options['generate_secret_key']:
                self.generate_secret_key()

            # 4. Crear superusuario si se solicita
            if options['create_superuser']:
                self.create_superuser()

            # 5. Cargar datos de ejemplo si se solicita
            if options['load_sample_data']:
                self.load_sample_data()

            # 6. Verificar configuración
            self.verify_configuration()

            self.stdout.write(
                self.style.SUCCESS('\n🎉 ¡Configuración de producción completada!')
            )
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  Recuerda:\n'
                    '   - Configurar las variables de entorno en .env\n'
                    '   - Configurar el servidor web (Nginx)\n'
                    '   - Configurar SSL/TLS para HTTPS\n'
                    '   - Configurar backups de la base de datos\n'
                )
            )

        except Exception as e:
            raise CommandError(f'Error durante la configuración: {str(e)}')

    def generate_secret_key(self):
        """Genera una nueva SECRET_KEY segura"""
        self.stdout.write('🔐 Generando nueva SECRET_KEY...')
        
        # Generar clave segura
        alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
        secret_key = ''.join(secrets.choice(alphabet) for _ in range(50))
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Nueva SECRET_KEY generada:\n'
                f'SECRET_KEY={secret_key}\n'
                f'⚠️  Guarda esta clave en tu archivo .env\n'
            )
        )

    def create_superuser(self):
        """Crear usuario administrador"""
        self.stdout.write('👤 Creando usuario administrador...')
        
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(
                self.style.WARNING('⚠️  Ya existe un superusuario')
            )
            return

        try:
            username = input('Nombre de usuario: ')
            email = input('Email: ')
            
            if not username or not email:
                self.stdout.write(
                    self.style.ERROR('❌ Nombre de usuario y email son requeridos')
                )
                return

            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=None  # Se pedirá interactivamente
            )
            
            # Crear cliente asociado
            Cliente.objects.create(
                Nombre_Completo=f'Admin {username}',
                usuario=user,
                es_particular=True,
                correo=email
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Superusuario {username} creado correctamente')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creando superusuario: {str(e)}')
            )

    def load_sample_data(self):
        """Cargar datos de ejemplo"""
        self.stdout.write('📊 Cargando datos de ejemplo...')
        
        try:
            with transaction.atomic():
                # Crear empresas de ejemplo
                empresas_ejemplo = [
                    {
                        'codigo': 'EMP001',
                        'nombre': 'Restaurante El Buen Sabor',
                        'direccion': 'Calle Mayor 123, Madrid',
                        'cif': 'B12345678'
                    },
                    {
                        'codigo': 'EMP002',
                        'nombre': 'Catering Delicious',
                        'direccion': 'Avenida Principal 456, Barcelona',
                        'cif': 'B87654321'
                    }
                ]
                
                for empresa_data in empresas_ejemplo:
                    empresa, created = Empresa.objects.get_or_create(
                        codigo=empresa_data['codigo'],
                        defaults=empresa_data
                    )
                    if created:
                        self.stdout.write(f'  ✅ Empresa creada: {empresa.nombre}')
                
                self.stdout.write(
                    self.style.SUCCESS('✅ Datos de ejemplo cargados correctamente\n')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error cargando datos: {str(e)}')
            )

    def verify_configuration(self):
        """Verificar configuración del sistema"""
        self.stdout.write('🔍 Verificando configuración...')
        
        from django.conf import settings
        
        checks = [
            ('DEBUG', not settings.DEBUG, 'DEBUG debe estar en False para producción'),
            ('SECRET_KEY', len(settings.SECRET_KEY) > 20, 'SECRET_KEY debe ser segura'),
            ('ALLOWED_HOSTS', len(settings.ALLOWED_HOSTS) > 0, 'ALLOWED_HOSTS debe estar configurado'),
            ('Database', 'sqlite' not in settings.DATABASES['default']['ENGINE'], 'Usar base de datos de producción'),
        ]
        
        all_good = True
        for name, condition, message in checks:
            if condition:
                self.stdout.write(f'  ✅ {name}: OK')
            else:
                self.stdout.write(f'  ❌ {name}: {message}')
                all_good = False
        
        if all_good:
            self.stdout.write(
                self.style.SUCCESS('✅ Todas las verificaciones pasaron\n')
            )
        else:
            self.stdout.write(
                self.style.WARNING('⚠️  Algunas verificaciones fallaron\n')
            )