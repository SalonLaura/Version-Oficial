from django.utils import timezone
import json
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from bussiness.utils import login_required
from django.views import View
from django.db.models import Q, Sum
from django.contrib import messages

from bussiness.models import AlertaAdmin, Descuentos, Producto, StockAlmacen, StockPuntoVenta, StockUsuario, Transferencia
from estudio.models import StockEstudio
from kitchen.models import StockCocina
from otherworkers.models import Turno

# Create your views here.

@method_decorator(login_required, name='dispatch')
class IpvView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        stock_ids = []
        stock = []
        stock_usuarios = StockUsuario.objects.filter(cantidad_actual__gt=0,user=request.user)

        for s in stock_usuarios:
            if s.producto.id not in stock_ids:
                stock_ids.append(s.producto.id)
                stock.append(s)
            else:
                
                stock[stock_ids.index(s.producto.id)].cantidad_actual += s.cantidad_actual
        base = "base"
        if request.user.pago_servicios.all().exists():base="ow/base"

        context = {"stock":stock,"base":base+".html"}
        return render(request,'ow/ipv.html',context)
    
@method_decorator(login_required, name='dispatch')
class RecibirTurnoView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        stock_ids = []
        stock = []
        stock_usuarios = StockUsuario.objects.filter(cantidad_actual__gt=0,user=request.user)

        for s in stock_usuarios:
            if s.producto.id not in stock_ids:
                stock_ids.append(s.producto.id)
                stock.append(s)
            else:
                
                stock[stock_ids.index(s.producto.id)].cantidad_actual += s.cantidad_actual

        context = {"stock":stock}
        return render(request,'ow/recibir_turno.html',context)

    def post(self,request,*args,**kwargs):
        #try:
            data = request.POST

            if "ids" in data.keys():ids = list(dict(data)["ids"])
            else:ids =  []

            if "ajuste-stock" in data.keys():ajuste_stock = list(dict(data)["ajuste-stock"])
            else:ajuste_stock =  []
            
            turno = Turno.objects.get_or_create(
                user=request.user,
                cuadre=json.dumps({}),
                fin = None
            )
            
            notas = []
            cuadre = []

            if "motivos-ajuste" in data.keys() and "id-producto" in data.keys() and "cantidad-ajuste" in data.keys():
                motivos_ajuste = list(dict(data)["motivos-ajuste"])
                id_producto = list(dict(data)["id-producto"])
                cantidad_ajuste = list(dict(data)["cantidad-ajuste"])

                try:
                    for index,motivo in enumerate(motivos_ajuste,start=0):
                        producto = Producto.objects.get(id=id_producto[index])
                        cantidad = float(cantidad_ajuste[index])
                        monto = cantidad * producto.precio_venta
                        if monto < 0: 
                            monto *= -1
                            Descuentos.objects.create(
                                monto_original = monto,
                                monto = monto,
                                descripcion = f"Faltan {cantidad*-1} {producto.medida.abreviatura} de {producto.nombre}",
                                motivo = motivo,
                                user_id = f"U-{request.user.id}",
                                user_name = request.user.user
                            )
                        
                        notas.append(
                            {
                                "producto_id":id_producto[index],
                                "cantidad" : cantidad,
                                "motivo" : motivo,
                                "monto" : monto,
                            }
                        )
                except Exception as e:
                    print(f"Error al guardar notas: {e}")

                    
                AlertaAdmin.objects.create(
                    tipo=False,
                    centro_costo = f"S-{turno[0].id}",
                    motivo = f"Inicio de turno de {request.user.user} efectuado con {len(motivos_ajuste)} incidencias."
                )
                
            else:
                AlertaAdmin.objects.create(
                    tipo=None,
                    centro_costo = f"S-{turno[0].id}",
                    motivo = f"Inicio de turno de {request.user.user} efectuado sin incidencias."
                )
            
            for index,id in enumerate(ids,start=0):
                stock = StockUsuario.objects.filter(producto__id=id,cantidad_actual__gt=0,user=request.user).order_by("alta")
                
                if stock.exists():
                    s = stock.first()
                    try:
                        existencia  = stock.aggregate(total = Sum("cantidad_actual"))["total"]
                    except:
                        existencia  = 0
                    finally:
                        if existencia == None:
                            existencia = 0

                    if ajuste_stock[index] != "-":
                        cantidad_descontar = existencia - float(ajuste_stock[index])

                        cuadre.append(
                            {
                                "producto_id":id,
                                "inicial":float(ajuste_stock[index]),
                                "entradas":0
                            }
                        )

                        if cantidad_descontar > 0:
                            for spv in stock:
                                if cantidad_descontar == 0: break
                                elif cantidad_descontar <= spv.cantidad_actual:
                                    spv.cantidad_actual -= cantidad_descontar
                                    if spv.cantidad_actual == 0:
                                        spv.activo = False
                                    spv.save()
                                    cantidad_descontar = 0
                                else:
                                    cantidad_descontar -= spv.cantidad_actual
                                    spv.cantidad_actual = 0
                                    spv.activo = False
                                    spv.save()
                        else:
                            cantidad_descontar *= -1 
                            for spv in stock:
                                if cantidad_descontar == 0: break
                                elif spv.cantidad_actual + cantidad_descontar <= spv.cantidad_inicial:
                                    spv.cantidad_actual += cantidad_descontar
                                    spv.activo = True
                                    spv.save()
                                    cantidad_descontar = 0
                                    break
                                else:
                                    cantidad_descontar -= (spv.cantidad_inicial - spv.cantidad_actual)
                                    spv.cantidad_actual = spv.cantidad_inicial
                                    spv.activo = True
                                    spv.save()
                
                            if cantidad_descontar != 0:
                                s.cantidad_actual += cantidad_descontar
                                s.save()
                
                    else:
                        cuadre.append(
                            {
                                "producto_id":id,
                                "inicial":existencia,
                                "entradas":0
                            }
                        )

                else:
                    stock = StockUsuario.objects.filter(producto__id=id,user=request.user).order_by("alta")
                    if stock.exists():
                        s = stock.first()
                        try:
                            existencia  = stock.aggregate(total = Sum("cantidad_actual"))["total"]
                        except:
                            existencia  = 0
                        finally:
                            if existencia == None:
                                existencia = 0

                        if ajuste_stock[index] != "-":
                            cantidad_descontar = existencia - float(ajuste_stock[index])

                            cuadre.append(
                                {
                                    "producto_id":id,
                                    "inicial":float(ajuste_stock[index]),
                                    "entradas":0
                                }
                            )

                            if cantidad_descontar > 0:
                                for spv in stock:
                                    if cantidad_descontar == 0: break
                                    elif cantidad_descontar <= spv.cantidad_actual:
                                        spv.cantidad_actual -= cantidad_descontar
                                        if spv.cantidad_actual == 0:
                                            spv.activo = False
                                        spv.save()
                                        cantidad_descontar = 0
                                    else:
                                        cantidad_descontar -= spv.cantidad_actual
                                        spv.cantidad_actual = 0
                                        spv.activo = False
                                        spv.save()
                            
                            else:
                                cantidad_descontar *= -1  
                                for spv in stock:
                                    if cantidad_descontar == 0: break
                                    elif spv.cantidad_actual + cantidad_descontar <= spv.cantidad_inicial:
                                        spv.cantidad_actual += cantidad_descontar
                                        spv.activo = True
                                        spv.save()
                                        cantidad_descontar = 0
                                        break
                                    else:
                                        cantidad_descontar -= (spv.cantidad_inicial - spv.cantidad_actual)
                                        spv.cantidad_actual = spv.cantidad_inicial
                                        spv.activo = True
                                        spv.save()
                                        
                                if cantidad_descontar != 0:
                                    s.cantidad_actual += cantidad_descontar
                                    s.save()

                        else:
                            cuadre.append(
                                {
                                    "producto_id":id,
                                    "inicial":existencia,
                                    "entradas":0
                                }
                            )

            cuadre_data =json.dumps({
                "notas":notas,
                "cuadre":cuadre
            })
        
            turno = Turno.objects.get_or_create(
                user=request.user,
                cuadre=json.dumps({}),
                fin = None
            )

            turno = turno[0]                
            turno.cuadre=cuadre_data
            turno.save()
                
            return redirect("IpvTrabajador")
        
        #except Exception as e:
            print("Error en el cuadre: ",e)
            return redirect("RecibirTurnoTrabajador")


