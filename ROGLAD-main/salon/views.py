from datetime import datetime, timedelta
import json
import threading
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from bot.bot import send_message
from bussiness.models import AlertaAdmin, Categoria, ConfigVar, Pago, Descuentos, Medida, Producto, StockAlmacen, StockPuntoVenta, StockUsuario, Transferencia, UserAccount
from bussiness.utils import login_required
from django.views import View
from django.db.models import Q, Sum
from django.contrib import messages
from django.utils import timezone
from caja.models import Caja, Operaciones
from estudio.models import FichaCliente, StockEstudio
from kitchen.models import StockCocina
from salon.models import Cliente, Consumo, Turno, Servicio, CantidadSubproducto


def super_upper(text:str) -> str:
    return text.upper().translate({
                ord('á'): 'A',
                ord('é'): 'E',
                ord('í'): 'I',
                ord('ó'): 'O',
                ord('ú'): 'U',
            })


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
        return render(request,'salon/recibir_turno.html',context)

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

                    
                alert = AlertaAdmin.objects.create(
                    tipo=False,
                    centro_costo = f"S-{turno[0].id}",
                    motivo = f"Inicio de turno de {request.user.user} en el Salón efectuado con {len(motivos_ajuste)} incidencias."
                )

                message = f"<b>🚨 SALÓN</b>\n\n"
                message += f"Inicio de turno de {request.user.user} en el Salón efectuado con {len(motivos_ajuste)} incidencias."
                
                t = threading.Thread(target=lambda:send_message(message,alert.id))
                t.start()
                
            else:
                alert = AlertaAdmin.objects.create(
                    tipo=None,
                    centro_costo = f"S-{turno[0].id}",
                    motivo = f"Inicio de turno de {request.user.user} en el Salón efectuado sin incidencias."
                )

                message = f"<b>✅ SALÓN</b>\n\n"
                message += f"Inicio de turno de {request.user.user} en el Salón efectuado sin incidencias."
                
                t = threading.Thread(target=lambda:send_message(message,alert.id))
                t.start()
            
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
                
            return redirect("ClientesSalon")
        
        #except Exception as e:
            print("Error en el cuadre: ",e)
            return redirect("RecibirTurnoSalon")



@method_decorator(login_required, name='dispatch')
class ConsumoView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        turno = Turno.objects.get(user=request.user,fin=None)
        productos = Consumo.objects.filter(turno=turno)
        context = {"productos":productos}
        return render(request,'salon/consumo.html',context)
    

@method_decorator(login_required, name='dispatch')
class ServiciosView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        productos = Producto.objects.filter(Q(activo = True) & Q(categoria__nombre="SUBPRODUCTOS SALON")).order_by("nombre")
        servicios = Servicio.objects.filter(activo = True)
        context = {"productos":productos,"servicios":servicios}
        return render(request,'salon/servicios.html',context)
    
    def post(self,request,*args,**kwargs):
        try:
            data = request.POST

            # Para el DELETE
            if "delete-id" in data.keys():
                servicio = Servicio.objects.get(id=data["delete-id"])
                #formula.producto.delete()
                servicio.activo = False
                servicio.save()
                return redirect(str(request.build_absolute_uri()))

            if "actualizar-id" in data and data["actualizar-id"] != "":
                new_servicio = Servicio.objects.get(id=data["actualizar-id"])
                new_servicio.nombre = data["nombre"]
                new_servicio.precio_usd = data["precio-servicio"]
                new_servicio.descuento = data["monto-descuento"]
                new_servicio.caracteristicas = data["descripcion"]
                new_servicio.pago_monto = data["pago-monto"]
                new_servicio.pago_relacion = data["pago-relacion"]
                new_servicio.subproductos.clear()
            else:
                new_servicio = Servicio.objects.create(
                    nombre = data["nombre"],
                    precio_usd = data["precio-servicio"],
                    descuento = data["monto-descuento"],
                    caracteristicas = data["descripcion"],
                    pago_monto = data["pago-monto"],
                    pago_relacion = data["pago-relacion"]
                )
            subproducto_id = []
            if "subproducto-id" in data:
                cantidad_subproducto = list(dict(data)["cantidad-subproducto"])
                subproducto_id = list(dict(data)["subproducto-id"])
                
            if "subgrupo-subproductos" in data and data["subgrupo-subproductos"] != "":
                subgrupos = list(dict(data)["subgrupo-subproductos"])
            else:
                subgrupos = []
                
            for index,id in enumerate(subproducto_id,start=0):
                
                if subgrupos[index] == "-":
                    subgrupo = None
                else:
                    subgrupo = subgrupos[index]

                cant_subproducto = CantidadSubproducto.objects.create(
                    producto=Producto.objects.get(id=id),
                    cantidad=cantidad_subproducto[index],
                    subgrupo=subgrupo)
                
                new_servicio.subproductos.add(cant_subproducto)

            new_servicio.save()

            return redirect(str(request.build_absolute_uri()))

        except Exception as e:
            print(e)
            return redirect(str(request.build_absolute_uri()))

