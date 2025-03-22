import json
import threading
from django.contrib import messages
from datetime import datetime
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views import View
from django.utils import timezone
from django.db.models import Q, Sum
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from bot.bot import send_message
from bussiness.models import AlertaAdmin, Almacen, Categoria, Descuentos, Medida, Pago, Producto, PuntoVenta, StockAlmacen, StockPuntoVenta, StockUsuario, Transferencia, UserAccount
from bussiness.utils import login_required, toMoney
from estudio.models import StockEstudio
from kitchen.models import Consumo, GastosElaboracion, Nota, CantidadSubproducto, Cocina, Cuadre, Formula, NotaCocina, SolicitudCocina, StockCocina, StockProductoCompuestoCocina, Turno

def super_upper(text:str) -> str:
    return text.upper().translate({
                ord('á'): 'A',
                ord('é'): 'E',
                ord('í'): 'I',
                ord('ó'): 'O',
                ord('ú'): 'U',
            })

def getCocinaFromCookie(request):
    cocina = None
    try:        
        if "cocina_id" in request.COOKIES: 
            cocina = Cocina.objects.get(id=request.COOKIES["cocina_id"].replace("C-",""))
        else:
            request.user.cocina()
        return cocina
    
    except:
        print("****** Error <getCocinaFromCookie> *****")
        return None

@method_decorator(login_required, name='dispatch')
class MediosBasicos(View):
    def get(self,request,*args,**kwargs):
        cocina = getCocinaFromCookie(request)
        productos_ids = []
        stock_return = []
        stock_cocina = StockCocina.objects.filter(cocina=cocina,activo=True,cantidad_actual__gt=0,producto__categoria__nombre = "MEDIOS BASICOS")
        for s in stock_cocina:
            if s.producto.id not in productos_ids:
                stock_return.append({
                    "producto":s.producto,
                    "disponibilidad":StockCocina.objects.filter(activo=True,cantidad_actual__gt=0, producto=s.producto, cocina=cocina).aggregate(total=Sum('cantidad_actual'))["total"]
                })
                productos_ids.append(s.producto.id)

        context = {"stock_return":stock_return}
        return render(request,'cocina/stock.html',context)

@method_decorator(login_required, name='dispatch')
class StockView(View):
    def get(self,request,*args,**kwargs):
        cocina = getCocinaFromCookie(request)
        productos_ids = []
        stock_return = []
        stock_cocina = StockCocina.objects.filter(cocina=cocina,activo=True,cantidad_actual__gt=0).exclude(producto__categoria__nombre = "MEDIOS BASICOS")
        for s in stock_cocina:
            if s.producto.id not in productos_ids:
                stock_return.append({
                    "producto":s.producto,
                    "disponibilidad":StockCocina.objects.filter(activo=True,cantidad_actual__gt=0, producto=s.producto, cocina=cocina).aggregate(total=Sum('cantidad_actual'))["total"]
                })
                productos_ids.append(s.producto.id)

        productos_ids = []
        stock_producto_compuesto = StockProductoCompuestoCocina.objects.filter(activo=True,cantidad_actual__gt=0,turno__cocina=cocina)
        for s in stock_producto_compuesto:
            if s.producto.id not in productos_ids:
                stock_return.append({
                    "producto":s.producto,
                    "disponibilidad":StockProductoCompuestoCocina.objects.filter(activo=True,cantidad_actual__gt=0, producto=s.producto,turno__cocina=cocina).aggregate(total=Sum('cantidad_actual'))["total"]
                })
                productos_ids.append(s.producto.id)

        context = {"stock_return":stock_return, "cocina":cocina}
        return render(request,'cocina/stock.html',context)

@method_decorator(login_required, name='dispatch')
class HistorialView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        cocina = getCocinaFromCookie(request)
        turno = Turno.objects.get(user=request.user,cocina=cocina,fin=None)
        
        platos = StockProductoCompuestoCocina.objects.filter(turno=turno).order_by("-fecha_fabricacion")
        suproductos = StockCocina.objects.filter(consumo__isnull=False,alta__gte = turno.inicio).order_by("-alta")
        context = {"platos":platos,"suproductos":suproductos, "cocina":cocina}
        return render(request,'cocina/historial_elaboracion.html',context)
        
# Cuando se elabora un producto solicitado por un cliente
@method_decorator(login_required, name='dispatch')
class SolicitudesView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        cocina = getCocinaFromCookie(request)
        if "solic" in data.keys():
            if not SolicitudCocina.objects.filter(id=data["solic"]).exists():
                messages.error(request, 'Error al comenzar a elaborar el producto. No debe elaborar el producto debido a que el punto de venta canceló el pedido.')
                return redirect("SolicitudesCocina")
            else:
                solicitud = SolicitudCocina.objects.get(id=data["solic"])
                if solicitud.estado == None:
                    solicitud.estado = False
                    solicitud.save()
        else:
            solicitudes = SolicitudCocina.objects.filter(cocina = cocina, activo = True,estado = False)
            
            for s in solicitudes:
                s.estado = None
                s.save()

            solicitud = None
        

        solicitudes = SolicitudCocina.objects.filter(Q(cocina = cocina) & Q(activo = True) & Q(transferido = False))
        context = {"solicitudes":solicitudes,
                   "solicitud_elaborar":solicitud,
                   "cocina":cocina
                   }

        return render(request,'cocina/solicitudes.html',context)
        
    def post_old(self,request,*args,**kwargs):
        data = request.POST
        data_get = request.GET

        if "solicitud-elaborar-id" in data:
            cocina = getCocinaFromCookie(request)
            solicitud = SolicitudCocina.objects.get(id=data["solicitud-elaborar-id"])
            formula = solicitud.formula()
            cantidad_elaborar = solicitud.cantidad
            cantidad_resultante = solicitud.cantidad
                
            costo_cup = 0
            audit = 0
            no_audit = 0
            
            subproductos_usados = []

            for k in data.keys():
                if "subproductos-usados" in k:
                    subproductos_usados.append(data[k])


            for subproducto in formula.subproducto.all():
                if str(subproducto.id) in subproductos_usados:
                    stock = StockCocina.objects.filter(producto=subproducto.producto,cantidad_actual__gt=0,cocina=cocina).order_by("alta")
                    
                    cantidad_descontar = (cantidad_elaborar * subproducto.cantidad)/formula.cantidad
                    
                    for s in stock:
                        if cantidad_descontar == 0: break
                        elif cantidad_descontar <= s.cantidad_actual:
                            costo_cup += (cantidad_descontar*s.lote.costo_real())
                            s.cantidad_actual -= cantidad_descontar
                            
                            if s.lote.almacen.is_audit: audit += cantidad_descontar
                            else: no_audit += cantidad_descontar

                            if s.cantidad_actual == 0:
                                s.activo = False
                            s.save()
                            cantidad_descontar = 0
                        else:
                            costo_cup += (s.cantidad_actual*s.lote.costo_real())
                            cantidad_descontar -= s.cantidad_actual
                            
                            if s.lote.almacen.is_audit: audit += s.cantidad_actual
                            else: no_audit += s.cantidad_actual

                            s.cantidad_actual = 0
                            s.activo = False
                            s.save()

            """if audit + no_audit == 0:
                messages.error(request, 'Error al elaborar el producto. El almacen no cuenta con el stock necesario para la elaboración.')
                return redirect("SolicitudesCocina")"""
            
            costo_cup = costo_cup/cantidad_resultante
            gastos = 0
            for gasto in formula.gastos.all():
                gastos += gasto.monto
            costo_cup += (gastos/cantidad_resultante)
            
            #PARA LOS AUDIT
            cantidad_elaborar_audit = (cantidad_elaborar * audit)/ (audit + no_audit)
            if cantidad_elaborar > cantidad_resultante:
                cantidad_resultante_audit =  cantidad_resultante
            else:
                cantidad_resultante_audit =  cantidad_elaborar_audit
            # Agregando al costo los gastos asociados a la produccion
            #costo_cup += ((cantidad_resultante_audit*gastos)/formula.cantidad)
                
            turno = Turno.objects.get(user=request.user,cocina=cocina,fin=None)
            StockProductoCompuestoCocina.objects.create(
                turno = turno,
                producto = formula.producto,
                costo_cup=costo_cup,
                cantidad_elaborada=cantidad_elaborar_audit,
                cantidad_resultante=cantidad_resultante_audit,
                cantidad_actual=cantidad_resultante_audit,
                monto_total = formula.producto.precio_venta * cantidad_resultante_audit
            )

            #PARA LOS NO AUDIT
            if cantidad_elaborar > cantidad_resultante:
                cantidad_resultante_audit =  0
            else:
                cantidad_resultante_audit =  cantidad_resultante - cantidad_elaborar_audit
            cantidad_elaborar_audit = (cantidad_elaborar * no_audit)/ (audit + no_audit)
            # Agregando al costo los gastos asociados a la produccion
            #costo_cup += ((cantidad_resultante_audit*gastos)/formula.cantidad)
            
            if cantidad_elaborar_audit > 0:
                StockProductoCompuestoCocina.objects.create(
                    turno = turno,
                    producto = formula.producto,
                    costo_cup=costo_cup,
                    cantidad_elaborada=cantidad_elaborar_audit,
                    cantidad_resultante=cantidad_resultante_audit,
                    cantidad_actual=cantidad_resultante_audit,
                    monto_total = formula.producto.precio_venta * cantidad_resultante_audit
                )

            
            if "solic" in data_get.keys():
                solicitud = SolicitudCocina.objects.get(id=data_get["solic"])
                solicitud.estado = True
                solicitud.costo = costo_cup # + monto
                solicitud.save()


            if formula.pago_elaboracion_relacion == "$": monto = formula.pago_elaboracion_monto
            elif formula.pago_elaboracion_relacion == "%": monto = formula.pago_elaboracion_monto * (cantidad_resultante * formula.producto.precio_venta)
            else:monto = 0.0
            Pago.objects.create(
                monto_original = monto,
                monto = monto,
                descripcion = f"Pago realizado por elaborar {cantidad_resultante} {formula.producto.medida.nombre} de {formula.producto.nombre}",
                user = request.user.user_str()
            )

                
            return redirect("SolicitudesCocina")
            

        id_solicitud = data["id-solicitud"]
        solicitud = SolicitudCocina.objects.get(id=id_solicitud)
        solicitud.transferido = True
        solicitud.mensaje_cancelacion = None
        solicitud.save()

        return redirect("SolicitudesCocina")
    
    def post(self,request,*args,**kwargs):
        data = request.POST
        data_get = request.GET

        if "solicitud-elaborar-id" in data:
            cocina = getCocinaFromCookie(request)
            solicitud = SolicitudCocina.objects.get(id=data["solicitud-elaborar-id"])
            formula = solicitud.formula()
            cantidad_elaborar = solicitud.cantidad
            cantidad_resultante = solicitud.cantidad
                
            turno = Turno.objects.get(user=request.user,cocina=cocina,fin=None)
            
            subproductos_usados = []

            for k in data.keys():
                if "subproductos-usados" in k:
                    subproductos_usados.append(data[k])

            consumo_list = []
            for subproducto in formula.subproducto.all():
                if str(subproducto.id) in subproductos_usados:
                    
                    cantidad_descontar = (cantidad_elaborar * subproducto.cantidad)/formula.cantidad
                    cuadre = Cuadre.objects.get_or_create(turno=turno,producto=subproducto.producto)[0]
                    consumo = Consumo.objects.create(
                        turno = turno,
                        formula = formula,
                        producto = subproducto.producto,
                        cantidad = cantidad_descontar,
                        medida = subproducto.medida
                    )
                    consumo_list.append(consumo.to_str())

            
            StockProductoCompuestoCocina.objects.create(
                turno = turno,
                producto = formula.producto,
                costo_cup=formula.producto.precio_venta,
                cantidad_elaborada=cantidad_elaborar,
                cantidad_resultante=cantidad_resultante,
                cantidad_actual=0,
                consumo = ", ".join(consumo_list),
                monto_total = formula.producto.precio_venta * cantidad_resultante
            )


            if "solic" in data_get.keys():
                solicitud = SolicitudCocina.objects.get(id=data_get["solic"])
                solicitud.estado = True
                solicitud.save()


            # Pago por la elaboracion
            if formula.pago_elaboracion_relacion == "$": 
                monto = (formula.pago_elaboracion_monto / formula.cantidad) * cantidad_resultante
            elif formula.pago_elaboracion_relacion == "%":
                monto = (formula.pago_elaboracion_monto / formula.cantidad) * cantidad_resultante * formula.producto.precio_venta
            else:
                monto = 0.0

            if monto > 0.0:

                ayudantes = turno.ayudantes.all()
                if len(ayudantes) > 0: monto_cocinero = monto*cocina.porciento_cocinero/100
                else:monto_cocinero = monto

                pago = Pago.objects.create(
                    monto_original = monto_cocinero,
                    monto = monto_cocinero,
                    descripcion = f"Elaborar {cantidad_resultante} {formula.producto.medida.nombre} de {formula.producto.nombre}",
                    user_id = f"U-{request.user.id}",
                    user_name = request.user.user_str()
                )

                turno.pagos.add(pago)

                ayudantes = turno.ayudantes.all()
                if len(ayudantes) >0:
                    monto_ayudante = (monto*(100-cocina.porciento_cocinero)/100)/len(ayudantes)
                    for a in ayudantes:                    
                        pago = Pago.objects.create(
                            monto_original = monto_ayudante,
                            monto = monto_ayudante,
                            descripcion = f"Elaborar {cantidad_resultante} {formula.producto.medida.nombre} de {formula.producto.nombre}",
                            user_id = f"U-{a.id}",
                            user_name = a.user
                        )
                    
                        turno.pagos.add(pago)

            return redirect("SolicitudesCocina")
            

        id_solicitud = data["id-solicitud"]
        solicitud = SolicitudCocina.objects.get(id=id_solicitud)
        solicitud.transferido = True
        solicitud.mensaje_cancelacion = None
        solicitud.save()

        return redirect("SolicitudesCocina")

