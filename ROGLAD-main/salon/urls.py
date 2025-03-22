from django.urls import path
from .views import (RecibirTurnoView,ServiciosView,SubproductosView,TurnosView,
                    ClientesView,ClientesAtendidosView,ConsumoView,TransferenciasView,
                    EntregarTurnoView,GestionTurnosView)

urlpatterns = [
    path('recibir-ipv', RecibirTurnoView.as_view(),name='RecibirTurnoSalon'),
    path('consumo',ConsumoView.as_view(),name='ConsumoSalon'),
    path('servicios',ServiciosView.as_view(),name='ServiciosSalon'),
    path('subproductos',SubproductosView.as_view(),name='SubproductosSalon'),
    path('turnos',TurnosView.as_view(),name='TurnosSalon'),
    path('gestion-turnos',GestionTurnosView.as_view(),name='GestionTurnosSalon'),
    path('clientes-turnos',ClientesView.as_view(),name='ClientesSalon'),
    
    path('clientes-atendidos',ClientesAtendidosView.as_view(),name='ClientesAtendidosSalon'),

    path('transferencias',TransferenciasView.as_view(),name='TransferenciaSalon'),
    path('entregar-turno',EntregarTurnoView.as_view(),name='EntregarTurnoSalon'),
    
]