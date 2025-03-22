import re
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.static import static, serve
from django.contrib.auth import views as auth_views

from django.conf.urls import  handler500 #handler404,
#from bussiness.views import ErrorView

from django.conf import settings

def staticProduction(prefix, view=serve, **kwargs):
    if settings.DEBUG:
        return []
    return []
    print([
        re_path(r'^%s(?P<path>.*)$' % re.escape(prefix.lstrip('/')), view, kwargs=kwargs),
    ]) 


urlpatterns = [
    #Ruta del admin de django
    path('admin/', admin.site.urls),

    #Ruta Principal del Sistema
    #path('', include('roglad.urls')),

    #Rutas del sietema Salon Laura
    #path('roglad/bussiness/', include('bussiness.urls')),
    path('', include('bussiness.urls')),
    path('remote-control/', include('bot.urls')),
    path('cocina/', include('kitchen.urls')),
    path('estudio/', include('estudio.urls')),
    path('almacen/', include('almacen.urls')),
    path('caja/', include('caja.urls')),
    path('salon/', include('salon.urls')),
    path('w/', include('otherworkers.urls')),   

    #Ruta Para Negocio de Punto de Venta
    #path('', include('punto_venta.urls')),
    


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += staticProduction(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


#handler404 = ErrorView.as_view()
#handler500 = ErrorView.as_view()