# Cuando se elebora un kit transferido desde el almacen
@method_decorator(login_required, name='dispatch')
class FormulasView(View):
    def get(self,request,*args,**kwargs):
        
        cocina = getCocinaFromCookie(request)
        transferencias_ids = []
        formulas_return = []
        try:
            stock = StockCocina.objects.filter(transferencia__cant_elaborar__isnull = False,cantidad_actual__isnull = False,activo=True,cocina=cocina,transferencia__mensaje_cancelacion__isnull = True)
            for s in stock:
                if s.transferencia.id not in transferencias_ids:
                    formula = s.objetivo
                    if formula:
                        formula.disponibilidad = s.transferencia.cant_elaborar
                        formula.transferencia = s.transferencia
                        formulas_return.append(formula)

                        transferencias_ids.append(s.transferencia.id)
        
        except Exception as e:
            messages.error(request,"Error: " + str(e))

        context = {
            "formulas":formulas_return,
            "cocina":cocina,
            }

        return render(request,'cocina/formulas.html',context)
    
    def post(self,request,*args,**kwargs):
        data = request.POST
        data_get = request.GET

        cocina = getCocinaFromCookie(request)
        formula = Formula.objects.get(id=data["formula-elaborar-id"])
        transferencia = Transferencia.objects.get(id=data["transferencia-id"])
        
        cantidad_elaborar = float(data["cantidad_elaborar"])
        cantidad_resultante = float(data["cantidad_resultante"])
        
        stock = StockCocina.objects.filter(transferencia=transferencia, objetivo = formula)
        turno = Turno.objects.get(user=request.user,cocina=cocina,fin=None)

        costo_produccion = 0.0
        consumo_list = []
        for s in stock:
            costo_produccion += (s.cantidad_actual * s.lote.costo_cup)

            s.cantidad_actual = 0
            s.activo = False
            s.save()
            consumo = Consumo.objects.create(
                turno = turno,
                formula = formula,
                producto = s.producto,
                cantidad = s.cantidad_inicial,
                medida = s.producto.medida
            )
            consumo_list.append(consumo.to_str())

        
        if cantidad_resultante < cantidad_elaborar:
            diferencia = cantidad_elaborar- cantidad_resultante 
            alert = AlertaAdmin.objects.create(
                tipo=False,
                centro_costo = f"C-{cocina.id}",
                motivo = f"En el {cocina.nombre} del turno de {turno.user} se elaboraron {diferencia} {formula.producto} menos."
            )
                    
            message = f"<b>🚨 {cocina.nombre}</b>\n\n"
            message += f"En el {cocina.nombre} del turno de {turno.user} se elaboraron {diferencia} {formula.producto} menos."
                   
            t = threading.Thread(target=lambda:send_message(message,alert.id))
            t.start()
        elif cantidad_resultante > cantidad_elaborar:
            diferencia = cantidad_resultante - cantidad_elaborar
            alert = AlertaAdmin.objects.create(
                tipo=False,
                centro_costo = f"C-{cocina.id}",
                motivo = f"En el {cocina.nombre} del turno de {turno.user} se elaboraron {diferencia} {formula.producto} de más."
            )
                        
            message = f"<b>🚨 {cocina.nombre}</b>\n\n"
            message += f"En el {cocina.nombre} del turno de {turno.user} se elaboraron {diferencia} {formula.producto} de más."
                    
            t = threading.Thread(target=lambda:send_message(message,alert.id))
            t.start()

        if formula.producto.categoria.nombre == "SUBPRODUCTOS":
            StockCocina.objects.create(
                cocina = cocina,
                costo_produccion = (costo_produccion/cantidad_resultante),
                producto = formula.producto,
                cantidad_remitida=cantidad_elaborar,
                cantidad_recibida=cantidad_resultante,
                cantidad_inicial=cantidad_resultante,
                cantidad_actual=cantidad_resultante,
                consumo = ", ".join(consumo_list)
            )

        else:
            StockProductoCompuestoCocina.objects.create(
                turno = turno,
                producto = formula.producto,
                costo_cup=0.0,
                cantidad_elaborada=cantidad_elaborar,
                cantidad_resultante=cantidad_resultante,
                cantidad_actual=cantidad_resultante,
                consumo = ", ".join(consumo_list),
                monto_total = formula.producto.precio_venta * cantidad_resultante
            )


        # Pago por la elaboracion hay que ponerlo aqui
        if formula.pago_elaboracion_relacion == "$": 
            monto = (formula.pago_elaboracion_monto / formula.cantidad) * cantidad_resultante
        elif formula.pago_elaboracion_relacion == "%":
            monto = (formula.pago_elaboracion_monto / formula.cantidad) * cantidad_resultante * formula.producto.precio_venta
        else:
            monto = 0.0

        if monto > 0.0:
            ayudantes = turno.ayudantes.all()
            if len(ayudantes) > 0: monto_cocinero = monto*cocina.porciento_cocinero/100
            else:monto_cocinero = monto

            pago = Pago.objects.create(
                monto_original = monto_cocinero,
                monto = monto_cocinero,
                descripcion = f"Elaborar {cantidad_resultante} {formula.producto.medida.nombre} de {formula.producto.nombre}",
                user_id = f"U-{request.user.id}",
                user_name = request.user.user_str()
            )

            turno.pagos.add(pago)
            
            if len(ayudantes) > 0:
                monto_ayudante = (monto*(100-cocina.porciento_cocinero)/100)/len(ayudantes)
                for a in ayudantes:                    
                    pago = Pago.objects.create(
                        monto_original = monto_ayudante,
                        monto = monto_ayudante,
                        descripcion = f"Elaborar {cantidad_resultante} {formula.producto.medida.nombre} de {formula.producto.nombre}",
                        user_id = f"U-{a.id}",
                        user_name = a.user
                    )
                
                    turno.pagos.add(pago)       

        
        if "solic" in data_get.keys():
            solicitud = SolicitudCocina.objects.get(id=data_get["solic"])
            solicitud.estado = True
            solicitud.costo = formula.producto.precio_venta
            solicitud.save()
            
        if "prod" in data_get.keys():
            return redirect("SolicitudesCocina")
        
        return redirect("FormulasCocina")

