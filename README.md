# 🍽️ Familia Gastro - Plataforma de Comercialización de Platos Preparados

Una aplicación web moderna y completa desarrollada en Django para la comercialización de platos preparados, orientada tanto a clientes particulares como empresariales.

## 🚀 Características Principales

### 🛒 **E-commerce Completo**
- Sistema de carrito de compras inteligente
- Gestión de disponibilidad por días de la semana
- Procesamiento de pagos integrado con PAYCOMET
- Soporte para clientes particulares y empresariales

### 🎨 **Interfaz Moderna**
- Diseño responsivo con Bootstrap 5
- Interfaz intuitiva y atractiva
- Filtros dinámicos por categorías
- Modales informativos para cada plato

### 🔧 **API REST Completa**
- Endpoints para todas las funcionalidades
- Autenticación y autorización robusta
- Documentación automática
- Rate limiting implementado

### 🛡️ **Seguridad Avanzada**
- Headers de seguridad configurados
- Autenticación de sesiones segura
- Validación de datos exhaustiva
- Configuración HTTPS lista para producción

### 📊 **Panel Administrativo**
- Dashboard con estadísticas
- Gestión completa de platos y disponibilidad
- Exportación de datos a Excel
- Sistema de logs detallado

## 🏗️ Arquitectura

```
familia-gastro/
├── myapp/                  # Aplicación principal
│   ├── models.py          # Modelos de datos
│   ├── views.py           # Vistas y lógica de negocio
│   ├── api_views.py       # API REST endpoints
│   ├── forms.py           # Formularios
│   ├── admin.py           # Configuración del admin
│   ├── serializers.py     # Serializadores API
│   ├── tests.py           # Tests unitarios
│   ├── management/        # Comandos personalizados
│   └── static/            # Archivos estáticos
├── mysitio/               # Configuración del proyecto
│   ├── settings.py        # Configuración mejorada
│   └── urls.py            # URLs principales
├── templates/             # Plantillas HTML
├── logs/                  # Archivos de log
├── Dockerfile             # Configuración Docker
├── docker-compose.yml     # Orquestación de servicios
├── nginx.conf            # Configuración Nginx
└── requirements.txt       # Dependencias
```

## 🛠️ Tecnologías Utilizadas

### Backend
- **Django 5.2.1** - Framework web principal
- **Django REST Framework** - API REST
- **PostgreSQL/SQL Server** - Base de datos
- **Redis** - Cache y sesiones
- **Gunicorn** - Servidor WSGI

### Frontend
- **Bootstrap 5.3.6** - Framework CSS
- **JavaScript ES6+** - Interactividad
- **Fuentes Google** - Tipografía moderna

### DevOps
- **Docker & Docker Compose** - Containerización
- **Nginx** - Proxy reverso y archivos estáticos
- **GitHub Actions** - CI/CD (configuración incluida)

## 📦 Instalación y Configuración

### 🐳 Instalación con Docker (Recomendado)

1. **Clonar el repositorio**
   ```bash
   git clone <repository-url>
   cd familia-gastro
   ```

2. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con tus configuraciones
   ```

3. **Levantar los servicios**
   ```bash
   docker-compose up -d
   ```

4. **Configurar la aplicación**
   ```bash
   docker-compose exec web python manage.py setup_production --create-superuser --load-sample-data
   ```

### 🐍 Instalación Manual

1. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # o
   venv\Scripts\activate     # Windows
   ```

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar base de datos**
   ```bash
   python manage.py migrate
   ```

4. **Crear superusuario**
   ```bash
   python manage.py createsuperuser
   ```

5. **Ejecutar servidor de desarrollo**
   ```bash
   python manage.py runserver
   ```

## 🔧 Configuración de Producción

### Variables de Entorno Principales

```env
# Seguridad
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com

# Base de datos
DB_ENGINE=django.db.backends.postgresql
DB_NAME=familia_gastro
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Cache
CACHE_BACKEND=django.core.cache.backends.redis.RedisCache
CACHE_LOCATION=redis://127.0.0.1:6379/1

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Pagos
PAYCOMET_CLIENT_CODE=your-client-code
PAYCOMET_TERMINAL=your-terminal
PAYCOMET_PASSWORD=your-password
```

## 🧪 Testing

Ejecutar todos los tests:
```bash
python manage.py test
```

Ejecutar tests con coverage:
```bash
coverage run --source='.' manage.py test
coverage report
coverage html
```

## 📊 Comandos Personalizados

### Configuración de Producción
```bash
python manage.py setup_production --create-superuser --load-sample-data --generate-secret-key
```

### Generar SECRET_KEY
```bash
python manage.py setup_production --generate-secret-key
```

## 🔍 Monitoreo y Logs

Los logs se almacenan en:
- `logs/familia_gastro.log` - Log principal
- `logs/security.log` - Log de seguridad

Configuración de log rotation incluida.

## 🚀 Deployment

### Con Docker Compose
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Con Nginx
La configuración de Nginx está incluida en `nginx.conf` con:
- Compresión gzip
- Headers de seguridad
- Cache de archivos estáticos
- Configuración SSL lista

## 🔒 Seguridad

### Características Implementadas
- ✅ Headers de seguridad (HSTS, CSP, etc.)
- ✅ Configuración HTTPS
- ✅ Validación de entrada
- ✅ Rate limiting en API
- ✅ Logs de seguridad
- ✅ Usuario no-root en Docker
- ✅ Secrets management

### Recomendaciones Adicionales
- Configurar firewall
- Implementar backups automáticos
- Monitoreo de recursos
- Actualizaciones regulares

## 📈 Performance

### Optimizaciones Implementadas
- ✅ Query optimization con select_related/prefetch_related
- ✅ Cache de datos frecuentes
- ✅ Compresión de archivos estáticos
- ✅ Connection pooling
- ✅ Lazy loading de imágenes

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 📞 Soporte

Para soporte técnico o consultas:
- 📧 Email: admin@familagastro.com
- 📱 Teléfono: +34 XXX XXX XXX
- 🌐 Web: https://familagastro.com

---

**Desarrollado con ❤️ para Familia Gastro**
