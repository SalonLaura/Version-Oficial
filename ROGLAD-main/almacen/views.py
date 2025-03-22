import threading
from django.shortcuts import render,redirect
from django.views import View
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from almacen.models import CambiosAlmacen, Nota, Turno
from bot.bot import send_message
from bussiness.models import AlertaAdmin, Almacen, Descuentos, InformeRecepcion, Producto, StockAlmacen, StockPuntoVenta, Transferencia

@method_decorator(csrf_exempt, name='dispatch')
class RecibirTurnoView(View):
    def get(self,request,*args,**kwargs):
        stock_almacenes = []
        almacenes = Almacen.objects.filter(activo=True)
        for a in almacenes:
            product_ids = []
            productos = []
            stock = StockAlmacen.objects.filter(activo=True,almacen = a).exclude(cantidad_actual=None).order_by("producto__nombre")
            for s in stock:
                if s.producto.id not in product_ids:
                    productos.append(s)
                    product_ids.append(s.producto.id)
                else:
                    productos[product_ids.index(s.producto.id)].cantidad_actual += s.cantidad_actual
            
            stock_almacenes.append({
                "stock":productos,
                "almacen":a
            })

        turno = Turno.objects.all().last()
        
        context = {
            "stock_almacenes":stock_almacenes,
            "turno_anterior":turno,
            }

        return render(request,'almacen/recibir_turno.html',context)
     
    def post(self,request,*args,**kwargs):
        #try:
            data = request.POST
            print(data)
            try: turno_saliente = Turno.objects.latest("fin")
            except: turno_saliente =  None

            #turno = Turno.objects.get_or_create(
            #    user=request.user,
            #    fin = None
            #)
            print(turno_saliente.almacen)
            if turno_saliente:
                
                if "motivos-ajuste" in data.keys() and "id-producto" in data.keys() and "cantidad-ajuste" in data.keys():
                    motivos_ajuste = list(dict(data)["motivos-ajuste"])
                    id_producto = list(dict(data)["id-producto"])
                    cantidad_ajuste = list(dict(data)["cantidad-ajuste"])
                    new_cant_ajuste = list(dict(data)["new-cant-ajuste"])
                    id_almacen = list(dict(data)["id-almacen"])
                    

                    try:
                        for index,motivo in enumerate(motivos_ajuste,start=0):
                            product = Producto.objects.get(id=id_producto[index])
                            stock = StockAlmacen.objects.filter(producto__id=id_producto[index],almacen__id = id_almacen[index]).order_by("alta")
                            if stock.exists():
                                existencia = 0
                                for s in stock:existencia+= s.cantidad_actual
                                cantidad = float(new_cant_ajuste[index]) - existencia
                                
                                CambiosAlmacen.objects.create(
                                    producto = product,
                                    almacen = Almacen.objects.get(id=id_almacen[index]),
                                    existencia = existencia + cantidad,
                                    cantidad = cantidad,
                                    motivo = motivo,
                                )
                                monto = cantidad * stock.first().costo_real()
                                
                                causa = f"Sobra {cantidad} {product.medida.abreviatura} de {product.nombre}"
                                if monto < 0: 
                                    causa = f"Falta {cantidad*-1} {product.medida.abreviatura} de {product.nombre}"
                                    monto *= -1

                                Nota.objects.create(
                                    cantidad = cantidad,
                                    causa = causa,
                                    motivo = motivo,
                                    turno = turno_saliente,
                                    monto = monto,
                                )

                                cantidad_descontar = cantidad * (-1)

                                if cantidad_descontar > 0:
                                    for s in stock:
                                        if cantidad_descontar == 0: break
                                        elif cantidad_descontar <= s.cantidad_actual:
                                            s.cantidad_actual -= cantidad_descontar
                                            if s.cantidad_actual == 0:
                                                s.activo = False
                                            s.save()
                                            cantidad_descontar = 0
                                        else:
                                            cantidad_descontar -= s.cantidad_actual
                                            s.cantidad_actual = 0
                                            s.activo = False
                                            s.save()
                                else:
                                    cantidad_descontar *= -1 
                                    for s in stock:
                                        if cantidad_descontar == 0: break
                                        elif s.cantidad_actual + cantidad_descontar <= s.cantidad_inicial:
                                            s.cantidad_actual += cantidad_descontar
                                            s.activo = True
                                            s.save()
                                            cantidad_descontar = 0
                                            break
                                        else:
                                            cantidad_descontar -= (s.cantidad_inicial - s.cantidad_actual)
                                            s.cantidad_actual = s.cantidad_inicial
                                            s.activo = True
                                            s.save()

                                    if cantidad_descontar > 0:
                                        s = stock.first()
                                        s.cantidad_actual += cantidad_descontar
                                        s.activo = True
                                        s.save()
                                        
                                        cantidad_descontar = 0
                        
                    
                                if product.precio_venta:monto = cantidad * float(product.precio_venta)
                                else:monto = cantidad * float(stock.first().costo_real())

                                if monto < 0: 
                                    monto *= -1
                                    Descuentos.objects.create(
                                        monto_original = monto,
                                        monto = monto,
                                        descripcion = f"Faltan {cantidad*-1} {product.medida.abreviatura} de {product.nombre}",
                                        motivo = motivo,
                                        user_id = f"U-{turno_saliente.user.id}",
                                        user_name = turno_saliente.user.user
                                    )
                    except Exception as e:
                        print(f"Error al guardar notas: {e}")
                    
                    alm = Almacen.objects.get(id=id_almacen[index])
                    alert = AlertaAdmin.objects.create(
                        tipo=False,
                        centro_costo = f"A-{id_almacen[index]}",
                        motivo = f"Cambio de turno de almacenero ({request.user}) en {alm.nombre} efectuado con {len(motivos_ajuste)} incidencias."
                    )
                    
                    message = f"<b>📦 {alm.nombre}</b>\n\n"
                    message += f"Cambio de turno de almacenero ({request.user}) en {alm.nombre} efectuado con {len(motivos_ajuste)} incidencias."
                    
                    t = threading.Thread(target=lambda:send_message(message,alert.id))
                    t.start()
                    
                        
                else:
                    alm = Almacen.objects.get(id=turno_saliente.almacen.id)
                    alert = AlertaAdmin.objects.create(
                        tipo=None,
                        centro_costo = f"A-all",
                        motivo = f"Cambio de turno de almacenero ({request.user}) en {alm.nombre} efectuado sin incidencias."
                    )
                    
                    message = f"<b>📦 {alm.nombre}</b>\n\n"
                    message += f"Cambio de turno de almacenero ({request.user}) en {alm.nombre} efectuado sin incidencias."
                    
                    t = threading.Thread(target=lambda:send_message(message,alert.id))
                    t.start()

            return redirect("StockAlmacen")
        
        #except Exception as e:
        #    print("Error en el cuadre: ",e)
        #    return redirect("RecibirTurnoAlmacen")