@method_decorator(login_required, name='dispatch')
class RecetasView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        
        context = { 
                   "formulas" : Formula.objects.filter(activo=True).exclude(producto__categoria__nombre = "SUBPRODUCTOS").order_by("producto__nombre"),
                    "formulas_subproductos":Formula.objects.filter(producto__is_compuesto=True, activo=True, producto__categoria__nombre = "SUBPRODUCTOS"),
                }
        
        if "formula" in data:
            context["formula_elaborar"] = Formula.objects.get(id=data["formula"])

        return render(request,'cocina/recetas.html',context)
    
    def post(self,request,*args,**kwargs):
        data = request.POST

        cocina = getCocinaFromCookie(request)
        formula = Formula.objects.get(id=data["formula-elaborar-id"])
        cantidad_elaborar = float(data["cantidad_elaborar"])
        
        turno = Turno.objects.get(user=request.user,cocina=cocina,fin=None)
        subproductos_usados = []

        for k in data.keys():
            if "subproductos-usados" in k:
                subproductos_usados.append(data[k])

        consumo_list = []
        costo_produccion = 0.0
        for subproducto in formula.subproducto.all():
            if str(subproducto.id) in subproductos_usados:
                
                try:
                    lote = StockCocina.objects.last()
                    costo_produccion += (cantidad_descontar * lote.costo_cup())
                except:
                    pass

                cantidad_descontar = (cantidad_elaborar * subproducto.cantidad)/formula.cantidad
                cuadre = Cuadre.objects.get_or_create(turno=turno,producto=subproducto.producto)[0]
                consumo = Consumo.objects.create(
                    turno = turno,
                    formula = formula,
                    producto = subproducto.producto,
                    cantidad = cantidad_descontar,
                    medida = subproducto.medida
                )
                consumo_list.append(consumo.to_str())

        cuadre = Cuadre.objects.get_or_create(turno=turno,producto=formula.producto)[0]
        if formula.producto.categoria.nombre == "SUBPRODUCTOS":
            StockCocina.objects.create(
                cocina = cocina,
                costo_produccion = (costo_produccion/cantidad_elaborar),
                producto = formula.producto,
                cantidad_remitida=cantidad_elaborar,
                cantidad_recibida=cantidad_elaborar,
                cantidad_inicial=cantidad_elaborar,
                cantidad_actual=cantidad_elaborar,
                consumo = ", ".join(consumo_list)
            )
            
        if formula.pago_elaboracion_relacion == "$": 
            monto = (formula.pago_elaboracion_monto / formula.cantidad) * cantidad_elaborar
        elif formula.pago_elaboracion_relacion == "%":
            monto = (formula.pago_elaboracion_monto / formula.cantidad) * cantidad_elaborar * formula.producto.precio_venta
        else:
            monto = 0.0

        if monto > 0.0:
            ayudantes = turno.ayudantes.all()
            if len(ayudantes) > 0: monto_cocinero = monto*cocina.porciento_cocinero/100
            else:monto_cocinero = monto

            pago = Pago.objects.create(
                monto_original = monto_cocinero,
                monto = monto_cocinero,
                descripcion = f"Elaborar {cantidad_elaborar} {formula.producto.medida.nombre} de {formula.producto.nombre}",
                user_id = f"U-{request.user.id}",
                user_name = request.user.user_str()
            )

            turno.pagos.add(pago)
            
            if len(ayudantes) > 0:
                monto_ayudante = (monto*(100-cocina.porciento_cocinero)/100)/len(ayudantes)
                for a in ayudantes:                    
                    pago = Pago.objects.create(
                        monto_original = monto_ayudante,
                        monto = monto_ayudante,
                        descripcion = f"Elaborar {cantidad_elaborar} {formula.producto.medida.nombre} de {formula.producto.nombre}",
                        user_id = f"U-{a.id}",
                        user_name = a.user
                    )
                
                    turno.pagos.add(pago)       


        return redirect("RecetasCocina")

@method_decorator(login_required, name='dispatch')
class NuevaTransferenciaView(View):
    def get(self,request,*args,**kwargs):

        cocina = getCocinaFromCookie(request)
        turno = Turno.objects.get(user=request.user,cocina=cocina,fin=None)

        productos_ids = []
        productos_return = []
        productos = StockProductoCompuestoCocina.objects.filter(
            turno__cocina=cocina,
            cantidad_actual__gt = 0,
            activo = True
        )
        for p in productos:
            #if not SolicitudCocina.objects.filter(venta__producto = p.producto).exists():
            if f"SC-{p.producto.id}" not in productos_ids:
                productos_return.append(p)
                productos_ids.append(f"SC-{p.producto.id}")
            else:
                productos_return[productos_ids.index(f"SC-{p.producto.id}")].cantidad_actual += p.cantidad_actual

           
        subproductos_ids = []
        subproductos_return = []     
        productos = StockCocina.objects.filter(
            cocina=cocina,
            cantidad_actual__gt = 0,
            activo = True,
            producto__is_compuesto = True
        )
        for p in productos:
            if f"C-{p.producto.id}" not in subproductos_ids:
                subproductos_return.append(p)
                subproductos_ids.append(f"C-{p.producto.id}")
            else:                
                subproductos_return[subproductos_ids.index(f"C-{p.producto.id}")].cantidad_actual += p.cantidad_actual

        for subproducto in subproductos_return:
            cantidad_consuida = 0
            consumo = Consumo.objects.filter(turno=turno,producto=subproducto.producto)
            for c in consumo: cantidad_consuida += c.cantidad
            subproducto.cantidad_actual -= cantidad_consuida
            if subproducto.cantidad_actual <= 0:
                subproductos_return.pop(subproductos_return.index(subproducto))

        almacenes = Almacen.objects.filter(activo = True).order_by("nombre")
        puntos_ventas = PuntoVenta.objects.filter(activo = True).order_by("nombre")
        cocinas = Cocina.objects.filter(activo = True).order_by("nombre")
        
        context = {"almacenes":almacenes,"puntos_ventas":puntos_ventas,"cocinas":cocinas,"productos":productos_return,"emisor":cocina,"subproductos":subproductos_return,"cocina":cocina,}

        return render(request,'cocina/nueva_transferencia.html',context)
    
    def post(self,request,*args,**kwargs):
        data = request.POST
        
        emisor = data['emisor']
        receptor = data['receptor']
        if emisor == receptor:
            messages.error(request,"Seleccione un receptor diferente")
            return redirect("NuevaTransferenciaCocina")
        

        entrega = data['nombre_entrega']
        recibe = data['nombre_recibe']
        autoriza = data['nombre_autoriza']
        
        cantidades = list(dict(data)["cantidad"])
        producto_ids = list(dict(data)["producto-id"])

        transferencia = Transferencia.objects.create(
            emisor_id = emisor,
            receptor_id = receptor,
            entrega = entrega,
            recibe = recibe,
            autoriza = autoriza,
            user_transfiere = request.user.user_str()
        )

        cocina = getCocinaFromCookie(request)
        success = False
        if "A-" in receptor:
            for index,producto_id in enumerate(producto_ids,start=0):
                if cantidades[index] != "":
                    producto = Producto.objects.get(id=producto_id)
                    stock = StockCocina.objects.filter(producto=producto,cocina=cocina)
                    
                    cantidad_descontar = float(cantidades[index])
                    
                    if cantidad_descontar > 0:
                        costo = 0
                        for sc in stock:
                            if cantidad_descontar == 0: break
                            elif cantidad_descontar <= sc.cantidad_actual:
                                costo += (cantidad_descontar * sc.costo_cup())
                                sc.cantidad_actual -= cantidad_descontar
                                if sc.cantidad_actual == 0:
                                    sc.activo = False
                                sc.save()
                                cantidad_descontar = 0
                            else:
                                costo += (sc.cantidad_actual * sc.costo_cup())
                                cantidad_descontar -= sc.cantidad_actual
                                sc.cantidad_actual = 0
                                sc.activo = False
                                sc.save()
                                
                        almacen_receptor = Almacen.objects.get(id=receptor.replace("A-",""))

                        cant_transferir = float(cantidades[index])
                        StockAlmacen.objects.create(
                            almacen = almacen_receptor,
                            producto = producto,
                            lote = datetime.now().strftime('%Y%m%d%H%M%S%f'),
                            cantidad_factura = cant_transferir,
                            costo_cup = (costo/cant_transferir),
                            transferencia = transferencia,
                            activo = None
                        )
                        success = True

        elif "C-" in receptor:
            for index,producto_id in enumerate(producto_ids,start=0):
                if cantidades[index] != "":
                    producto = Producto.objects.get(id=producto_id)
                    stock = StockCocina.objects.filter(producto=producto,cocina=cocina)
                    
                    cantidad_descontar = float(cantidades[index])

                    
                    if cantidad_descontar > 0:
                        costo = 0
                        lote = None
                        for sc in stock:
                            if lote == None: lote = sc.lote

                            if cantidad_descontar == 0: break
                            elif cantidad_descontar <= sc.cantidad_actual:
                                costo += (cantidad_descontar * sc.costo_cup())
                                sc.cantidad_actual -= cantidad_descontar
                                if sc.cantidad_actual == 0:
                                    sc.activo = False
                                sc.save()
                                cantidad_descontar = 0
                            else:
                                costo += (sc.cantidad_actual * sc.costo_cup())
                                cantidad_descontar -= sc.cantidad_actual
                                sc.cantidad_actual = 0
                                sc.activo = False
                                sc.save()
                        
                        cant_transferir = float(cantidades[index])
                        cocina = Cocina.objects.get(id = receptor.replace("C-",""))
                        StockCocina.objects.create(
                            cocina =cocina,
                            producto = producto,
                            lote = lote,
                            transferencia = transferencia,
                            costo_produccion = costo/cant_transferir,
                            #existencia = existencia,
                            cantidad_remitida = cant_transferir,
                        )
                        success = True



        elif "PV-" in receptor:
            for index,producto_id in enumerate(producto_ids,start=0):
                if cantidades[index] != "":
                    producto = Producto.objects.get(id=producto_id)
                    stock = StockProductoCompuestoCocina.objects.filter(producto=producto,turno__cocina=cocina)
                    cantidad_descontar = float(cantidades[index])
                    
                    if cantidad_descontar > 0:                               
                        for sc in stock:
                            if cantidad_descontar == 0: break
                            elif cantidad_descontar <= sc.cantidad_actual:
                                sc.cantidad_actual -= cantidad_descontar
                                if sc.cantidad_actual == 0:
                                    sc.activo = False
                                sc.save()
                                cantidad_descontar = 0
                            else:
                                cantidad_descontar -= sc.cantidad_actual
                                sc.cantidad_actual = 0
                                sc.activo = False
                                sc.save()
                        
                        cant_transferir = float(cantidades[index])
                        punto_venta = PuntoVenta.objects.get(id = receptor.replace("PV-",""))
                        StockPuntoVenta.objects.create(
                            punto_venta =punto_venta,
                            producto = producto,
                            costo_produccion = producto.precio_venta,
                            transferencia = transferencia,
                            lote_auditable = False,
                            #existencia = existencia,
                            cantidad_remitida = cant_transferir,
                        )
                        success = True

        if success == False:
            transferencia.delete()

        return redirect("NuevaTransferenciaCocina")

