from django.urls import path
from .views import (HistorialTransferenciasView, InformeRecepcionView, Login, Logout, MenuView,RecepcionarStockView,ConfirmRecepcionView, RecibirTurnoView, RegistroVentasView,TransferenciaSimpleView,TransferenciaPedidosView,
                    TransferenciaPvView,
                    CancelarTransferenciaView,CuentasView,CerrarCuenta,AlmacenView,EntregarTurnoView,ConfigView,AddTrabajador,PreciosView,
                    ConfigServicioView,ConfigCocinaView,ConfigTransformacionView,ConfigUsuarioView,ConfigMedidaView,ConfigCategoriaView,ConfigProductoView,ConfigPuntoVentaView,ConfigAlmacenView,ConfigFormulaView,
                    VentaRapidaView,ResumenTurnoView,GestionTurnosView,HistorialRecepcionView, getNotificacionPv,reabrirTurno,restringirVentas,ConfigVariablesView,
                    update_cuenta,getNotas,EntradasSalidasView,TransferenciaCompuestaView,SolicitudesView,addProducto,NotasPvView,AdminAlertasView
                    )

urlpatterns = [
    path('', Login.as_view(),name='login'),
    path('logout/', Logout.as_view(),name='logout'),
    
    
    path('precios/', PreciosView.as_view(),name='Precios'),

    #- Urls del Superusuario
    path('config/<str:area>/', ConfigView.as_view(),name='Config'),
    
    #- Urls del Superusuario
    path('config-variables/', ConfigVariablesView.as_view()),
    path('config-user/', ConfigUsuarioView.as_view()),
    path('config-medida/', ConfigMedidaView.as_view()),
    path('config-categoria/', ConfigCategoriaView.as_view()),
    path('config-producto/', ConfigProductoView.as_view()),
    path('config-add-producto/', addProducto),
    path('config-punto-venta/', ConfigPuntoVentaView.as_view()),
    path('config-almacen/', ConfigAlmacenView.as_view()),
    path('config-servicio/', ConfigServicioView.as_view()),
    path('config-cocina/', ConfigCocinaView.as_view()),
    path('config-formula/', ConfigFormulaView.as_view(),name="ConfigFormula"),
    path('config-transformacion/', ConfigTransformacionView.as_view()),
    path('alertas/', AdminAlertasView.as_view(),name="AdminAlertas"),

    path('get-notas/', getNotas,name='notas'),
    
    #- Urls del almacenero
    path('turnos/', GestionTurnosView.as_view(),name='GestionTurnos'),
    path('reabrir-turno/', reabrirTurno),
    path('restringir-venta/', restringirVentas),
    
    #- Urls del balancista
    path('informe-recepcion/', InformeRecepcionView.as_view(),name='InformeRecepcion'),
    path('historial-recepcion/', HistorialRecepcionView.as_view(),name='HistorialRecepcion'),
    path('confirm-recepcion/', ConfirmRecepcionView.as_view(),name='ConfirmRecepcionView'),

    #- Urls del almacenero
    path('almacen/', AlmacenView.as_view(),name='StockAlmacen'),   
    path('recepcionar-stock/', RecepcionarStockView.as_view(),name='RecepcionarStockView'),
    path('transferencia-simple/', TransferenciaSimpleView.as_view(),name='TransferenciaSimple'),
    path('transferencia-pedidos/', TransferenciaPedidosView.as_view(),name='TransferenciaPedidos'),
    path('transferencia-compuesta/', TransferenciaCompuestaView.as_view(),name='TransferenciaCompuesta'),

    path('historial-transferencias/', HistorialTransferenciasView.as_view(),name='HistorialTransferencias'),
    path('informe/entradas-salidas/', EntradasSalidasView.as_view(),name='EntradasSalidasView'),

    #- Urls del punto venta
    path('recibir/<int:pv_id>/', RecibirTurnoView.as_view(),name='RecibirTurno'),
    path('entregar/', EntregarTurnoView.as_view(),name='EntregarTurno'),
    path('cuentas-punto-venta/', CuentasView.as_view(),name='CuentasPuntoVenta'),    
    path('update-cuenta/', update_cuenta,name='update_cuenta'),
    path('venta-rapida/', VentaRapidaView.as_view(),name='VentaRapida'),
    path('solicitudes-pv/', SolicitudesView.as_view(),name='SolicitudesPv'),
    path('resumen-turno/<int:turno_id>/', ResumenTurnoView.as_view(),name='ResumenTurno'),
    path('punto-venta/<int:cuenta_id>', CerrarCuenta.as_view(),name='CerrarCuenta'),
    path('transferencia-pv/', TransferenciaPvView.as_view(),name='TransferenciaPv'),    
    path('cancel-transferencia/<int:id>/<str:rool>', CancelarTransferenciaView.as_view(),name='CancelarTransferenciaPv'),
    path('ventas/', RegistroVentasView.as_view(),name='RegistroVentas'),
    path('notas-pv', NotasPvView.as_view(),name='NotasPv'),
    path('add-trabajador/', AddTrabajador.as_view(),name='AddTrabajadorPv'),
    
    path('menu/<int:pv_id>', MenuView.as_view(),name='Menu'),


    # NOtificaciones
    path('get-notificacion-pv/', getNotificacionPv,name='NotificacionPv'),

]