from django.urls import path
from .views import (ContratosPendientesView, EditContratoView, NewClienteView,FichaClienteView,ConfigView,ContratosRealizadosView,HistorialContratosView,
                    add_servicio,add_tipo_contrato,add_contrato,add_fotografo, add_editor, add_casa_impresion,add_estados,VerContratoTerminadoView,
                    FotosEdicionView,FotosImpresionView,SubproductosView,TransferenciasView,RecibirTurnoView,EntregarTurnoView,BolsaView)

urlpatterns = [
    path('new-cliente/', NewClienteView.as_view(),name='NewClienteEstudio'),
    path('pendientes/', ContratosPendientesView.as_view(),name='PendientesEstudio'),
    path('realizados/', ContratosRealizadosView.as_view(),name='RealizadosEstudio'),
    path('historial/', HistorialContratosView.as_view(),name='HistorialEstudio'),
    path('fotos-edicion/', FotosEdicionView.as_view(),name='FotosEdicionEstudio'),
    path('fotos-impresion/', FotosImpresionView.as_view(),name='FotosImpresionEstudio'),
    path('contrato/<int:id_contrato>/', EditContratoView.as_view(),name='EditContratoEstudio'),
    path('c/<int:id>/', VerContratoTerminadoView.as_view(),name='VerContratoTerminadoEstudio'),
    path('subproductos',SubproductosView.as_view(),name='SubproductosEstudio'),
    path('transferencias',TransferenciasView.as_view(),name='TransferenciasEstudio'),
    path('recibir', RecibirTurnoView.as_view(),name='RecibirTurnoEstudio'),
    path('entregar-turno',EntregarTurnoView.as_view(),name='EntregarTurnoEstudio'),
    path('ipv-bolsa',BolsaView.as_view(),name='BolsaEstudio'),

    path('ficha-cliente/', FichaClienteView.as_view(),name='FichaCliente'),
    path('config/', ConfigView.as_view(),name='ConfigEstudio'),
    path('add-servicio/', add_servicio),
    path('add-tipo-contrato/', add_tipo_contrato),
    path('add-contrato/', add_contrato),
    path('add-fotografo/', add_fotografo),
    path('add-editor/', add_editor),
    path('add-casa-impresion/', add_casa_impresion),
    path('add-estados/', add_estados),
]