@method_decorator(login_required, name='dispatch')
class SubproductosView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        productos = Producto.objects.filter(Q(activo = True) & Q(categoria__nombre="SUBPRODUCTOS SALON")).order_by("nombre")
        context = {
            "productos":productos,
            "medidas" : Medida.objects.filter(activo = True),
            "categorias" : Categoria.objects.filter(activo = True).exclude(nombre="SUBPRODUCTOS SALON"),
            }
        return render(request,'salon/subproductos.html',context)
    
    def post(self,request,*args,**kwargs):
        try:
            data = request.POST            

            # Para el DELETE
            if "delete-id" in data.keys():
                producto = Producto.objects.get(id=data["delete-id"])
                producto.delete()

                return redirect(str(request.build_absolute_uri()))
            
            nombre = super_upper(data['nombre'])
            if "codigo" in data.keys():
                codigo = data['codigo']
                if "LINT-" in codigo:
                    codigo = "LINT-"
            else:codigo = "LINT-"
            categoria = Categoria.objects.filter(nombre="SUBPRODUCTOS SALON").first()
            medida = data['medida']

            if (((codigo != "LINT-" and Producto.objects.filter(Q(codigo=codigo),Q(activo=True)).exists()) or Producto.objects.filter(nombre=nombre,activo=True,categoria=categoria).exists()) and 
                ("edit-id" not in data.keys() or data['edit-id'] == '')):
                messages.error(request, f'Ya existe un producto de nombre {nombre}')
                return redirect(str(request.build_absolute_uri()))
            
            else:
                if "edit-id" in data.keys() and data['edit-id'] != '':
                    new_producto = Producto.objects.get(id=data['edit-id'])
                    new_producto.nombre=nombre
                else:
                    new_producto = Producto.objects.create(nombre=nombre)
                    
                if codigo == "LINT-":codigo += str(new_producto.id)
                new_producto.codigo=codigo

                uploaded_files = request.FILES
                
                if "image-product" in uploaded_files.keys(): 
                    new_producto.imagen = uploaded_files["image-product"]
                    new_producto.save()
                    imagen = new_producto.imagen.url
                else: 
                    imagen = data["image-product"]
                    if imagen != "":
                        imagen = f"/static/images/productos/{imagen}.jpg"
                        new_producto.imagen = imagen

                descripcion = data['descripcion']
                new_producto.descripcion = descripcion

                precio_venta = data['precio_venta']
                if precio_venta != "":new_producto.precio_venta = precio_venta

                if "precio_venta_pv" in data:
                    precio_venta_pv = list(dict(data)["precio_venta_pv"])
                    pv_precio = list(dict(data)["pv_precio"])

                    precios_diferenciados = []
                    for i, id in enumerate(pv_precio,start=0):
                        pv_d = precio_venta_pv[i]
                        if pv_d != "":
                            precios_diferenciados.append(f"{id}:{pv_d}")

                    new_producto.precios_diferenciados = "|".join(precios_diferenciados)



                new_producto.categoria = categoria
                if medida and str(medida).isnumeric():
                    new_producto.medida = Medida.objects.get(id=medida)
                
                if "producto-compuesto" in data:
                    new_producto.is_compuesto = True
                new_producto.save()
                
                return redirect(str(request.build_absolute_uri()))
            
        except Exception as e:
            print(e)
            return redirect(str(request.build_absolute_uri()))

