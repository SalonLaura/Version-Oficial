from django.urls import path
from .views import (RecibirTurnoView, TransferenciasView,IpvView,EntregarTurnoView)

urlpatterns = [
    path('recibir-turno/', RecibirTurnoView.as_view(),name='RecibirTurnoTrabajador'),
    path('transferencias-w/', TransferenciasView.as_view(),name='TransferenciasTrabajador'),
    path('ipv/', IpvView.as_view(),name='IpvTrabajador'),
    path('entregar-turno/', EntregarTurnoView.as_view(),name='EntregarTurnoTrabajador'),
]