class EntregarTurnoView(View):
    def get(self,request,*args,**kwargs):

        turno = Turno.objects.filter(user=request.user,fin = None).first()

        if not turno:
            return redirect("logout")
        
        entradas = []
        salidas = []

        almacenes = Almacen.objects.filter(activo=True)
        for a in almacenes:

            cambios = CambiosAlmacen.objects.filter(
                almacen=a,
                fecha__gte = turno.inicio,
                cantidad__gt = 0
            )
            for c in cambios:
                entradas.append({
                    "nombre":c.producto.nombre,
                    "medida":c.producto.medida.nombre,
                    "almacen":a.nombre,
                    "cantidad":c.cantidad,
                    "fecha":c.fecha,
                    "existencia":c.producto.existencia(a.id),
                })

            informes_recepcion = InformeRecepcion.objects.filter(
                almacen=a,
                fecha__gte = turno.inicio
            )
            for ir in informes_recepcion:
                stock = StockAlmacen.objects.filter(informe_recepcion = ir)
                for s in stock:
                    entradas.append({
                        "nombre":s.producto.nombre,
                        "medida":s.producto.medida.nombre,
                        "almacen":a.nombre,
                        "cantidad":s.cantidad_inicial,
                        "fecha":ir.fecha,
                        "existencia":s.producto.existencia(a.id),
                    })
            
            transferencias_recibidas = Transferencia.objects.filter(
                receptor_id=f"A-{a.id}",
                alta__gte = turno.inicio
            ).order_by("-alta")
            
            for t in transferencias_recibidas:
                stock = StockAlmacen.objects.filter(transferencia = t)
                for s in stock:
                    entradas.append({
                        "nombre":s.producto.nombre,
                        "medida":s.producto.medida.nombre,
                        "almacen":a.nombre,
                        "cantidad":s.cantidad_inicial,
                        "fecha":t.alta,
                    })


                
            cambios = CambiosAlmacen.objects.filter(
                almacen=a,
                fecha__gte = turno.inicio,
                cantidad__lt = 0
            )
            for c in cambios:
                salidas.append({
                    "nombre":c.producto.nombre,
                    "medida":c.producto.medida.nombre,
                    "almacen":a.nombre,
                    "cantidad":c.cantidad*(-1),
                    "fecha":c.fecha,
                    "existencia":c.producto.existencia(a.id),
                })

            transferencias = Transferencia.objects.filter(
                emisor_id=f"A-{a.id}",
                alta__gte = turno.inicio
            ).order_by("-alta")
            
            for t in transferencias:
                if "PV-" in t.receptor_id:
                    stock = StockPuntoVenta.objects.filter(transferencia = t)
                    for s in stock:
                        salidas.append({
                            "nombre":s.producto.nombre,
                            "medida":s.producto.medida.nombre,
                            "almacen":a.nombre,
                            "cantidad":s.cantidad_inicial,
                            "fecha":t.alta,
                            "existencia":s.producto.existencia(a.id),
                        })

                elif "C-" in t.receptor_id:
                    stock = t.cocinaTransferencia.all()
                    for s in stock:
                        salidas.append({
                            "nombre":s.producto.nombre,
                            "medida":s.producto.medida.nombre,
                            "almacen":a.nombre,
                            "cantidad":s.cantidad_inicial,
                            "fecha":t.alta,
                            "existencia":s.producto.existencia(a.id),
                        })

                elif "A-" in t.receptor_id:
                    stock = StockAlmacen.objects.filter(transferencia = t)
                    for s in stock:
                        salidas.append({
                            "nombre":s.producto.nombre,
                            "medida":s.producto.medida.nombre,
                            "almacen":a.nombre,
                            "cantidad":s.cantidad_inicial,
                            "fecha":t.alta,
                            "existencia":s.producto.existencia(a.id),
                        })
            
        salidas_ordenadas = sorted(salidas, key=lambda x: x["fecha"])
        entradas_ordenadas = sorted(entradas, key=lambda x: x["fecha"])
        
        context = {"salidas":salidas_ordenadas,"entradas":entradas_ordenadas}

        if InformeRecepcion.objects.filter(date_confirm__isnull=True).exists():
            context["message"] = "Tiene inoformes de recepción pendientes a ser atendidos"

        elif Transferencia.objects.filter(receptor_id__icontains=f"A-",date_confirm__isnull=True):
            context["message"] = "Tienes transferencias pendientes a ser atendidas"

        elif Transferencia.objects.filter(emisor_id__icontains=f"A-",date_confirm__isnull=True):
            context["message"] = "Ha realizado transferencias pendientes a ser atendidas"



        return render(request,'almacen/entregar_turno.html',context)
  

    def post(self,request,*args,**kwargs):
        data = request.POST
        turno = Turno.objects.filter(user=request.user,fin = None).first()
        turno.fin = timezone.now()
        turno.save()
        return  redirect("logout")