@method_decorator(login_required, name='dispatch')
class TransferenciasView(View):
    def get(self,request,action,*args,**kwargs):
        cocina = getCocinaFromCookie(request)
        turno = Turno.objects.get(user=request.user,cocina=cocina,fin=None)
        if action == "get":
            transferencias = Transferencia.objects.filter(
                Q(receptor_id=f"C-{cocina.id}") & 
                Q(mensaje_cancelacion__isnull = True) & 
                (Q(turno_id = f"C-{turno.id}") | Q(turno_id = None))
                ).order_by("alta").reverse()
                
        else:
            transferencias = Transferencia.objects.filter(
                emisor_id=f"C-{cocina.id}",
                alta__gte = turno.inicio
            ).order_by("alta").reverse()
            
            
        context = {"transferencias":transferencias,"action":action,"emisor_cosina":cocina, "cocina":cocina,}

        return render(request,'cocina/historial_transferencias.html',context)
        
    def post(self,request,*args,**kwargs):
        data = request.POST
        productos_ids = list(dict(data)["producto-id"])
        cantidades = list(dict(data)["cantidad"])        
        cocina = getCocinaFromCookie(request)
        turno = Turno.objects.get(user=request.user,cocina=cocina,fin=None) 
        cantidad_anterior = 0       

        for index,id in enumerate(productos_ids,start=0):
            stock_cocina = StockCocina.objects.get(id=id)
            cant = cantidades[index]            
            stock_cocina.cantidad_recibida = cant
            
            if stock_cocina.lote:
                existencia = stock_cocina.lote.producto.existencia(stock_cocina.lote.almacen.id)
                
                por_confirmar = StockPuntoVenta.objects.filter(producto=stock_cocina.producto,transferencia__turno_id = None, transferencia__emisor_id = f"A-{stock_cocina.lote.almacen.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
                if por_confirmar is not None:
                    existencia = existencia + por_confirmar                   

                por_confirmar = StockCocina.objects.filter(producto=stock_cocina.producto, transferencia__turno_id = None, transferencia__emisor_id = f"A-{stock_cocina.lote.almacen.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
                if por_confirmar is not None:
                    if cantidad_anterior == 0 :
                        existencia = existencia + por_confirmar
                        cantidad_anterior = 1
                    else:
                        cantidad_anterior = por_confirmar + float(cant)
                        existencia = existencia + cantidad_anterior                                        
                else:
                    existencia = existencia + float(cant)                

                por_confirmar = StockAlmacen.objects.filter(producto=stock_cocina.producto, cantidad_inicial = None, transferencia__emisor_id = f"A-{stock_cocina.lote.almacen.id}").aggregate(total = Sum("cantidad_factura"))["total"]
                if por_confirmar is not None:
                    existencia = existencia + por_confirmar

                por_confirmar = StockUsuario.objects.filter(producto=stock_cocina.producto,transferencia__turno_id = None, transferencia__emisor_id = f"A-{stock_cocina.lote.almacen.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
                if por_confirmar is not None:
                    existencia = existencia + por_confirmar                    

                por_confirmar = StockEstudio.objects.filter(producto=stock_cocina.producto,transferencia__turno_id = None, transferencia__emisor_id = f"A-{stock_cocina.lote.almacen.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
                if por_confirmar is not None:
                    existencia = existencia + por_confirmar         
                                   
                existencia -= float(cant)
            else:
                existencia = None           

            if stock_cocina.transferencia.turno_id is None:
                stock_cocina.transferencia.turno_id = f"C-{turno.id}"
                stock_cocina.transferencia.date_confirm = timezone.now()
                stock_cocina.transferencia.user_confirmacion = request.user.user_str()
                stock_cocina.transferencia.save()

            stock_cocina.cantidad_inicial = cant
            stock_cocina.cantidad_actual = cant
            stock_cocina.existencia = existencia
            stock_cocina.activo = True
            stock_cocina.save()
            
            if not Cuadre.objects.filter(turno = turno,producto = stock_cocina.producto).exists():
                Cuadre.objects.create(
                    turno = turno,
                    producto = stock_cocina.producto,
                    recibido = 0
                )
        
        return redirect("TransferenciaCocina",action="get")

@method_decorator(login_required, name='dispatch')
class EntregarTurnoView(View):
    def get(self,request,*args,**kwargs):
        cocina = getCocinaFromCookie(request)
        turno = Turno.objects.get(user=request.user,cocina=cocina,fin=None) 
        productos = Cuadre.objects.filter(turno = turno)
        productos_usados=[]

        for usado in productos:
            if usado.usado != 0:
                productos_usados.append(usado)

        context = {"productos_usados":productos_usados, "cocina":cocina,}
        
        if Transferencia.objects.filter(receptor_id=f"C-{cocina.id}",turno_id__isnull = True, mensaje_cancelacion__isnull = True).exists():
            context["message"]="Hay transferencias realizadas pendientes a ser recibidas"

        elif Transferencia.objects.filter(emisor_id=f"C-{cocina.id}",date_confirm__isnull = True).exists():
            context["message"]="Ha realizado transferencias que no han sido confirmadas"

        else:
            transferencias = Transferencia.objects.filter(emisor_id=f"C-{cocina.id}")
            for transferencia in transferencias:
                stock = transferencia.stock()
                if len(stock) > 0 and stock[0].activo == None:
                    context["message"]="Hay transferencias realizadas pendientes a confirmación"
                    break
        
        #if StockProductoCompuestoCocina.objects.filter(activo = True,cantidad_actual__gt=0):
        #    context["message"]="Hay productos elaborados en la cocina, debe transferirlos a un punto de venta o a un almacen"
        
        if SolicitudCocina.objects.filter(Q(cocina = cocina) & Q(activo = True) & Q(transferido = False)).exists():
            context["message"]="Hay solicitudes de un punto de venta pendientes a ser atendidas"

        return render(request,'cocina/entregar_turno.html',context)
   
    def post(self,request,*args,**kwargs):
        data = request.POST
        cocina = getCocinaFromCookie(request)
        turno = Turno.objects.get(user=request.user,cocina=cocina,fin=None) 
        turno.fin = timezone.now()

        cuadre = Cuadre.objects.filter(turno=turno)
        costo = 0
        costo_ext = 0
        for p in cuadre:
            usado = Consumo.objects.filter(producto=p.producto,turno=turno).aggregate(total = Sum("cantidad"))["total"]
            if usado:
                p.usado = usado
                
                stock = StockCocina.objects.filter(producto=p.producto,cantidad_actual__gt=0,cocina=cocina).order_by("alta")
                if stock.exists():
                    s = stock.first()
                    existencia  = s.existencia_cocina()
                    if existencia - usado < 0:
                        cantidad_descontar = existencia
                    else:
                        cantidad_descontar = usado
                    
                    for sc in stock:
                        if cantidad_descontar == 0: 
                            break
                        elif cantidad_descontar <= sc.cantidad_actual:
                            if sc.lote:
                                costo += (cantidad_descontar * sc.lote.costo_real())
                                if sc.lote.almacen.is_audit:
                                    costo_ext += (cantidad_descontar * sc.lote.costo_real())

                            sc.cantidad_actual -= cantidad_descontar
                            if sc.cantidad_actual == 0:
                                sc.activo = True
                            sc.save()
                            cantidad_descontar = 0
                        else:
                            cantidad_descontar -= sc.cantidad_actual
                            if sc.lote:
                                costo += (sc.cantidad_actual * sc.lote.costo_real())
                                if sc.lote.almacen.is_audit:
                                    costo_ext += (sc.cantidad_actual * sc.lote.costo_real())

                            sc.cantidad_actual = 0
                            sc.activo = True
                            sc.save()
                    
            else: p.usado = 0
            p.save()

        pago_fijo = turno.pago_fijo()

        if pago_fijo:
            pago = Pago.objects.create(
                monto_original = pago_fijo,
                monto = pago_fijo,
                descripcion = f"Pago de salario fijo asignado al turno para el cocinero",
                user_id = f"U-{request.user.id}",
                user_name = request.user.user_str()
            )
            turno.pagos.add(pago)

        ayudantes = turno.ayudantes.all()
        monto_ayudante = turno.pago_fijo_ayudante()
        for a in ayudantes:                    
            pago = Pago.objects.create(
                monto_original = monto_ayudante,
                monto = monto_ayudante,
                descripcion = f"Pago de salario fijo asignado al turno para los ayudantes de cocina",
                user_id = f"U-{a.id}",
                user_name = a.user
            )
        
            turno.pagos.add(pago)
            
        monto = 0
        platos = StockProductoCompuestoCocina.objects.filter(turno=turno)
        for p in platos:
            monto += p.monto_total
            
        turno.costo = costo
        turno.costo_ext = costo_ext
        turno.monto = monto
        turno.save()
        return  redirect("ResumenTurnoCocina",turno_id=turno.id)

@method_decorator(login_required, name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')
class RecibirTurnoView(View):
    def get(self,request,coc_id,*args,**kwargs):
        #if not request.user.cocina(): return redirect('logout')
        elaboracion = []
        sin_elaborar = []
        cocina = Cocina.objects.get(id=coc_id)
        turno = Turno.objects.filter(cocina=cocina).order_by('-fin').first()        

        if(cocina.categoria == "no"):
            productos = cocina.productos_start_turno(turno)
            productos_kit = None         
            ruta = 'cocina/recibir_turno_cc.html'
            context = {
                "turno_anterior":turno,
                "productos":productos,
                "productos_kit":productos_kit
            }
        else:    
            productos_kit = cocina.kit_productos_start_turno(turno)
            productos = None

            for prod in productos_kit:
                if prod.consumo :
                    elaboracion.append(prod) 
                else:
                    sin_elaborar.append(prod)
            
            ruta = 'cocina/recibir_turno_ce.html'            
            context = {
                "turno_anterior":turno,
                "productos":productos,
                "productos_elab_kit":elaboracion,
                "productos_sin_elab_kit":sin_elaborar
            }          

        return render(request,ruta,context)
    
    def post(self,request,coc_id,*args,**kwargs):
        #try:
            data = request.POST
            cocina = Cocina.objects.get(id=coc_id)
            if cocina.categoria == "no":
                if Turno.objects.filter(cocina=cocina).exists():
                    turno_saliente = Turno.objects.filter(cocina=cocina).latest("fin")
    
                    ids = []
                    if "ids" in data:ids = list(dict(data)["ids"])
                    ajuste_stock = []
                    if "ajuste-stock" in data:ajuste_stock = list(dict(data)["ajuste-stock"])
                    
                    if "motivos-ajuste" in data.keys() and "id-producto" in data.keys() and "cantidad-ajuste" in data.keys():
                        motivos_ajuste = list(dict(data)["motivos-ajuste"])
                        id_producto = list(dict(data)["id-producto"])
                        cantidad_ajuste = list(dict(data)["cantidad-ajuste"])
                        precios = list(dict(data)["precio"])                
    
                        for index,motivo in enumerate(motivos_ajuste,start=0):
                            try:
                                cuadre = Cuadre.objects.get(producto__id=id_producto[index].replace("SC-","").replace("FC-",""),turno = turno_saliente)
                                cantidad = float(cantidad_ajuste[index])
                                monto = cantidad * float(precios[index])
                                if monto < 0: 
                                    monto *= -1
                                    
                                    Descuentos.objects.create(
                                        monto_original = monto,
                                        monto = monto,
                                        descripcion = f"Faltan {cantidad*-1} {cuadre.producto.medida.abreviatura} de {cuadre.producto.nombre}",
                                        motivo = motivo,
                                        user_id = f"U-{turno_saliente.user.id}",
                                        user_name = turno_saliente.user.user
                                    )
                            
                                nota = Nota.objects.create(
                                    cantidad = cantidad,
                                    motivo = motivo,
                                    cuadre = cuadre,
                                    monto = monto,
                                )
                            except Exception as e:
                                messages.error(request, f"Error al crear descuento y la nota: {e}")
                            
                        
                        alert = AlertaAdmin.objects.create(
                            tipo=False,
                            centro_costo = f"C-{cocina.id}",
                            motivo = f"Cambio de turno de {turno_saliente.user} en {cocina.nombre} efectuado con {len(motivos_ajuste)} incidencias."
                        )
                        
                        message = f"<b>🚨 {cocina.nombre}</b>\n\n"
                        message += f"Cambio de turno de {turno_saliente.user} en {cocina.nombre} efectuado con {len(motivos_ajuste)} incidencias."
                        
                        t = threading.Thread(target=lambda:send_message(message,alert.id))
                        t.start()
                        
                    else:
                        alert = AlertaAdmin.objects.create(
                            tipo=None,
                            centro_costo = f"C-{cocina.id}",
                            motivo = f"Cambio de turno de {turno_saliente.user} en {cocina.nombre} efectuado sin incidencias."
                        )
                        message = f"<b>✅ {cocina.nombre}</b>\n\n"
                        message += f"Cambio de turno de {turno_saliente.user} en {cocina.nombre} efectuado sin incidencias."
                        
                        t = threading.Thread(target=lambda:send_message(message,alert.id))
                        t.start()
                   
                    for index,id in enumerate(ids,start=0):
                        producto_id = id.replace("SC-","").replace("FC-","")
                        if Cuadre.objects.filter(turno=turno_saliente,producto__id=producto_id).exists():
                            producto = Cuadre.objects.get(turno=turno_saliente,producto__id=producto_id)
                            if ajuste_stock[index] != "-":
                                producto.entregado = ajuste_stock[index]
                            else:
                                producto.entregado = producto.existencia()
                                
                            producto.save()
                        
                        if "SC-" in id:
                            stock = StockProductoCompuestoCocina.objects.filter(producto__id=producto_id,cantidad_actual__gt=0,turno__cocina=cocina).order_by("fecha_fabricacion")
                            if stock.exists():
                                s = stock.first()
                                existencia  = s.existencia_cocina()
    
                                if ajuste_stock[index] != "-":
                                    cantidad_descontar = existencia - float(ajuste_stock[index])
                                    
                                    if cantidad_descontar > 0:
                                        for sc in stock:
                                            if cantidad_descontar == 0: break
                                            elif cantidad_descontar <= sc.cantidad_actual:
                                                sc.cantidad_actual -= cantidad_descontar
                                                if sc.cantidad_actual == 0:
                                                    sc.activo = False
                                                sc.save()
                                                cantidad_descontar = 0
                                            else:
                                                cantidad_descontar -= sc.cantidad_actual
                                                sc.cantidad_actual = 0
                                                sc.activo = False
                                                sc.save()
                                    else:
                                        cantidad_descontar *= -1 
                                        for sc in stock:
                                            if cantidad_descontar == 0: break
                                            elif sc.cantidad_actual + cantidad_descontar <= sc.cantidad_resultante:
                                                sc.cantidad_actual += cantidad_descontar
                                                sc.activo = True
                                                sc.save()
                                                cantidad_descontar = 0
                                                break
                                            else:
                                                cantidad_descontar -= (sc.cantidad_resultante - sc.cantidad_actual)
                                                sc.cantidad_actual = sc.cantidad_resultante
                                                sc.activo = True
                                                sc.save()
    
                                        if cantidad_descontar != 0:
                                            s.cantidad_actual += cantidad_descontar
                                            s.save()
                            
                            else:
                                stock = StockProductoCompuestoCocina.objects.filter(producto__id=producto_id,turno__cocina=cocina).order_by("-fecha_fabricacion")
                                if stock.exists():
                                    s = stock.first()
                                    existencia  = s.existencia_cocina()
                                    if ajuste_stock[index] != "-":
                                        cantidad_descontar = existencia - float(ajuste_stock[index])
    
                                        if cantidad_descontar > 0:
                                        
                                            for sc in stock:
                                                if cantidad_descontar == 0: break
                                                elif cantidad_descontar <= sc.cantidad_actual:
                                                    sc.cantidad_actual -= cantidad_descontar
                                                    if sc.cantidad_actual == 0:
                                                        sc.activo = False
                                                    sc.save()
                                                    cantidad_descontar = 0
                                                else:
                                                    cantidad_descontar -= sc.cantidad_actual
                                                    sc.cantidad_actual = 0
                                                    sc.activo = False
                                                    sc.save()
                                        else:
                                            cantidad_descontar *= -1 
                                            for sc in stock:
                                                if cantidad_descontar == 0: break
                                                elif sc.cantidad_actual + cantidad_descontar <= sc.cantidad_resultante:
                                                    sc.cantidad_actual += cantidad_descontar
                                                    sc.activo = True
                                                    sc.save()
                                                    cantidad_descontar = 0
                                                    break
                                                else:
                                                    cantidad_descontar -= (sc.cantidad_resultante - sc.cantidad_actual)
                                                    sc.cantidad_actual = sc.cantidad_resultante
                                                    sc.activo = True
                                                    sc.save()
    
                                            if cantidad_descontar != 0:
                                                s.cantidad_actual += cantidad_descontar
                                                s.save()
                                
                        elif "FC-" in id:
                            stock = StockCocina.objects.filter(producto__id=producto_id,cantidad_actual__gt=0,cocina=cocina).order_by("alta")
                            if stock.exists():
                                s = stock.first()
                                existencia  = s.existencia_cocina()
    
                                if ajuste_stock[index] != "-":
                                    cantidad_descontar = existencia - float(ajuste_stock[index])
    
                                    if cantidad_descontar > 0:                                
                                        for sc in stock:
                                            if cantidad_descontar == 0: break
                                            elif cantidad_descontar <= sc.cantidad_actual:
                                                sc.cantidad_actual -= cantidad_descontar
                                                if sc.cantidad_actual == 0:
                                                    sc.activo = False
                                                sc.save()
                                                cantidad_descontar = 0
                                            else:
                                                cantidad_descontar -= sc.cantidad_actual
                                                sc.cantidad_actual = 0
                                                sc.activo = False
                                                sc.save()
                                    else:
                                        cantidad_descontar *= -1 
                                        for sc in stock:
                                            if cantidad_descontar == 0: break
                                            elif sc.cantidad_actual + cantidad_descontar <= sc.cantidad_actual:
                                                sc.cantidad_actual += cantidad_descontar
                                                sc.activo = True
                                                sc.save()
                                                cantidad_descontar = 0
                                                break
                                            else:
                                                cantidad_descontar -= (sc.cantidad_actual - sc.cantidad_actual)
                                                sc.cantidad_actual = sc.cantidad_actual
                                                sc.activo = True
                                                sc.save()
                                        if cantidad_descontar != 0:
                                            s.cantidad_actual += cantidad_descontar
                                            s.save()
                            
                            else:
                                stock = StockCocina.objects.filter(producto__id=producto_id,cocina=cocina).order_by("-alta")
                                if stock.exists():
                                    s = stock.first()
                                    existencia  = s.existencia_cocina()
                                    if ajuste_stock[index] != "-":
                                        cantidad_descontar = existencia - float(ajuste_stock[index])
    
                                        if cantidad_descontar > 0:
                                        
                                            for sc in stock:
                                                if cantidad_descontar == 0: break
                                                elif cantidad_descontar <= sc.cantidad_actual:
                                                    sc.cantidad_actual -= cantidad_descontar
                                                    if sc.cantidad_actual == 0:
                                                        sc.activo = False
                                                    sc.save()
                                                    cantidad_descontar = 0
                                                else:
                                                    cantidad_descontar -= sc.cantidad_actual
                                                    sc.cantidad_actual = 0
                                                    sc.activo = False
                                                    sc.save()
                                        else:
                                            cantidad_descontar *= -1 
                                            for sc in stock:
                                                if cantidad_descontar == 0: break
                                                elif not sc.cantidad_actual: 
                                                    cantidad_descontar = 0
                                                    break
                                                elif sc.cantidad_actual + cantidad_descontar <= sc.cantidad_actual:
                                                    sc.cantidad_actual += cantidad_descontar
                                                    sc.activo = True
                                                    sc.save()
                                                    cantidad_descontar = 0
                                                    break
                                                else:
                                                    cantidad_descontar -= (sc.cantidad_actual - sc.cantidad_actual)
                                                    sc.cantidad_actual = sc.cantidad_actual
                                                    sc.activo = True
                                                    sc.save()
                                            if cantidad_descontar != 0:
                                                s.cantidad_actual += cantidad_descontar
                                                s.save()
                               
                
                    if turno_saliente.user == request.user:
                        alert = AlertaAdmin.objects.create(
                            tipo=True,
                            centro_costo = f"C-{cocina.id}",
                            motivo = f"El trabajador {request.user.user_str()} ha cerrado y abierto un turno en cocina {cocina.nombre}"
                        )
    
                        message = f"<b>⚠️ {cocina.nombre}</b>\n\n"
                        message += f"El trabajador {request.user.user_str()} ha cerrado y abierto un turno en cocina {cocina.nombre}"
                        
                        t = threading.Thread(target=lambda:send_message(message,alert.id))
                        t.start()
  
            turno = Turno.objects.get_or_create(
                cocina = cocina,
                user=request.user,
                fin = None
            )
                    
            if turno[1]:
                productos = cocina.productos()
                for producto in productos:
                    if producto.cant_stock > 0:
                        Cuadre.objects.create(
                            turno = turno[0],
                            producto = producto,
                            recibido = producto.cant_stock
                        )                
                
            return redirect("FormulasCocina")
        
        #except:
        #    context = {"productos":productos}
        #    return render(request,'cocina/recibir_turno.html',context)

@method_decorator(login_required, name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')
class RecibirTurnoInventarioView(View):
    def get(self,request,coc_id,*args,**kwargs):
        #if not request.user.cocina(): return redirect('logout')
        cocina = Cocina.objects.get(id=coc_id)
        turno = Turno.objects.filter(cocina=cocina).order_by('-fin').first()
        productos = cocina.inventario_start_turno(turno)
        
        context = {
            "turno_anterior":turno,
            "productos":productos
            }

        return render(request,'cocina/recibir_turno_inventario.html',context)
    
    def post(self,request,coc_id,*args,**kwargs):
        ##try:
            data = request.POST
            cocina = Cocina.objects.get(id=coc_id)

            if Turno.objects.filter(cocina=cocina).exists():
                turno_saliente = Turno.objects.filter(cocina=cocina).latest("fin")

                ids = []
                if "ids" in data:ids = list(dict(data)["ids"])
                ajuste_stock = []
                if "ajuste-stock" in data:ajuste_stock = list(dict(data)["ajuste-stock"])
                
                if "motivos-ajuste" in data.keys() and "id-producto" in data.keys() and "cantidad-ajuste" in data.keys():
                    motivos_ajuste = list(dict(data)["motivos-ajuste"])
                    id_producto = list(dict(data)["id-producto"])
                    cantidad_ajuste = list(dict(data)["cantidad-ajuste"])
                    precios = list(dict(data)["precio"])
                

                    for index,motivo in enumerate(motivos_ajuste,start=0):
                        try:
                            cuadre = Cuadre.objects.get(producto__id=id_producto[index].replace("SC-","").replace("FC-",""),turno = turno_saliente)
                            cantidad = float(cantidad_ajuste[index])
                            monto = cantidad * float(precios[index])
                            if monto < 0: 
                                monto *= -1
                                
                                Descuentos.objects.create(
                                    monto_original = monto,
                                    monto = monto,
                                    descripcion = f"Faltan {cantidad*-1} {cuadre.producto.medida.abreviatura} de {cuadre.producto.nombre}",
                                    motivo = motivo,
                                    user_id = f"U-{turno_saliente.user.id}",
                                    user_name = turno_saliente.user.user
                                )
                        
                            nota = Nota.objects.create(
                                cantidad = cantidad,
                                motivo = motivo,
                                cuadre = cuadre,
                                monto = monto,
                            )
                        except Exception as e:
                            messages.error(request, f"Error al crear descuento y la nota: {e}")
                        
                    
                    alert = AlertaAdmin.objects.create(
                        tipo=False,
                        centro_costo = f"C-{cocina.id}",
                        motivo = f"Cambio de turno de {turno_saliente.user} en {cocina.nombre} efectuado con {len(motivos_ajuste)} incidencias."
                    )
                    
                    message = f"<b>🚨 {cocina.nombre}</b>\n\n"
                    message += f"Cambio de turno de {turno_saliente.user} en {cocina.nombre} efectuado con {len(motivos_ajuste)} incidencias."
                    
                    t = threading.Thread(target=lambda:send_message(message,alert.id))
                    t.start()
                    
                else:
                    alert = AlertaAdmin.objects.create(
                        tipo=None,
                        centro_costo = f"C-{cocina.id}",
                        motivo = f"Cambio de turno de {turno_saliente.user} en {cocina.nombre} efectuado sin incidencias."
                    )
                    message = f"<b>✅ {cocina.nombre}</b>\n\n"
                    message += f"Cambio de turno de {turno_saliente.user} en {cocina.nombre} efectuado sin incidencias."
                    
                    t = threading.Thread(target=lambda:send_message(message,alert.id))
                    t.start()
               
                for index,id in enumerate(ids,start=0):
                    producto_id = id.replace("SC-","").replace("FC-","")
                    if Cuadre.objects.filter(turno=turno_saliente,producto__id=producto_id).exists():
                        producto = Cuadre.objects.get(turno=turno_saliente,producto__id=producto_id)
                        if ajuste_stock[index] != "-":
                            producto.entregado = ajuste_stock[index]
                        else:
                            producto.entregado = producto.existencia()
                            
                        producto.save()
                    
                    if "SC-" in id:
                        stock = StockProductoCompuestoCocina.objects.filter(producto__id=producto_id,cantidad_actual__gt=0,turno__cocina=cocina).order_by("fecha_fabricacion")
                        if stock.exists():
                            s = stock.first()
                            existencia  = s.existencia_cocina()

                            if ajuste_stock[index] != "-":
                                cantidad_descontar = existencia - float(ajuste_stock[index])
                                
                                if cantidad_descontar > 0:
                                    for sc in stock:
                                        if cantidad_descontar == 0: break
                                        elif cantidad_descontar <= sc.cantidad_actual:
                                            sc.cantidad_actual -= cantidad_descontar
                                            if sc.cantidad_actual == 0:
                                                sc.activo = False
                                            sc.save()
                                            cantidad_descontar = 0
                                        else:
                                            cantidad_descontar -= sc.cantidad_actual
                                            sc.cantidad_actual = 0
                                            sc.activo = False
                                            sc.save()
                                else:
                                    cantidad_descontar *= -1 
                                    for sc in stock:
                                        if cantidad_descontar == 0: break
                                        elif sc.cantidad_actual + cantidad_descontar <= sc.cantidad_resultante:
                                            sc.cantidad_actual += cantidad_descontar
                                            sc.activo = True
                                            sc.save()
                                            cantidad_descontar = 0
                                            break
                                        else:
                                            cantidad_descontar -= (sc.cantidad_resultante - sc.cantidad_actual)
                                            sc.cantidad_actual = sc.cantidad_resultante
                                            sc.activo = True
                                            sc.save()

                                    if cantidad_descontar != 0:
                                        s.cantidad_actual += cantidad_descontar
                                        s.save()
                        
                        else:
                            stock = StockProductoCompuestoCocina.objects.filter(producto__id=producto_id,turno__cocina=cocina).order_by("-fecha_fabricacion")
                            if stock.exists():
                                s = stock.first()
                                existencia  = s.existencia_cocina()
                                if ajuste_stock[index] != "-":
                                    cantidad_descontar = existencia - float(ajuste_stock[index])

                                    if cantidad_descontar > 0:
                                    
                                        for sc in stock:
                                            if cantidad_descontar == 0: break
                                            elif cantidad_descontar <= sc.cantidad_actual:
                                                sc.cantidad_actual -= cantidad_descontar
                                                if sc.cantidad_actual == 0:
                                                    sc.activo = False
                                                sc.save()
                                                cantidad_descontar = 0
                                            else:
                                                cantidad_descontar -= sc.cantidad_actual
                                                sc.cantidad_actual = 0
                                                sc.activo = False
                                                sc.save()
                                    else:
                                        cantidad_descontar *= -1 
                                        for sc in stock:
                                            if cantidad_descontar == 0: break
                                            elif sc.cantidad_actual + cantidad_descontar <= sc.cantidad_resultante:
                                                sc.cantidad_actual += cantidad_descontar
                                                sc.activo = True
                                                sc.save()
                                                cantidad_descontar = 0
                                                break
                                            else:
                                                cantidad_descontar -= (sc.cantidad_resultante - sc.cantidad_actual)
                                                sc.cantidad_actual = sc.cantidad_resultante
                                                sc.activo = True
                                                sc.save()

                                        if cantidad_descontar != 0:
                                            s.cantidad_actual += cantidad_descontar
                                            s.save()
                            
                    elif "FC-" in id:
                        stock = StockCocina.objects.filter(producto__id=producto_id,cantidad_actual__gt=0,cocina=cocina).order_by("alta")
                        if stock.exists():
                            s = stock.first()
                            existencia  = s.existencia_cocina()

                            if ajuste_stock[index] != "-":
                                cantidad_descontar = existencia - float(ajuste_stock[index])

                                if cantidad_descontar > 0:                                
                                    for sc in stock:
                                        if cantidad_descontar == 0: break
                                        elif cantidad_descontar <= sc.cantidad_actual:
                                            sc.cantidad_actual -= cantidad_descontar
                                            if sc.cantidad_actual == 0:
                                                sc.activo = False
                                            sc.save()
                                            cantidad_descontar = 0
                                        else:
                                            cantidad_descontar -= sc.cantidad_actual
                                            sc.cantidad_actual = 0
                                            sc.activo = False
                                            sc.save()
                                else:
                                    cantidad_descontar *= -1 
                                    for sc in stock:
                                        if cantidad_descontar == 0: break
                                        elif sc.cantidad_actual + cantidad_descontar <= sc.cantidad_actual:
                                            sc.cantidad_actual += cantidad_descontar
                                            sc.activo = True
                                            sc.save()
                                            cantidad_descontar = 0
                                            break
                                        else:
                                            cantidad_descontar -= (sc.cantidad_actual - sc.cantidad_actual)
                                            sc.cantidad_actual = sc.cantidad_actual
                                            sc.activo = True
                                            sc.save()
                                    if cantidad_descontar != 0:
                                        s.cantidad_actual += cantidad_descontar
                                        s.save()
                        
                        else:
                            stock = StockCocina.objects.filter(producto__id=producto_id,cocina=cocina).order_by("-alta")
                            if stock.exists():
                                s = stock.first()
                                existencia  = s.existencia_cocina()
                                if ajuste_stock[index] != "-":
                                    cantidad_descontar = existencia - float(ajuste_stock[index])

                                    if cantidad_descontar > 0:
                                    
                                        for sc in stock:
                                            if cantidad_descontar == 0: break
                                            elif cantidad_descontar <= sc.cantidad_actual:
                                                sc.cantidad_actual -= cantidad_descontar
                                                if sc.cantidad_actual == 0:
                                                    sc.activo = False
                                                sc.save()
                                                cantidad_descontar = 0
                                            else:
                                                cantidad_descontar -= sc.cantidad_actual
                                                sc.cantidad_actual = 0
                                                sc.activo = False
                                                sc.save()
                                    else:
                                        cantidad_descontar *= -1 
                                        for sc in stock:
                                            if cantidad_descontar == 0: break
                                            elif not sc.cantidad_actual: 
                                                cantidad_descontar = 0
                                                break
                                            elif sc.cantidad_actual + cantidad_descontar <= sc.cantidad_actual:
                                                sc.cantidad_actual += cantidad_descontar
                                                sc.activo = True
                                                sc.save()
                                                cantidad_descontar = 0
                                                break
                                            else:
                                                cantidad_descontar -= (sc.cantidad_actual - sc.cantidad_actual)
                                                sc.cantidad_actual = sc.cantidad_actual
                                                sc.activo = True
                                                sc.save()
                                        if cantidad_descontar != 0:
                                            s.cantidad_actual += cantidad_descontar
                                            s.save()
                            
            
                if turno_saliente.user == request.user:
                    alert = AlertaAdmin.objects.create(
                        tipo=True,
                        centro_costo = f"C-{cocina.id}",
                        motivo = f"El trabajador {request.user.user_str()} ha cerrado y abierto un turno en cocina {cocina.nombre}"
                    )

                    message = f"<b>⚠️ {cocina.nombre}</b>\n\n"
                    message += f"El trabajador {request.user.user_str()} ha cerrado y abierto un turno en cocina {cocina.nombre}"
                    
                    t = threading.Thread(target=lambda:send_message(message,alert.id))
                    t.start()

  
            turno = Turno.objects.get_or_create(
                cocina = cocina,
                user=request.user,
                fin = None
            )

                    
            if turno[1]:
                productos = cocina.productos()
                for producto in productos:
                    if producto.cant_stock > 0:
                        Cuadre.objects.create(
                            turno = turno[0],
                            producto = producto,
                            recibido = producto.cant_stock
                        )                
                
            #return redirect("FormulasCocina")
            
        
        #except:
            context = {"productos":productos}
            return render(request,'punto_venta/recibir_turno.html',context)

@method_decorator(login_required, name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')
class RecibirTurnoUtilesView(View):
    def get(self,request,coc_id,*args,**kwargs):
        #if not request.user.cocina(): return redirect('logout')
        cocina = Cocina.objects.get(id=coc_id)
        turno = Turno.objects.filter(cocina=cocina).order_by('-fin').first()
        productos = cocina.productos_start_turno(turno)
        context = {
            "turno_anterior":turno,
            "productos":productos
            }

        return render(request,'cocina/recibir_turno_utiles.html',context)
    
    def post(self,request,coc_id,*args,**kwargs):
        #try:
            data = request.POST
            cocina = Cocina.objects.get(id=coc_id)

            if Turno.objects.filter(cocina=cocina).exists():
                turno_saliente = Turno.objects.filter(cocina=cocina).latest("fin")

                ids = []
                if "ids" in data:ids = list(dict(data)["ids"])
                ajuste_stock = []
                if "ajuste-stock" in data:ajuste_stock = list(dict(data)["ajuste-stock"])
                
                if "motivos-ajuste" in data.keys() and "id-producto" in data.keys() and "cantidad-ajuste" in data.keys():
                    motivos_ajuste = list(dict(data)["motivos-ajuste"])
                    id_producto = list(dict(data)["id-producto"])
                    cantidad_ajuste = list(dict(data)["cantidad-ajuste"])
                    precios = list(dict(data)["precio"])
                

                    for index,motivo in enumerate(motivos_ajuste,start=0):
                        try:
                            cuadre = Cuadre.objects.get(producto__id=id_producto[index].replace("SC-","").replace("FC-",""),turno = turno_saliente)
                            cantidad = float(cantidad_ajuste[index])
                            monto = cantidad * float(precios[index])
                            if monto < 0: 
                                monto *= -1
                                
                                Descuentos.objects.create(
                                    monto_original = monto,
                                    monto = monto,
                                    descripcion = f"Faltan {cantidad*-1} {cuadre.producto.medida.abreviatura} de {cuadre.producto.nombre}",
                                    motivo = motivo,
                                    user_id = f"U-{turno_saliente.user.id}",
                                    user_name = turno_saliente.user.user
                                )
                        
                            nota = Nota.objects.create(
                                cantidad = cantidad,
                                motivo = motivo,
                                cuadre = cuadre,
                                monto = monto,
                            )
                        except Exception as e:
                            messages.error(request, f"Error al crear descuento y la nota: {e}")
                        
                    
                    alert = AlertaAdmin.objects.create(
                        tipo=False,
                        centro_costo = f"C-{cocina.id}",
                        motivo = f"Cambio de turno de {turno_saliente.user} en {cocina.nombre} efectuado con {len(motivos_ajuste)} incidencias."
                    )
                    
                    message = f"<b>🚨 {cocina.nombre}</b>\n\n"
                    message += f"Cambio de turno de {turno_saliente.user} en {cocina.nombre} efectuado con {len(motivos_ajuste)} incidencias."
                    
                    t = threading.Thread(target=lambda:send_message(message,alert.id))
                    t.start()
                    
                else:
                    alert = AlertaAdmin.objects.create(
                        tipo=None,
                        centro_costo = f"C-{cocina.id}",
                        motivo = f"Cambio de turno de {turno_saliente.user} en {cocina.nombre} efectuado sin incidencias."
                    )
                    message = f"<b>✅ {cocina.nombre}</b>\n\n"
                    message += f"Cambio de turno de {turno_saliente.user} en {cocina.nombre} efectuado sin incidencias."
                    
                    t = threading.Thread(target=lambda:send_message(message,alert.id))
                    t.start()
               
                for index,id in enumerate(ids,start=0):
                    producto_id = id.replace("SC-","").replace("FC-","")
                    if Cuadre.objects.filter(turno=turno_saliente,producto__id=producto_id).exists():
                        producto = Cuadre.objects.get(turno=turno_saliente,producto__id=producto_id)
                        if ajuste_stock[index] != "-":
                            producto.entregado = ajuste_stock[index]
                        else:
                            producto.entregado = producto.existencia()
                            
                        producto.save()
                    
                    if "SC-" in id:
                        stock = StockProductoCompuestoCocina.objects.filter(producto__id=producto_id,cantidad_actual__gt=0,turno__cocina=cocina).order_by("fecha_fabricacion")
                        if stock.exists():
                            s = stock.first()
                            existencia  = s.existencia_cocina()

                            if ajuste_stock[index] != "-":
                                cantidad_descontar = existencia - float(ajuste_stock[index])
                                
                                if cantidad_descontar > 0:
                                    for sc in stock:
                                        if cantidad_descontar == 0: break
                                        elif cantidad_descontar <= sc.cantidad_actual:
                                            sc.cantidad_actual -= cantidad_descontar
                                            if sc.cantidad_actual == 0:
                                                sc.activo = False
                                            sc.save()
                                            cantidad_descontar = 0
                                        else:
                                            cantidad_descontar -= sc.cantidad_actual
                                            sc.cantidad_actual = 0
                                            sc.activo = False
                                            sc.save()
                                else:
                                    cantidad_descontar *= -1 
                                    for sc in stock:
                                        if cantidad_descontar == 0: break
                                        elif sc.cantidad_actual + cantidad_descontar <= sc.cantidad_resultante:
                                            sc.cantidad_actual += cantidad_descontar
                                            sc.activo = True
                                            sc.save()
                                            cantidad_descontar = 0
                                            break
                                        else:
                                            cantidad_descontar -= (sc.cantidad_resultante - sc.cantidad_actual)
                                            sc.cantidad_actual = sc.cantidad_resultante
                                            sc.activo = True
                                            sc.save()

                                    if cantidad_descontar != 0:
                                        s.cantidad_actual += cantidad_descontar
                                        s.save()
                        
                        else:
                            stock = StockProductoCompuestoCocina.objects.filter(producto__id=producto_id,turno__cocina=cocina).order_by("-fecha_fabricacion")
                            if stock.exists():
                                s = stock.first()
                                existencia  = s.existencia_cocina()
                                if ajuste_stock[index] != "-":
                                    cantidad_descontar = existencia - float(ajuste_stock[index])

                                    if cantidad_descontar > 0:
                                    
                                        for sc in stock:
                                            if cantidad_descontar == 0: break
                                            elif cantidad_descontar <= sc.cantidad_actual:
                                                sc.cantidad_actual -= cantidad_descontar
                                                if sc.cantidad_actual == 0:
                                                    sc.activo = False
                                                sc.save()
                                                cantidad_descontar = 0
                                            else:
                                                cantidad_descontar -= sc.cantidad_actual
                                                sc.cantidad_actual = 0
                                                sc.activo = False
                                                sc.save()
                                    else:
                                        cantidad_descontar *= -1 
                                        for sc in stock:
                                            if cantidad_descontar == 0: break
                                            elif sc.cantidad_actual + cantidad_descontar <= sc.cantidad_resultante:
                                                sc.cantidad_actual += cantidad_descontar
                                                sc.activo = True
                                                sc.save()
                                                cantidad_descontar = 0
                                                break
                                            else:
                                                cantidad_descontar -= (sc.cantidad_resultante - sc.cantidad_actual)
                                                sc.cantidad_actual = sc.cantidad_resultante
                                                sc.activo = True
                                                sc.save()

                                        if cantidad_descontar != 0:
                                            s.cantidad_actual += cantidad_descontar
                                            s.save()
                            
                    elif "FC-" in id:
                        stock = StockCocina.objects.filter(producto__id=producto_id,cantidad_actual__gt=0,cocina=cocina).order_by("alta")
                        if stock.exists():
                            s = stock.first()
                            existencia  = s.existencia_cocina()

                            if ajuste_stock[index] != "-":
                                cantidad_descontar = existencia - float(ajuste_stock[index])

                                if cantidad_descontar > 0:                                
                                    for sc in stock:
                                        if cantidad_descontar == 0: break
                                        elif cantidad_descontar <= sc.cantidad_actual:
                                            sc.cantidad_actual -= cantidad_descontar
                                            if sc.cantidad_actual == 0:
                                                sc.activo = False
                                            sc.save()
                                            cantidad_descontar = 0
                                        else:
                                            cantidad_descontar -= sc.cantidad_actual
                                            sc.cantidad_actual = 0
                                            sc.activo = False
                                            sc.save()
                                else:
                                    cantidad_descontar *= -1 
                                    for sc in stock:
                                        if cantidad_descontar == 0: break
                                        elif sc.cantidad_actual + cantidad_descontar <= sc.cantidad_actual:
                                            sc.cantidad_actual += cantidad_descontar
                                            sc.activo = True
                                            sc.save()
                                            cantidad_descontar = 0
                                            break
                                        else:
                                            cantidad_descontar -= (sc.cantidad_actual - sc.cantidad_actual)
                                            sc.cantidad_actual = sc.cantidad_actual
                                            sc.activo = True
                                            sc.save()
                                    if cantidad_descontar != 0:
                                        s.cantidad_actual += cantidad_descontar
                                        s.save()
                        
                        else:
                            stock = StockCocina.objects.filter(producto__id=producto_id,cocina=cocina).order_by("-alta")
                            if stock.exists():
                                s = stock.first()
                                existencia  = s.existencia_cocina()
                                if ajuste_stock[index] != "-":
                                    cantidad_descontar = existencia - float(ajuste_stock[index])

                                    if cantidad_descontar > 0:
                                    
                                        for sc in stock:
                                            if cantidad_descontar == 0: break
                                            elif cantidad_descontar <= sc.cantidad_actual:
                                                sc.cantidad_actual -= cantidad_descontar
                                                if sc.cantidad_actual == 0:
                                                    sc.activo = False
                                                sc.save()
                                                cantidad_descontar = 0
                                            else:
                                                cantidad_descontar -= sc.cantidad_actual
                                                sc.cantidad_actual = 0
                                                sc.activo = False
                                                sc.save()
                                    else:
                                        cantidad_descontar *= -1 
                                        for sc in stock:
                                            if cantidad_descontar == 0: break
                                            elif not sc.cantidad_actual: 
                                                cantidad_descontar = 0
                                                break
                                            elif sc.cantidad_actual + cantidad_descontar <= sc.cantidad_actual:
                                                sc.cantidad_actual += cantidad_descontar
                                                sc.activo = True
                                                sc.save()
                                                cantidad_descontar = 0
                                                break
                                            else:
                                                cantidad_descontar -= (sc.cantidad_actual - sc.cantidad_actual)
                                                sc.cantidad_actual = sc.cantidad_actual
                                                sc.activo = True
                                                sc.save()
                                        if cantidad_descontar != 0:
                                            s.cantidad_actual += cantidad_descontar
                                            s.save()
                            
            
                if turno_saliente.user == request.user:
                    alert = AlertaAdmin.objects.create(
                        tipo=True,
                        centro_costo = f"C-{cocina.id}",
                        motivo = f"El trabajador {request.user.user_str()} ha cerrado y abierto un turno en cocina {cocina.nombre}"
                    )

                    message = f"<b>⚠️ {cocina.nombre}</b>\n\n"
                    message += f"El trabajador {request.user.user_str()} ha cerrado y abierto un turno en cocina {cocina.nombre}"
                    
                    t = threading.Thread(target=lambda:send_message(message,alert.id))
                    t.start()

  
            turno = Turno.objects.get_or_create(
                cocina = cocina,
                user=request.user,
                fin = None
            )

                    
            if turno[1]:
                productos = cocina.productos()
                for producto in productos:
                    if producto.cant_stock > 0:
                        Cuadre.objects.create(
                            turno = turno[0],
                            producto = producto,
                            recibido = producto.cant_stock
                        )                
                
            return redirect("FormulasCocina")
        
        #except:
            context = {"productos":productos}
            return render(request,'punto_venta/recibir_turno.html',context)


@method_decorator(login_required, name='dispatch')
class ResumenTurnoView(View):
    def get(self,request,turno_id,*args,**kwargs):
        turno = Turno.objects.get(id=turno_id)
        cantidad_elaborada = StockProductoCompuestoCocina.objects.filter(turno = turno).aggregate(total=Sum('cantidad_resultante'))["total"]
        if not cantidad_elaborada: cantidad_elaborada = 0

        
        pagos_fijos = [{"n":turno.user.user,"v":round(turno.cocina.pago_fijo_cocinero,2)}]


        if turno.cocina.pago_fijo_ayudante:
            for a in turno.ayudantes.all():
                pagos_fijos.append(
                    {
                        "n":a.user,
                        "v":round(turno.cocina.pago_fijo_ayudante,2)
                    }
                )
                
        pagos_dict = {}
        pagos = turno.pagos.all()
        for p in pagos:
            if p.user_name in pagos_dict:
                pagos_dict[p.user_name] += p.monto_original
            else:
                pagos_dict[p.user_name] = p.monto_original
        pagos_list = []
        for k in pagos_dict.keys():
            pagos_list.append({"n":k,"v":pagos_dict[k]})
        context = {
            "turno":turno,
            "cantidad_elaborada":int(cantidad_elaborada),
            "pagos_elaboracion":pagos_list,
            "pagos_fijos":pagos_fijos
            }

        return render(request,'cocina/resumen_turno.html',context)

class NuevaFormulaView(View):
    def post(self,request,*args,**kwargs):
        #try:
            data = request.POST
            # Para el DELETE
            if "delete-id" in data.keys():
                formula = Formula.objects.get(id=data["delete-id"])
                #formula.producto.delete()
                formula.delete()

                csrf = str(render(request,"csrf.html").content).replace('''b'<input type="hidden" name="csrfmiddlewaretoken" value="''',"").replace("""">'""","")
                returned = {"csrf":csrf,"delete":"success"}
                data =json.dumps(returned)
                return HttpResponse(data,"application/json")
                        
            cantidad = data['cant-resultante']
            formula_descripcion = data['formula-text']

            cantidad_subproducto = list(dict(data)["cantidad-subproducto"])
            subproducto_id = list(dict(data)["subproducto-id"])
            #medidas = list(dict(data)["medida-id"])

            if "subgrupo-subproductos" in data and data["subgrupo-subproductos"] != "":
                subgrupos = list(dict(data)["subgrupo-subproductos"])
            else:
                subgrupos = []

            if "gasto-nombre" in data.keys():
                nombres_gastos = list(dict(data)["gasto-nombre"])
                cantidad_gastos = list(dict(data)["gasto-cantidad"])
            else:
                nombres_gastos = []
                cantidad_gastos = []

            producto_resultante = Producto.objects.get(id=data["producto-resultante"])
            
            if "edited-formula" in data and data["edited-formula"] != "":
                formula = Formula.objects.get(id=data["edited-formula"])
                formula.cantidad=cantidad
                formula.producto=producto_resultante
                formula.subproducto.all().delete()
                formula.gastos.all().delete()
                formula.cocinas.clear()
            else: 
                formula = Formula.objects.create(producto=producto_resultante,cantidad=cantidad)

            for index,id in enumerate(subproducto_id,start=0):
                if subgrupos[index] == "-":
                    subgrupo = None
                else:
                    subgrupo = subgrupos[index]

                prod = Producto.objects.get(id=id)
                cant_subproducto = CantidadSubproducto.objects.create(
                    producto=prod,
                    cantidad=cantidad_subproducto[index],
                    subgrupo=subgrupo,
                    medida = prod.medida,#Medida.objects.get(id=medidas[index])
                )
                formula.subproducto.add(cant_subproducto)

            formula.descripcion = formula_descripcion
            formula.pago_elaboracion_monto = data["pago-elaboracion-monto"]
            formula.pago_elaboracion_relacion = data["pago-elaboracion-relacion"]
            
            for index,nombre in enumerate(nombres_gastos,start=0):
                gasto = GastosElaboracion.objects.create(nombre=nombre,monto=cantidad_gastos[index])
                formula.gastos.add(gasto)

            
            if "cocinas" in data:
                cocinas = list(dict(data)["cocinas"])
                for c in cocinas:
                    formula.cocinas.add(Cocina.objects.get(id=c))
            formula.save()
            
            
            return redirect("http://" + str(request.get_host()) + "/config/formulas/")
    
        #except Exception as e:
            print(e)
            return redirect("http://" + str(request.get_host()) + "/config/formulas/")

@method_decorator(login_required, name='dispatch')
class NotasCocinaView(View):
    def get(self,request,*args,**kwargs):

        cocina = getCocinaFromCookie(request)
        notas = NotaCocina.objects.filter(cocina_id = f"C-{cocina.id}")

        return render(request,'cocina/notas.html',{"notas":notas})
    
    def post(self,request,*args,**kwargs):
        data = request.POST
        cocina = getCocinaFromCookie(request)
        if "nueva-nota" in data:
            NotaCocina.objects.create(
                cocina_id = f"C-{cocina.id}",
                cocina_nombre = f"{cocina.nombre}",
                cocinero_nombre = request.user.user_str(),
                nota = data["nueva-nota"],
            )
        elif "delete-note" in data:
            delete_notes = list(dict(data)["delete-note"])
            for index,id in enumerate(delete_notes,start=0):
                NotaCocina.objects.get(id=id).delete()

        return redirect('NotasCocina')

@method_decorator(login_required, name='dispatch')
class AddAyudantes(View):    
    def post(self,request,*args,**kwargs):
        data = request.POST
        turno = Turno.objects.get(id=data["turno-id"])

        if data["user-id-add"] != "":
            turno.ayudantes.add(UserAccount.objects.get(id=data["user-id-add"]))
            turno.save()

        elif data["user-id-delete"] != "":
            turno.ayudantes.remove(UserAccount.objects.get(id=data["user-id-delete"]))
            turno.save()

        return redirect(data["redirect"])
    
def getNotificacionCocina(request):
    if request.method == 'GET':
        cocina_id = int(request.GET["cocina_id"].split("-")[1])
        stock = StockCocina.objects.filter(transferencia__receptor_id = f"C-{cocina_id}",cantidad_recibida__isnull=True,
                                               transferencia__mensaje_cancelacion__isnull=True)

        messages_list = []
        if stock.exists():
            messages_list.append(f"{len(stock)} transferencias pendientes por confirmación")

        solicitudes = SolicitudCocina.objects.filter(cocina__id = cocina_id, estado = None)
        if solicitudes.exists():
            messages_list.append(f"{len(solicitudes)} solicitudes  pendientes a ser atendidas")


        if len(messages_list) > 0:
            message = f'{request.user}, tienes ' + ", ".join(messages_list).replace(",", "y", -1)
            returned = {
                "success":"YES",
                "message":message,
            }        
            
        else:
            returned = {
                "success":"NO"
            }
        return HttpResponse(json.dumps(returned),"application/json")
    
    else:
        returned = {
            "success":"NO"
        }
        
        return HttpResponse(json.dumps(returned),"application/json")
    