@method_decorator(login_required, name='dispatch')
class TurnosView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        servicios = Servicio.objects.filter(activo = True)
        clientes = Cliente.objects.filter(fecha_realizacion=None)
        usuarios = UserAccount.objects.filter(salon_permission=True,is_active=True)
        contratos = FichaCliente.objects.filter(fecha_realizacion__isnull = True)

        context = {"servicios":servicios,"clientes":clientes,"usuarios":usuarios,"contratos":contratos}
        return render(request,'salon/turnos.html',context)
    
    def post(self,request,*args,**kwargs):
        data = request.POST
        if "turno-delete-id" in data:
            cliente = Cliente.objects.get(id=data["turno-delete-id"])
            cliente.delete()
            return redirect(str(request.build_absolute_uri()))
        
        user = UserAccount.objects.get(id=data["user-salon"])
        contrato_asociado = data["contrato_asociado"]
        if contrato_asociado != "":
            contrato_id = int(contrato_asociado)
            f_cliente = FichaCliente.objects.get(id=contrato_id)
            nombre = f_cliente.nombre
        else:
            nombre = data["nombre"]
            contrato_id = None
        cliente = Cliente.objects.create(
            nombre = nombre,
            user_id = user.id,
            user_name = user.user,
            contrato_id = contrato_id
        )
        
        if "ci" in data and data["ci"] != "":cliente.ci = data["ci"]
        if "telefono" in data and data["telefono"] != "":cliente.telefono = data["telefono"]
        
        cliente.fecha_acordada = datetime.strptime(data["fecha-acordada"], '%d/%m/%Y')
        if "servicios-ids" in data:
            servicios = list(dict(data)["servicios-ids"])
            for servicio in servicios:
                cliente.servicios.add(Servicio.objects.get(id = servicio))
        cliente.save()

        return redirect(str(request.build_absolute_uri()))
    
    
