from django.urls import path
from .views import (OperacionesView,ReciboEfectivoView,HistorialReciboView,SalariosView,EstadoLiquidesView,CrearPrenominaView,EstadoCapitalView)

urlpatterns = [
    path('operaciones', OperacionesView.as_view(),name='OperacionesCaja'),
    path('recibo-efectivo', ReciboEfectivoView.as_view(),name='ReciboEfectivoCaja'),
    path('historial-recibo', HistorialReciboView.as_view(),name='HistorialRecepcionCaja'),
    path('salarios', SalariosView.as_view(),name='SalariosCaja'),
    path('estado-liquides/', EstadoLiquidesView.as_view(),name='EstadoLiquides'),
    path('estado-capital/', EstadoCapitalView.as_view(),name='EstadoCapital'),
    path('crear-prenomina/', CrearPrenominaView.as_view(),name='CrearPrenomina'),
]