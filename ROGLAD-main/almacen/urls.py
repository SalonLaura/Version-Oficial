from django.urls import path
from .views import (RecibirTurnoView,EntregarTurnoView)

urlpatterns = [
    path('recibir/', RecibirTurnoView.as_view(),name='RecibirTurnoAlmacen'),
    path('entregar/', EntregarTurnoView.as_view(),name='EntregarTurnoAlmacen'),

]