@method_decorator(login_required, name='dispatch')
class ClientesView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        servicios = Servicio.objects.filter(activo = True)
        fecha_actual = timezone.now().date()

        clientes = Cliente.objects.filter(fecha_realizacion = None, fecha_acordada = fecha_actual, user_id = request.user.id).order_by("fecha_acordada")

        context = {"servicios":servicios,"clientes":clientes}
        
        if "cliente" in data:
            cliente = Cliente.objects.get(id=data["cliente"])
            context["cliente"] = cliente
            
        return render(request,'salon/clientes.html',context)
    
    def post(self,request,*args,**kwargs):
        data_get = request.GET
        data = request.POST

        cliente = Cliente.objects.get(id=data_get["cliente"])
        turno = Turno.objects.get(user=request.user,fin=None)

        conf = ConfigVar.objects.get_or_create(key="precio_usd")
        if conf[1]:
            precio_usd = conf[0]
            precio_usd.value = 270
            precio_usd.save()
            
        precio_usd = conf[0].value

        for k in data:
            if "subproducto" in k:
                cliente_name = f"{cliente.nombre}"
                if cliente.ci: cliente_name += f"- ({cliente.ci})"

                servicio_id,producto_id = data[k].split("-")
                servicio = Servicio.objects.get(id=servicio_id)
                subproduto = CantidadSubproducto.objects.get(id=producto_id)

                cant_servicio = float(data[f"cant-servicio-{servicio_id}"])

                Consumo.objects.create(
                    cliente_name = cliente_name,
                    servicio = servicio.nombre,
                    producto = subproduto.producto,
                    cantidad = subproduto.cantidad * cant_servicio,
                    turno = turno
                )

                

            elif "cant-servicio-" in k:
                cant_servicio = float(data[k])
                servicio_id = k.replace("cant-servicio-","")
                servicio = Servicio.objects.get(id=servicio_id)
                if servicio.pago_relacion == "$":
                    pago = Pago.objects.create(
                        monto_original = servicio.pago_monto * cant_servicio,
                        monto = servicio.pago_monto * cant_servicio,
                        descripcion = f"Por realizar {cliente.servicios_str()} a {cliente.nombre}",
                        user_id = f"U-{request.user.id}",
                        user_name = request.user.user_str()
                    )

                else:
                    pago = Pago.objects.create(
                        monto_original = (servicio.pago_monto/100) * servicio.precio_cup() * cant_servicio,
                        monto = (servicio.pago_monto/100) * servicio.precio_cup() * cant_servicio,
                        descripcion = f"Por realizar {cant_servicio} {servicio.nombre}",
                        user_id = f"U-{request.user.id}",
                        user_name = request.user.user_str()
                    )
                    
                cliente.pagos.add(pago)
        
        cliente.fecha_realizacion = timezone.now()
        cliente.razon_cambio = precio_usd

        if data["moneda"] == "usd":
            monto_cobrado = data["precio_total_final_usd"]
            cliente.monto_base = data["precio_base_final_usd"]
            cliente.monto_cobrado = monto_cobrado
            cliente.moneda = "USD"

            desc = ""
            if not cliente.contrato_id:
                desc = "(Se aplicaron descuentos a cada servicio por el cliente estar asociado a un contrato)"
            
                caja = Caja.objects.get_or_create(name = "CENTRAL",moneda = "USD")[0]
                servicios = cliente.servicios_str()
                Operaciones.objects.create(
                    monto = float(monto_cobrado),
                    motivo = f"Monto cobrado al cliente {cliente.nombre} por los siguientes servicios ofrecidos por el salón: {servicios}",
                    caja = caja
                )

        else:
            monto_cobrado = data["precio_total_final_cup"]
            cliente.monto_base = data["precio_base_final_cup"]
            cliente.monto_cobrado = monto_cobrado
            cliente.moneda = "CUP"

            desc = ""
            if not cliente.contrato_id:
                desc = "(Se aplicaron descuentos a cada servicio por el cliente estar asociado a un contrato)"
            
                caja = Caja.objects.get_or_create(name = "CENTRAL",moneda = "CUP")[0]
                servicios = cliente.servicios_str()
                Operaciones.objects.create(
                    monto = float(monto_cobrado),
                    motivo = f"Monto cobrado al cliente {cliente.nombre} por los siguientes servicios ofrecidos por el salón: {servicios}",
                    caja = caja
                )


        cliente.turno = turno
        cliente.save()
        
        return redirect(str(request.build_absolute_uri()).split("?cliente=")[0])
    

    
@method_decorator(login_required, name='dispatch')
class ClientesAtendidosView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        fecha_actual = timezone.now().date()
        turno = Turno.objects.get(user=request.user,fin=None)
        clientes = Cliente.objects.filter(fecha_realizacion__date = fecha_actual, user_id = request.user.id,turno = turno)
        context = {"clientes":clientes}

        return render(request,'salon/clientes_atendidos.html',context)
    

    
@method_decorator(login_required, name='dispatch')
class TransferenciasView(View):
    def get(self,request,*args,**kwargs):
        turno = Turno.objects.get(user=request.user,fin=None)
        transferencias = Transferencia.objects.filter(Q(receptor_id=f"U-{request.user.id}") & (Q(turno_id=f"S-{turno.id}") | Q(turno_id=None)) & Q(mensaje_cancelacion__isnull = True)).order_by("alta").reverse()
        context = {"transferencias":transferencias}

        return render(request,'salon/transferencias.html',context)
    
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

        return redirect("TransferenciaSalon")
        