@method_decorator(login_required, name='dispatch')
class TransferenciasView(View):
    def get(self,request,*args,**kwargs):
        turno = Turno.objects.get(user=request.user,fin=None)
        transferencias = Transferencia.objects.filter(Q(receptor_id=f"U-{request.user.id}") & (Q(turno_id=f"S-{turno.id}") | Q(turno_id=None)) & Q(mensaje_cancelacion__isnull = True)).order_by("alta").reverse()
        
        base = "base"
        if request.user.pago_servicios.all().exists():base="ow/base"

        context = {"transferencias":transferencias,"base":base+".html"}

        return render(request,'ow/transferencias.html',context)
    
    def post(self,request,*args,**kwargs):
        data = request.POST

        pv_ids = list(dict(data)["producto-pv-id"])
        cantidades = list(dict(data)["cantidad"])
        try:
            turno = Turno.objects.get(user=request.user,fin=None)
            for index,id in enumerate(pv_ids,start=0):
                stock = StockUsuario.objects.get(id=id)
                cant = cantidades[index]
                stock.cantidad_recibida = cant

                if stock.lote:
                    existencia = stock.lote.producto.existencia(stock.lote.almacen.id)
                    por_confirmar = StockPuntoVenta.objects.filter(producto=stock.producto,transferencia__turno_id = None, transferencia__emisor_id = f"A-{stock.lote.almacen.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
                    if por_confirmar is not None:
                        existencia = existencia + por_confirmar

                    por_confirmar = StockCocina.objects.filter(producto=stock.producto, transferencia__turno_id = None, transferencia__emisor_id = f"A-{stock.lote.almacen.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
                    if por_confirmar is not None:
                        existencia = existencia + por_confirmar

                    por_confirmar = StockAlmacen.objects.filter(producto=stock.producto, cantidad_inicial = None, transferencia__emisor_id = f"A-{stock.lote.almacen.id}").aggregate(total = Sum("cantidad_factura"))["total"]
                    if por_confirmar is not None:
                        existencia = existencia + por_confirmar

                    por_confirmar = StockUsuario.objects.filter(producto=stock.producto,transferencia__turno_id = None, transferencia__emisor_id = f"A-{stock.lote.almacen.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
                    if por_confirmar is not None:
                        existencia = existencia + por_confirmar
                        

                    por_confirmar = StockEstudio.objects.filter(producto=stock.producto,transferencia__turno_id = None, transferencia__emisor_id = f"A-{stock.lote.almacen.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
                    if por_confirmar is not None:
                        existencia = existencia + por_confirmar
                        
                        
                    existencia -= float(cant)

                else:existencia = None

                
                turno.add_entrada_cuadre(stock.lote.producto.id, cant)

                stock.cantidad_inicial = cant
                stock.cantidad_actual = cant
                stock.existencia = existencia
                stock.activo = True
                stock.save()

                if stock.transferencia.turno_id is None and index + 1 == len(pv_ids):
                    stock.transferencia.date_confirm = timezone.now()
                    stock.transferencia.user_confirmacion = request.user.user_str()
                    stock.transferencia.turno_id = f"S-{turno.id}"
                    stock.transferencia.save()
        except:
            messages.error(request, "Error al confirmar transferencia, puede que el remitente haya cancelado la transferencia.")

            return redirect("TransferenciasTrabajador")
        
@method_decorator(login_required, name='dispatch')
class EntregarTurnoView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET

        turno = Turno.objects.get(user=request.user,fin=None)
        cuadre = turno.datos_cuadre()["cuadre"]
        for c in cuadre:
            c["producto"] = Producto.objects.get(id=c["producto_id"])

        base = "base"
        if request.user.pago_servicios.all().exists():base="ow/base"

        context = {"cuadre":cuadre,"base":base+".html"}

        if Transferencia.objects.filter(receptor_id=f"U-{request.user.id}",turno_id__isnull = True,mensaje_cancelacion=None).exists():            
            context["message"] = "Antes de terminar el turno debe aceptar o cancelar todas las transferencias pendientes"     

        return render(request,'ow/entregar_turno.html',context)
    
    
    def post(self,request,*args,**kwargs):
        data = request.POST
        turno = Turno.objects.get(user=request.user,fin=None)
        turno.fin = timezone.now()
        turno.save()
        
        return redirect("http://" + str(request.get_host()) + "/logout/?for=servicio")
    
