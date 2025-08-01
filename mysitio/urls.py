"""
URL configuration for mysitio project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import path, include
from myapp import views
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from myapp.api_views import PlatoViewSet, ClienteViewSet, CarritoViewSet, ReciboViewSet, DashboardViewSet

# Router para la API
router = DefaultRouter()
router.register(r'platos', PlatoViewSet)
router.register(r'clientes', ClienteViewSet)
router.register(r'carrito', CarritoViewSet, basename='carrito')
router.register(r'recibos', ReciboViewSet, basename='recibo')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('', views.helloword, name='home'),
    path('singup/', views.register),
    path('main/', views.main, name='main'),  # ✅ Esta es la buena
    path('logout/', views.signout, name='logout'),
    path('signin/', views.signin, name='signin'),
    path('info/', views.create_cliente, name='create_cliente'),
    path('procesar-pago/', views.procesar_pago, name='procesar_pago'),
    path('pago-exitoso/', views.pago_exitoso, name='pago_exitoso'),
    path('pago-fallido/', views.pago_fallido, name='pago_fallido'),
    path('pago/', views.pago, name='pago'),
    path('eliminar-item/<int:item_id>/', views.eliminar_carrito_item, name='eliminar_item'),
] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