@method_decorator(login_required, name='dispatch')
class EntregarTurnoView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET

        turno = Turno.objects.get(user=request.user,fin=None)
        cuadre = turno.datos_cuadre()["cuadre"]
        for c in cuadre:
            c["producto"] = Producto.objects.get(id=c["producto_id"])


        context = {"cuadre":cuadre}

        if Transferencia.objects.filter(receptor_id=f"U-{request.user.id}",turno_id__isnull = True,mensaje_cancelacion=None).exists():            
            context["message"] = "Antes de terminar el turno debe aceptar o cancelar todas las transferencias pendientes"        
        return render(request,'salon/entregar_turno.html',context)
    
    
    def post(self,request,*args,**kwargs):
        data = request.POST
        turno = Turno.objects.get(user=request.user,fin=None)
        turno.cerrar_cuadre()
        turno.fin = timezone.now()
        turno.save()
        

        consumos = Consumo.objects.filter(turno=turno)
        
        for c in consumos:
            cantidad_descontar = c.cantidad
            stock = StockUsuario.objects.filter(producto=id,cantidad_actual__gt=0,user=request.user).order_by("alta")

            for spv in stock:
                if cantidad_descontar == 0: break
                elif cantidad_descontar <= spv.cantidad_actual:
                    c.cliente.costo += (cantidad_descontar * spv.lote.costo_real())
                    spv.cantidad_actual -= cantidad_descontar
                    if spv.cantidad_actual == 0:
                        spv.activo = False
                    spv.save()
                    cantidad_descontar = 0
                else:
                    cantidad_descontar -= spv.cantidad_actual
                    c.cliente.costo += (spv.cantidad_actual * spv.lote.costo_real())
                    spv.cantidad_actual = 0
                    spv.activo = False
                    spv.save()

        return redirect("http://" + str(request.get_host()) + "/logout/?for=salon")
    

    
@method_decorator(login_required, name='dispatch')
class GestionTurnosView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        usuarios = UserAccount.objects.filter(salon_permission=True,is_active=True)

        if "inicio" in data.keys() and "fin" in data.keys():
            inicio = datetime.strptime(data["inicio"], '%d/%m/%Y')
            fin = datetime.strptime(data["fin"], '%d/%m/%Y')
        else:
            fin = datetime.now().date()
            inicio = fin - timedelta(days=2)

        if "user" in data.keys():
            usuario_select = UserAccount.objects.get(id=data["user"])
        else:
            usuario_select = usuarios.first()

        turnos = Turno.objects.filter(
            (Q(inicio__date__range=[inicio, fin]) |
            Q(fin__date__range=[inicio, fin]))
        ).order_by("-inicio")
        
        if "user" in data.keys():
            turno_select = Turno.objects.get(id=data["turno"])
        elif turnos.count() > 0:
            turno_select = turnos.first()
        else:
        
            turno_select = Turno.objects.filter(
                Q(inicio__lte = fin)
            ).order_by("-inicio").first()
            inicio = turno_select.inicio
            turnos = Turno.objects.filter(
                (Q(inicio__date__range=[inicio, fin]) |
                Q(fin__date__range=[inicio, fin]))
            ).order_by("-inicio")
            
        if "opc" in data.keys() and data["opc"] != "": 
            opcion = data["opc"]
        else: 
            opcion = "cuadre"

        cuadre = None
        clientes = None
        consumo = None
        notas = None

        if opcion == "cuadre":
            cuadre = turno_select.datos_cuadre()["cuadre"]
            for c in cuadre: c["producto"] = Producto.objects.get(id=c["producto_id"])
        if opcion == "clientes":
            clientes = Cliente.objects.filter(turno = turno_select)
        if opcion == "consumo":
            consumo = Consumo.objects.filter(turno=turno_select)
        if opcion == "notas":
            notas = turno_select.datos_cuadre()["notas"]
            for c in notas: c["producto"] = Producto.objects.get(id=c["producto_id"])

        context = {
            "cuadre":cuadre,
            "clientes":clientes,
            "consumo":consumo,
            "notas":notas,
            "turnos":turnos,
            "turno_select":turno_select,
            "usuario_select":usuario_select,
            "usuarios":usuarios,
            "inicio":inicio.strftime('%d/%m/%Y'),
            "fin":fin.strftime('%d/%m/%Y'),
            "inicio_url":inicio.strftime('%d/%m/%Y').replace("/","%2F"),
            "fin_url":fin.strftime('%d/%m/%Y').replace("/","%2F"),
            }        
        return render(request,'salon/gestion_turnos.html',context)
    