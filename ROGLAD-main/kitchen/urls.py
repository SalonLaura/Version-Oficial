from django.urls import path
from .views import (HistorialView, SolicitudesView,ResumenTurnoView,StockView,FormulasView,TransferenciasView,MediosBasicos,RecetasView,
                    NuevaTransferenciaView,RecibirTurnoView,RecibirTurnoInventarioView, RecibirTurnoUtilesView, EntregarTurnoView,NuevaFormulaView,NotasCocinaView, getNotificacionCocina,
                    AddAyudantes)

urlpatterns = [
    path('medios-basicos', MediosBasicos.as_view(),name='MediosBasicosCocina'),
    path('stock', StockView.as_view(),name='StockCocina'),
    path('solicitudes', SolicitudesView.as_view(),name='SolicitudesCocina'),
    path('formulas', FormulasView.as_view(),name='FormulasCocina'),
    path('recetas', RecetasView.as_view(),name='RecetasCocina'),
    path('historial-elaboracion/', HistorialView.as_view(),name='HistorialCocina'),
    path('new-formula', NuevaFormulaView.as_view(),name='NuevaFormula'),
    path('add-ayudantes', AddAyudantes.as_view(),name='AddAyudantes'),

    path('nueva-transferencias', NuevaTransferenciaView.as_view(),name='NuevaTransferenciaCocina'),
    path('historial-transferencias/<str:action>', TransferenciasView.as_view(),name='TransferenciaCocina'),
    
    path('recibir-turno/<int:coc_id>/', RecibirTurnoView.as_view(),name='RecibirTurnoCocina'),
    path('recibir-inv-turno/<int:coc_id>/', RecibirTurnoInventarioView.as_view(),name='RecibirInventarioTurnoCocina'),
    path('recibir-util-turno/<int:coc_id>/', RecibirTurnoUtilesView.as_view(),name='RecibirUtilesTurnoCocina'),
    path('cerrar-turno', EntregarTurnoView.as_view(),name='CerrarTurnoCocina'),
    path('resumen-turno/<int:turno_id>/', ResumenTurnoView.as_view(),name='ResumenTurnoCocina'),
    path('notas', NotasCocinaView.as_view(),name='NotasCocina'),
    
    path('get-notificacion-cocina/', getNotificacionCocina,name='NotificacionCocina'),
]