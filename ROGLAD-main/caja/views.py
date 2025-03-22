import json
import random
import threading
from django.shortcuts import redirect, render
from django.views import View
from django.db.models import Q,Sum
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import timedelta,datetime
from bot.bot import send_message
from bussiness.models import AlertaAdmin, Almacen, Descuentos, Pago, PuntoVenta, StockAlmacen, StockPuntoVenta, Turno, UserAccount
from kitchen.models import Cocina, StockCocina, Turno as TurnoCocina
from bussiness.utils import get_days_in_month, login_required, toMoney
from caja.models import Caja, Capital, CapitalLiquides, GastoMensual, Operaciones, ReciboEfectivo ,Nomina
from django.contrib import messages

from estudio.models import Editor, FichaCliente, Fotografo
from salon.models import Cliente


@method_decorator(login_required, name='dispatch')
class OperacionesView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        Caja.objects.get_or_create(name = "CENTRAL",moneda = "CUP")[0]
        Caja.objects.get_or_create(name = "CENTRAL",moneda = "USD")[0]
        Caja.objects.get_or_create(name = "CENTRAL",moneda = "MLC")[0]
        Caja.objects.get_or_create(name = "CENTRAL",moneda = "EUR")[0]

        if "inicio" in data.keys() and "fin" in data.keys():
            inicio = datetime.strptime(data["inicio"], '%d/%m/%Y')
            fin = datetime.strptime(data["fin"], '%d/%m/%Y')
        else:
            fin = datetime.now().date()
            inicio = fin - timedelta(days=2)

        if request.user.super_permission:
            cajas = Caja.objects.all()
        else:
            cajas = Caja.objects.filter(Q(name__icontains = "CENTRAL"))

        if "caja" in data and data["caja"] != "":
            caja_select = cajas.get(id=data["caja"])
        else:
            caja_select = cajas.first()

        operaciones = Operaciones.objects.filter(fecha__date__range=[inicio, fin],caja=caja_select,existencia__isnull=False).order_by("-fecha")
        
        if "registros" in data and data["registros"] == "si":
            operaciones = operaciones.filter(monto__gt = 0)
            registros = "si"
        elif "registros" in data and data["registros"] == "se":
            operaciones = operaciones.filter(monto__lt = 0)
            registros = "se"
        else:
            
            operaciones = list(Operaciones.objects.filter(fecha__date__range=[inicio, fin],caja=caja_select,existencia__isnull=True).order_by("-fecha")) + list(operaciones)
            registros = "all"

        context = {
            "caja_select":caja_select,
            "cajas":cajas,
            "inicio":inicio.strftime('%d/%m/%Y'),
            "fin":fin.strftime('%d/%m/%Y'),
            "operaciones":operaciones,
            "registros":registros
            }

        return render(request,'caja/operaciones.html',context)

    def post(self,request,*args,**kwargs):
        data = request.POST

        caja = Caja.objects.get(id=data["caja-add-id"])

        if "operacion-id" in data:
            operacion = Operaciones.objects.get(id=data["operacion-id"])
            caja.monto += operacion.monto
            caja.save()
            operacion.existencia = caja.monto
            operacion.fecha = timezone.now()
            operacion.save()
            return redirect(str(request.build_absolute_uri()))


        monto = float(data["monto-agregado"])
        if monto > 0:
            if "add-monto" in data:
                caja.monto += monto
                caja.save()
                motivo = data["motivo-caja-add"]
                Operaciones.objects.create(
                    caja = caja,
                    existencia = caja.monto,
                    monto = monto,
                    motivo = f"Efectivo ingresado manualmente por {request.user.user}. Motivo del ingreso: {motivo}",
                )
                messages.success(request, f'Efectivo ingresado satisfactoriamente a {caja.name}({caja.moneda})')
            else:
                motivo = data["motivo-caja-add"]
                if caja.monto == 0:
                    messages.error(request, 'El saldo en la caja es de $0.00, por lo que no puede realizar retiros.')
                elif caja.monto >= monto:
                    caja.monto -= monto
                    caja.save()
                    
                    alert = AlertaAdmin.objects.create(
                        tipo=True,
                        centro_costo = f"CAJA",
                        motivo = f"Se ha egresado manualmente ${toMoney(monto)} de {caja.name}({caja.moneda})"
                    )
                    
                    message = f"<b>💸 CAJA</b>\n\n"
                    message += f"Se ha egresado manualmente ${toMoney(monto)} de {caja.name}({caja.moneda})"
                    
                    t = threading.Thread(target=lambda:send_message(message,alert.id))
                    t.start()
                        
                    Operaciones.objects.create(
                        caja = caja,
                        existencia = caja.monto,
                        monto = monto*-1,
                        motivo = f"Efectivo egresado manualmente por {request.user.user}. Motivo del retiro: {motivo}",
                    )
                    messages.success(request, f'Efectivo retirado satisfactoriamente de la caja {caja.name}({caja.moneda})')
                else:
                    monto_retirado = caja.monto
                    Operaciones.objects.create(
                        caja = caja,
                        existencia = 0,
                        monto = monto_retirado*-1,
                        motivo = f"Efectivo egresado manualmente por {request.user.user}. Motivo del retiro: {motivo}",
                    )
                    
                    alert = AlertaAdmin.objects.create(
                        tipo=True,
                        centro_costo = f"CAJA",
                        motivo = f"Se ha egresado manualmente ${toMoney(monto_retirado)} de la caja {caja.name}({caja.moneda})"
                    )
                    
                    message = f"<b>💸 CAJA</b>\n\n"
                    message += f"Se ha egresado manualmente ${toMoney(monto_retirado)} de la caja {caja.name}({caja.moneda})"
                    
                    t = threading.Thread(target=lambda:send_message(message,alert.id))
                    t.start()

                    caja.monto = 0
                    caja.save()
                    monto_retirado = toMoney(monto_retirado)
                    messages.error(request, f'Solo se ha podido retirar ${monto_retirado} de {caja.name}({caja.moneda}) por falta de liquides.')

        return redirect(str(request.build_absolute_uri()))


@method_decorator(login_required, name='dispatch')
class ReciboEfectivoView(View):
    def get(self,request,*args,**kwargs):
        recibos = ReciboEfectivo.objects.filter(fecha_confirmacion = None).order_by("fecha")
        context = {"recibos":recibos}

        return render(request,'caja/recibo_efectivo.html',context)
    
    def post(self,request,*args,**kwargs):
        data = request.POST

        recibo = ReciboEfectivo.objects.get(id=data["id-recibo"])
        recibo.fecha_confirmacion = timezone.now()
        recibo.save()

        caja = Caja.objects.get_or_create(name = "CENTRAL",moneda = "CUP")[0]
        caja.monto += recibo.monto
        caja.save()

        turno = recibo.turno()

        if recibo.monto > 0:
            Operaciones.objects.create(
                caja = caja,
                existencia = caja.monto,
                monto = recibo.monto,
                motivo = f"Efectivo recibido desde cierre de turno en {turno.punto_venta} correspondiente al turno de {turno.user.user_str()}",
            )

        return redirect('ReciboEfectivoCaja')


@method_decorator(login_required, name='dispatch')
class HistorialReciboView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        if "inicio" in data.keys() and "fin" in data.keys():
            inicio = datetime.strptime(data["inicio"], '%d/%m/%Y')
            fin = datetime.strptime(data["fin"], '%d/%m/%Y')
        else:
            fin = datetime.now().date()
            inicio = fin - timedelta(days=2)
        
        recibos = ReciboEfectivo.objects.filter(fecha_confirmacion__date__range=[inicio, fin]).order_by("fecha")
        context = {
            "inicio":inicio.strftime('%d/%m/%Y'),
            "fin":fin.strftime('%d/%m/%Y'),
            "recibos":recibos}
        return render(request,'caja/historial_recibo.html',context)

@method_decorator(login_required, name='dispatch')
class SalariosView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        if "fin" in data.keys():
            fin = datetime.strptime(data["fin"], '%d/%m/%Y').replace(hour=23, minute=59, second=59)
        else:
            fin = timezone.now().replace(hour=23, minute=59, second=59)
            #fin = datetime.combine(fecha_actual, datetime.min.time()) + timedelta(hours=23, minutes=59, seconds=59)
        
        pending_prenomina = Nomina.objects.filter(user_confirm = None).exists()
        if pending_prenomina and "select" not in data:
            open_nomina = Nomina.objects.filter(user_confirm = None).first()
            return redirect(str(request.build_absolute_uri()) + f"?select={open_nomina.id}-nom")

        nomina_select = None
        users_return = [] 
        monto_pagar = 0

        if ("select" in data and data["select"] != "pendientes"):
            nomina_select = Nomina.objects.get(id = data["select"].replace("-nom",""))
        else:
            users = UserAccount.objects.all()
            for u in users:
                u.get_pagos = u.pagos(fin)
                u.get_descuentos = u.descuentos(fin)
                u.get_pago_acumulado = u.pago_acumulado(fin)
                u.get_monto_descontar = u.monto_descontar(fin)
                u.get_monto_pagar = u.monto_pagar(fin)
                users_return.append(u)
                monto_pagar += u.get_monto_pagar

            fotografo = Fotografo.objects.all()
            for u in fotografo:
                u.get_pagos = u.pagos(fin)
                u.get_descuentos = u.descuentos(fin)
                u.get_pago_acumulado = u.pago_acumulado(fin)
                u.get_monto_descontar = u.monto_descontar(fin)
                u.get_monto_pagar = u.monto_pagar(fin)
                users_return.append(u)
                monto_pagar += u.get_monto_pagar

            """editor = Editor.objects.all()
            for u in editor:
                u.get_pagos = u.pagos(fin)
                u.get_descuentos = u.descuentos(fin)
                u.get_pago_acumulado = u.pago_acumulado(fin)
                u.get_monto_descontar = u.monto_descontar(fin)
                u.get_monto_pagar = u.monto_pagar(fin)
                users_return.append(u)
                monto_pagar += u.get_monto_pagar"""



        nominas = Nomina.objects.all().order_by("-fecha")

        context = {
                    "fin":fin.strftime('%d/%m/%Y'),
                    "nomina_select":nomina_select,
                    "usuarios":users_return,
                    "monto_pagar":monto_pagar,
                    "nominas":nominas,
                    "pending_prenomina":pending_prenomina
                }

        return render(request,'caja/salarios.html',context)
    
    def post(self,request,*args,**kwargs):
        data = request.POST
        url = str(request.build_absolute_uri())

        if "denegar-id" in data:
            nomina = Nomina.objects.get(id=data["denegar-id"])
            nomina.delete()

            return redirect("SalariosCaja")
        
        elif "comfirm-id" in data:
            nomina = Nomina.objects.get(id=data["comfirm-id"])
            pagos = nomina.pagos.all()
            monto_pagos = 0.0
            for pago in pagos:
                monto_pagos += pago.monto
                pago.liquidado = pago.monto
                pago.fecha_liquidacion = timezone.now()
                pago.save()
            descuentos = nomina.descuentos.all()
            for descuento in descuentos:
                if monto_pagos <= 0 :
                    break
                
                elif monto_pagos - (descuento.monto-descuento.liquidado) >= 0:
                    descuento.liquidado = descuento.monto
                    descuento.fecha_liquidacion = timezone.now()
                    descuento.save()
                    monto_pagos -= descuento.monto

                else:                    
                    descuento.liquidado += monto_pagos
                    descuento.save()
                    monto_pagos = 0

            nomina.user_confirm = request.user.user_str()
            nomina.save()
            nom_name = nomina.nombre()
            nom_monto = float(nomina.datos_nomina()["total"])
            caja = Caja.objects.get_or_create(name = "CENTRAL",moneda = "CUP")[0]
            caja.monto += (nom_monto*-1)
            caja.save()
            Operaciones.objects.create(
                caja = caja,
                existencia = caja.monto,
                monto = nom_monto*-1,
                motivo = f"Efectivo egresado por {request.user.user}. Motivo del egreso: Pago de salario correspondiente a la nómina {nom_name}.",
            )
            return redirect(str(request.build_absolute_uri()))

        elif "add-pago" in data.keys():
            if "U-" in data["user-monto-agregado"]:
                user = UserAccount.objects.get(id=data["user-monto-agregado"].split("-")[1]).user
            if "F-" in data["user-monto-agregado"]:
                user = Fotografo.objects.get(id=data["user-monto-agregado"].split("-")[1]).nombre

            pago = Pago.objects.create(
                monto_original = data["monto-agregado"],
                monto = data["monto-agregado"],
                liquidado = 0,
                descripcion = data["motivo-pago"],
                user_id = data["user-monto-agregado"],
                user_name = user
            )
            url = url.replace("&s=desc","")

        elif "add-descuento" in data.keys():
            if "U-" in data["user-monto-agregado"]:
                user = UserAccount.objects.get(id=data["user-monto-agregado"].split("-")[1]).user
            if "F-" in data["user-monto-agregado"]:
                user = Fotografo.objects.get(id=data["user-monto-agregado"].split("-")[1]).nombre

            pago = Descuentos.objects.create(
                monto_original = data["monto-agregado"],
                monto = data["monto-agregado"],
                liquidado = 0,
                descripcion = "Descuento efectuado manualmente",
                motivo = data["motivo-pago"],
                user_id = data["user-monto-agregado"],
                user_name = user
            )
            
            if "?u=" in url and "&s=desc" not in url:
                url += "&s=desc"

        elif "pago-id" in data.keys():
            pago = Pago.objects.get(id=data["pago-id"])
            pago.monto = data["monto-modificado"]
            pago.save()

        elif "descuento-id" in data.keys():
            descuento = Descuentos.objects.get(id=data["descuento-id"])
            descuento.monto = data["monto-modificado"]
            descuento.save()
            url += "&s=desc"


        return redirect(url)


@method_decorator(login_required, name='dispatch')
class EstadoCapitalView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        total = 0.0

        if "inicio" in data.keys() and "fin" in data.keys():
            inicio = datetime.strptime(data["inicio"], '%d/%m/%Y')
            fin = datetime.strptime(data["fin"], '%d/%m/%Y')
        else:
            fin = datetime.now().date()
            inicio = fin - timedelta(days=2)

        date = timezone.now()

        centros_costo = []
        pvs = PuntoVenta.objects.filter(activo=True)
        for pv in pvs: 
            centros_costo.append(
                {
                    "id":f"PV-{pv.id}",
                    "n":"Punto de venta " + pv.nombre
                }
            )
            capital = 0
            stock = StockPuntoVenta.objects.filter(punto_venta=pv,cantidad_actual__gt=0)
            for s in stock:
                try:
                    capital += (s.cantidad_actual * s.producto.get_precios_diferenciados(pv.id))
                except:pass

            if Capital.objects.filter(centro_costo = f"PV-{pv.id}",fecha = date).exists():
                c = Capital.objects.filter(centro_costo = f"PV-{pv.id}", fecha = date).first()
                c.monto = round(capital,2)
                c.save()
            else:
                Capital.objects.create(
                    centro_costo = f"PV-{pv.id}",
                    monto = round(capital,2)
                )

        almacenes = Almacen.objects.filter(activo=True)
        for a in almacenes: 
            centros_costo.append(
                {
                    "id":f"A-{a.id}",
                    "n":"Almacén " + a.nombre
                }
            )
            capital = 0
            stock = StockAlmacen.objects.filter(almacen=a,cantidad_actual__gt=0)
            for s in stock:
                capital += (s.cantidad_actual * s.costo_real())

            if Capital.objects.filter(centro_costo = f"A-{a.id}",fecha = date).exists():
                c = Capital.objects.filter(centro_costo = f"A-{a.id}", fecha = date).first()
                c.monto = round(capital,2)
                c.save()
            else:
                Capital.objects.create(
                    centro_costo = f"A-{a.id}",
                    monto = round(capital,2)
                )

        cocinas = Cocina.objects.filter(activo=True)
        for c in cocinas: 
            centros_costo.append(
                {
                    "id":f"C-{c.id}",
                    "n":"Cocina " + c.nombre
                }
            )
            capital = 0
            stock = StockCocina.objects.filter(cocina=c,cantidad_actual__gt=0)
            for s in stock:
                capital += (s.cantidad_actual * s.costo_cup())

            if Capital.objects.filter(centro_costo = f"C-{c.id}",fecha = date).exists():
                c = Capital.objects.filter(centro_costo = f"C-{c.id}", fecha = date).first()
                c.monto = round(capital,2)
                c.save()
            else:
                Capital.objects.create(
                    centro_costo = f"C-{c.id}",
                    monto = round(capital,2)
                )

        series = [ ]

        fechas = []
        fecha_actual = inicio
        while fecha_actual <= fin:
            fechas.append(fecha_actual)
            fecha_actual += timedelta(days=1)

        lista_colores = [f"#{random.randint(0, 0xFFFFFF):06x}" for _ in range(len(centros_costo))]

        if CapitalLiquides.objects.filter(fecha = date).exists():
            capital_liquides = CapitalLiquides.objects.filter(fecha = date).first()
        else:
            capital_liquides = CapitalLiquides.objects.create(
                capital = 0.0,
                liquides = 0.0
            )

        for i,cc in enumerate(centros_costo,start=0):
            data = []
            for fecha in fechas:
                capital = Capital.objects.filter(fecha=fecha,centro_costo = cc["id"])
                
                if capital.exists():
                    data.append(capital.first().monto)
                else:
                    data.append(0.0)

            series.append({
                "name": cc["n"],
                "data": data,
                "color": lista_colores[i],
            })

            total += sum(data)

        capital_liquides.capital = total
        capital_liquides.liquides = Caja.objects.get_or_create(name = "CENTRAL",moneda = "CUP")[0].monto
        capital_liquides.save()
        
        data_liquides = []
        data_capital = []
        data_total = []
        for fecha in fechas:
            capital = CapitalLiquides.objects.filter(fecha=fecha)            
            if capital.exists():
                c = capital.first()
                data_liquides.append(c.liquides)
                data_capital.append(c.capital)
                data_total.append(c.liquides + c.capital)
            else:
                data_liquides.append(0.0)
                data_capital.append(0.0)
                data_total.append(0.0)

        series2 = []
        series2.append({
            "name": "Monto total",
            "data": data_total,
            "color": "#31C48D",
        })
        series2.append({
            "name": "Monto en capital",
            "data": data_capital,
            "color": "#1A56DB",
        })
        series2.append({
            "name": "Liquides en caja (CUP)",
            "data": data_liquides,
            "color": "#7E3AF2",
        })

        total_liquides = sum(data_liquides)

        for s in series:
            if sum(s["data"]) == 0.0:
                series.remove(s)
                
        context = {
            "fechas":fechas,
            "series":series,
            "inicio":inicio.strftime('%d/%m/%Y'),
            "fin":fin.strftime('%d/%m/%Y'),
            "total":total,
            "total_liquides":total_liquides,
            "series2":series2
        }

        return render(request,'caja/estado_capital.html',context)



@method_decorator(login_required, name='dispatch')
class EstadoLiquidesView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET

        meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]

        if "periodo" not in data.keys():
            year = timezone.now().year
            month = timezone.now().month
        else:
            periodo = data["periodo"].split("-")
            year = periodo[0]
            month = periodo[1]

        if "cc" not in data.keys():
            centro_costo = "all"
        else:
            centro_costo = data["cc"]
        


        if "type" not in data.keys():
            tipo_contabilidad = "f"
        else:
            tipo_contabilidad = data["type"]
        

        
        pagos = []
        inversion_semana_total = 0
        monto_semana_total = 0
        impuestos_10_total = 0
        impuestos_1_total = 0
        impuestos_35_total = 0
        impuestos_semana_total = 0
        
        pago_total = 0.0
        pagos_909_total = 0.0

        contratos_list = []
        semanas = []
        clientes_salon_list = []

        s = 1
        cant_dias = get_days_in_month(int(year),int(month))
        
        """if centro_costo == "all":

            puntos_ventas = PuntoVenta.objects.filter(activo=True)

            for pv in puntos_ventas:
                turnos = Turno.objects.filter(fin__year=year, fin__month=month)
                imp_10 = 0
                imp_1 = 0
                imp_35 = 0
                inversion = 0
                monto = 0
                impuestos = 0

                for turno in turnos:
                    
                    if tipo_contabilidad == "r" or tipo_contabilidad == "p":
                        inversion += turno.coste_productos()
                        monto += turno.monto
                    else:
                        inversion += turno.coste_productos(False)
                        monto += turno.monto_ext

                    if tipo_contabilidad == "f" or tipo_contabilidad == "r":
                        impuestos += turno.impuestos_ventas()
                        imp_01,imp_001,imp_035 = turno.impuestos_ventas_list()
                    elif tipo_contabilidad == "p":
                        impuestos += turno.impuestos_ventas(True)
                        imp_01,imp_001,imp_035 = turno.impuestos_ventas_list(True)

                    imp_10 += imp_01
                    imp_1 += imp_001
                    imp_35 += imp_035
                    
                    
                margen = monto-(impuestos + inversion)
                if monto>0:margen_porcent = (margen*100)/monto 
                else:margen_porcent =  monto
                contrato_data = {
                    "pv":pv.nombre,
                    "imp_10":imp_10,
                    "imp_1":imp_1,
                    "imp_35":imp_35,
                    "inversion":inversion,
                    "monto":monto,
                    "impuestos":impuestos,
                    "margen":margen,
                    "margen_porcent":round(margen_porcent,2)
                }  
        """

        if "C-" in centro_costo or centro_costo == "all":
            _pagos = 0.0
            _pagos_909 = 0.0
            for v in [7,14,21,28,35]:

                inversion_semana = 0
                monto_semana = 0
                impuestos_10 = 0
                impuestos_1 = 0
                impuestos_35 = 0
                impuestos_semana = 0
                dias=[]

                for d in range(s, v + 1):
                    if d > cant_dias:
                        break

                    inversion = 0
                    impuestos = 0
                    monto = 0
                    
                    imp_1= 0
                    imp_10= 0
                    imp_35= 0

                    turnos = TurnoCocina.objects.filter(fin__year=year, fin__month=month, fin__day=d)
                    if "C-" in centro_costo:
                        turnos = turnos.filter(cocina__id = centro_costo.replace("C-",""))

                    for turno in turnos:
                        
                        for p in turno.pagos.all():
                            _pagos += p.monto_original
                            if "U-" in p.user_id and UserAccount.objects.get(id= p.user_id.replace("U-","")).pago_909:
                                _pagos_909 += p.monto_original

                        if tipo_contabilidad == "r" or tipo_contabilidad == "p":
                            inversion += turno.coste_productos()
                            monto += turno.monto
                        else:
                            inversion += turno.coste_productos(False)
                            monto += turno.monto_ext()

                        if tipo_contabilidad == "f" or tipo_contabilidad == "r":
                            impuestos += turno.impuestos_ventas()
                            imp_01,imp_001,imp_035 = turno.impuestos_ventas_list()
                        elif tipo_contabilidad == "p":
                            impuestos += turno.impuestos_ventas(True)
                            imp_01,imp_001,imp_035 = turno.impuestos_ventas_list(True)

                        imp_10 += imp_01
                        imp_1 += imp_001
                        imp_35 += imp_035

                    impuestos_detalles = [
                        {
                            "n":"10% sobre venta",
                            "v":imp_10
                        },
                        {
                            "n":"1%  sobre venta",
                            "v":imp_1
                        },
                    ]
                    
                    margen = monto-(impuestos + inversion)
                    if monto>0:margen_porcent = (margen*100)/monto 
                    else:margen_porcent =  monto
                    dias.append({
                        #"turnos":turnos,
                        "fecha":f"{d} de {meses[int(month) - 1]} de {year}",
                        "inversion":inversion,
                        "monto":monto,
                        "impuestos":impuestos,
                        "impuestos_detalles":impuestos_detalles,
                        "margen":margen,
                        "margen_porcent":round(margen_porcent,2)
                    })

                    impuestos_10 += imp_10
                    impuestos_1 += imp_1
                    impuestos_35 += imp_35

                    inversion_semana += inversion
                    monto_semana += monto
                    impuestos_semana += impuestos

                if len(dias) == 0:break
                else:
                    impuestos_detalles = [
                        {
                            "n":"10% sobre venta",
                            "v":impuestos_10
                        },
                        {
                            "n":"1%  sobre venta",
                            "v":impuestos_1
                        },
                        """{
                            "n":"35%  sobre venta menos costo",
                            "v":impuestos_35
                        }"""
                    ]
                    margen = monto_semana-(impuestos_semana + inversion_semana)
                    if monto_semana>0:margen_porcent = (margen*100)/monto_semana 
                    else:margen_porcent =  monto_semana

                    semanas.append({
                        "dias":dias,
                        "inversion":inversion_semana,
                        "monto":monto_semana,
                        "impuestos":impuestos_semana,
                        "impuestos_detalles":impuestos_detalles,
                        "margen":margen,
                        "margen_porcent":round(margen_porcent,2)
                        })
                    inversion_semana_total += inversion_semana
                    monto_semana_total += monto_semana
                    impuestos_10_total += impuestos_10
                    impuestos_1_total += impuestos_1
                    impuestos_35_total += impuestos_35
                    impuestos_semana_total += impuestos_semana

                    s=v+1
            
            if "C-" in centro_costo:
                if tipo_contabilidad == "r":
                    pagos.append({
                        "n":"",
                        "v":_pagos,
                        "909":_pagos_909*0.0909,
                        "125":_pagos_909*0.125,
                        "5":_pagos_909*0.05,
                        "t":_pagos + (_pagos_909*0.0909) +(_pagos_909*0.125) + (_pagos_909*0.05)
                        })
                elif tipo_contabilidad == "p":
                    pagos.append({
                        "n":"",
                        "v":_pagos,
                        "909":_pagos*0.0909,
                        "125":_pagos*0.125,
                        "5":_pagos*0.05,
                        "t":_pagos + (_pagos*0.0909) +(_pagos*0.125) + (_pagos*0.05)
                        })
                else:
                    pagos.append({
                        "n":"",
                        "v":_pagos_909,
                        "909":_pagos_909*0.0909,
                        "125":_pagos_909*0.125,
                        "5":_pagos_909*0.05,
                        "t":_pagos_909 + (_pagos_909*0.0909) +(_pagos_909*0.125) + (_pagos_909*0.05)
                        })
                
            else:
                pago_total += _pagos
                pagos_909_total += _pagos_909


        if "PV-" in centro_costo or centro_costo == "all":
            _pagos = 0.0
            _pagos_909 = 0.0
            for v in [7,14,21,28,35]:

                inversion_semana = 0
                monto_semana = 0
                impuestos_10 = 0
                impuestos_1 = 0
                impuestos_35 = 0
                impuestos_semana = 0
                dias=[]

                for d in range(s, v + 1):
                    if d > cant_dias:
                        break

                    inversion = 0
                    impuestos = 0
                    monto = 0
                    
                    imp_1= 0
                    imp_10= 0
                    imp_35= 0 # Dice yosvani qu eeste no va

                    # pra los turnos de los puntos de ventas
                    if "PV-" in centro_costo: # centro_costo == "all" or
                        turnos = Turno.objects.filter(fin__year=year, fin__month=month, fin__day=d)
                        if "PV-" in centro_costo:
                            turnos = turnos.filter(punto_venta__id = centro_costo.replace("PV-",""))

                        for turno in turnos:
                            for p in turno.pagos.all():
                                _pagos += p.monto_original
                                if "U-" in p.user_id and UserAccount.objects.get(id= p.user_id.replace("U-","")).pago_909:
                                    _pagos_909 += p.monto_original

                            
                            if tipo_contabilidad == "r" or tipo_contabilidad == "p":
                                inversion += turno.coste_productos()
                                monto += turno.monto
                            else:
                                inversion += turno.coste_productos(False)
                                monto += turno.monto_ext

                            if tipo_contabilidad == "f" or tipo_contabilidad == "r":
                                impuestos += turno.impuestos_ventas()
                                imp_01,imp_001,imp_035 = turno.impuestos_ventas_list()
                            elif tipo_contabilidad == "p":
                                impuestos += turno.impuestos_ventas(True)
                                imp_01,imp_001,imp_035 = turno.impuestos_ventas_list(True)

                            imp_10 += imp_01
                            imp_1 += imp_001
                            imp_35 += imp_035

                    impuestos_detalles = [
                        {
                            "n":"10% sobre venta",
                            "v":imp_10
                        },
                        {
                            "n":"1%  sobre venta",
                            "v":imp_1
                        },
                    ]
                    
                    margen = monto-(impuestos + inversion)
                    if monto>0:margen_porcent = (margen*100)/monto 
                    else:margen_porcent =  monto
                    dias.append({
                        #"turnos":turnos,
                        "fecha":f"{d} de {meses[int(month) - 1]} de {year}",
                        "inversion":inversion,
                        "monto":monto,
                        "impuestos":impuestos,
                        "impuestos_detalles":impuestos_detalles,
                        "margen":margen,
                        "margen_porcent":round(margen_porcent,2)
                    })

                    impuestos_10 += imp_10
                    impuestos_1 += imp_1
                    impuestos_35 += imp_35

                    inversion_semana += inversion
                    monto_semana += monto
                    impuestos_semana += impuestos

                if len(dias) == 0:break
                else:
                    impuestos_detalles = [
                        {
                            "n":"10% sobre venta",
                            "v":impuestos_10
                        },
                        {
                            "n":"1%  sobre venta",
                            "v":impuestos_1
                        },
                    ]
                    """{
                        "n":"35%  sobre venta menos costo",
                        "v":impuestos_35
                    }"""
                    margen = monto_semana-(impuestos_semana + inversion_semana)
                    if monto_semana>0:margen_porcent = (margen*100)/monto_semana 
                    else:margen_porcent =  monto_semana

                    if "PV-" in centro_costo:
                        semanas.append({
                            "dias":dias,
                            "inversion":inversion_semana,
                            "monto":monto_semana,
                            "impuestos":impuestos_semana,
                            "impuestos_detalles":impuestos_detalles,
                            "margen":margen,
                            "margen_porcent":round(margen_porcent,2)
                            })
                    inversion_semana_total += inversion_semana
                    monto_semana_total += monto_semana
                    impuestos_10_total += impuestos_10
                    impuestos_1_total += impuestos_1
                    impuestos_35_total += impuestos_35
                    impuestos_semana_total += impuestos_semana

                    s=v+1
            
            if "PV-" in centro_costo:
                if tipo_contabilidad == "r":
                    pagos.append({
                        "n":"",
                        "v":_pagos,
                        "909":_pagos_909*0.0909,
                        "125":_pagos_909*0.125,
                        "5":_pagos_909*0.05,
                        "t":_pagos + (_pagos_909*0.0909) +(_pagos_909*0.125) + (_pagos_909*0.05)
                        })
                elif tipo_contabilidad == "p":
                    pagos.append({
                        "n":"",
                        "v":_pagos,
                        "909":_pagos*0.0909,
                        "125":_pagos*0.125,
                        "5":_pagos*0.05,
                        "t":_pagos + (_pagos*0.0909) +(_pagos*0.125) + (_pagos*0.05)
                        })
                else:
                    pagos.append({
                        "n":"",
                        "v":_pagos_909,
                        "909":_pagos_909*0.0909,
                        "125":_pagos_909*0.125,
                        "5":_pagos_909*0.05,
                        "t":_pagos_909 + (_pagos_909*0.0909) +(_pagos_909*0.125) + (_pagos_909*0.05)
                        })
            
            else:
                pago_total += _pagos
                pagos_909_total += _pagos_909

        if "estudio" in centro_costo or centro_costo == "all":
            contratos = FichaCliente.objects.filter(fecha_fin__year=year, fecha_fin__month=month)
            for c in contratos:
                contrato_data = {
                    "contrato":c.identificador(),
                    "fecha":c.fecha_fin.strftime('%d/%m/%Y'),
                    "cliente":c.nombre,
                }                
                if tipo_contabilidad == "r" or tipo_contabilidad == "p":
                    inversion = c.costo_cup + (c.costo_usd * c.tasa_cambio_usd)
                    monto = c.precio_contrato_cup + (c.precio_contrato_usd * c.tasa_cambio_usd) 
                    contrato_data["inversion"] = str(toMoney(inversion)) + " ($" +toMoney(c.costo_usd) + " en USD)" 
                    contrato_data["monto"] = str(toMoney(monto)) + " ($" +toMoney(c.precio_contrato_usd) + " en USD)" 
                    #contrato_data["inversion"] = inversion
                    contrato_data["monto"] = monto

                    if c.audit:
                        imp_01 = monto *  0.1
                        imp_001 = monto * 0.01
                        imp_035 = (monto - inversion)*0.35
                    else:
                        imp_01 = 0
                        imp_001 = 0
                        imp_035 = 0

                    impuestos = imp_01 + imp_001 #+ imp_035
                    contrato_data["impuestos_10"] = imp_01
                    contrato_data["impuestos_1"] = imp_001
                    contrato_data["impuestos_35"] = imp_035
                    contrato_data["impuestos_total"] = imp_01 + imp_001 + imp_035

                    margen = monto-(impuestos + inversion)
                    if monto>0:margen_porcent = (margen*100)/monto 
                    else:margen_porcent =  monto
                    contrato_data["margen"] = margen
                    contrato_data["margen_porcent"] = margen_porcent

                    contratos_list.append(contrato_data)

                    inversion_semana_total += inversion
                    monto_semana_total += monto
                    impuestos_10_total += imp_01
                    impuestos_1_total += imp_001
                    impuestos_35_total += imp_035
                    impuestos_semana_total += impuestos

                else:
                    if c.audit:
                        inversion = c.costo_cup + (c.costo_usd * c.tasa_cambio_usd)
                        monto = c.precio_contrato_cup + (c.precio_contrato_usd * c.tasa_cambio_usd) 
                        contrato_data["inversion"] = str(toMoney(inversion)) + " ($" +toMoney(c.costo_usd) + " en USD)" 
                        contrato_data["monto"] = str(toMoney(monto)) + " ($" +toMoney(c.precio_contrato_usd) + " en USD)" 
                        imp_01 = monto *  0.1
                        imp_001 = monto * 0.01
                        imp_035 = (monto - inversion)*0.35

                        impuestos = imp_01 + imp_001 #+ imp_035
                        margen = monto-(impuestos + inversion)
                        if monto>0:margen_porcent = (margen*100)/monto 
                        else:margen_porcent =  monto
                        contrato_data["margen"] = margen
                        contrato_data["margen_porcent"] = margen_porcent

                        contrato_data["impuestos_10"] = imp_01
                        contrato_data["impuestos_1"] = imp_001
                        contrato_data["impuestos_35"] = imp_035
                        contrato_data["impuestos_total"] = imp_01 + imp_001 #+ imp_035

                        contratos_list.append(contrato_data)

                        inversion_semana_total += inversion
                        monto_semana_total += monto
                        impuestos_10_total += imp_01
                        impuestos_1_total += imp_001
                        impuestos_35_total += imp_035
                        impuestos_semana_total += impuestos
        
        if "salon" in centro_costo or centro_costo == "all":
            
            _pagos = 0.0
            _pagos_909 = 0.0

            clientes = Cliente.objects.filter(fecha_realizacion__year=year, fecha_realizacion__month=month).order_by("fecha_realizacion")
            for c in clientes:
                cliente_data = {
                    "fecha":c.fecha_realizacion.strftime('%d/%m/%Y'),
                    "cliente":c.nombre,
                }                
                if tipo_contabilidad == "r" or tipo_contabilidad == "p":                    
                    inversion = c.costo
                    monto = c.monto()
                    cliente_data["inversion"] = str(toMoney(inversion)) 
                    cliente_data["monto"] = str(toMoney(monto))

                    if c.audit:
                        imp_01 = monto *  0.1
                        imp_001 = monto * 0.01
                        imp_035 = (monto - inversion)*0.35
                    else:
                        imp_01 = 0
                        imp_001 = 0
                        imp_035 = 0

                    impuestos = imp_01 + imp_001 #+ imp_035
                    cliente_data["impuestos_10"] = imp_01
                    cliente_data["impuestos_1"] = imp_001
                    cliente_data["impuestos_35"] = imp_035
                    cliente_data["impuestos_total"] = imp_01 + imp_001 + imp_035

                    margen = monto-(impuestos + inversion)
                    if monto>0:margen_porcent = (margen*100)/monto 
                    else:margen_porcent =  monto
                    cliente_data["margen"] = margen
                    cliente_data["margen_porcent"] = margen_porcent

                    clientes_salon_list.append(cliente_data)

                    inversion_semana_total += inversion
                    monto_semana_total += monto
                    impuestos_10_total += imp_01
                    impuestos_1_total += imp_001
                    impuestos_35_total += imp_035
                    impuestos_semana_total += impuestos
                    
                else:
                    if c.audit:
                        inversion = c.costo
                        monto = c.monto()
                        cliente_data["inversion"] = str(toMoney(inversion)) 
                        cliente_data["monto"] = str(toMoney(monto))

                        imp_01 = monto *  0.1
                        imp_001 = monto * 0.01
                        imp_035 = (monto - inversion)*0.35

                        impuestos = imp_01 + imp_001 #+ imp_035
                        margen = monto-(impuestos + inversion)
                        if monto>0:margen_porcent = (margen*100)/monto 
                        else:margen_porcent =  monto
                        cliente_data["margen"] = margen
                        cliente_data["margen_porcent"] = margen_porcent

                        cliente_data["impuestos_10"] = imp_01
                        cliente_data["impuestos_1"] = imp_001
                        cliente_data["impuestos_35"] = imp_035
                        cliente_data["impuestos_total"] = imp_01 + imp_001 #+ imp_035

                        clientes_salon_list.append(cliente_data)

                        inversion_semana_total += inversion
                        monto_semana_total += monto
                        impuestos_10_total += imp_01
                        impuestos_1_total += imp_001
                        impuestos_35_total += imp_035
                        impuestos_semana_total += impuestos

                for p in c.pagos.all():
                    _pagos += p.monto_original
                    if "U-" in p.user_id and UserAccount.objects.get(id= p.user_id.replace("U-","")).pago_909:
                        _pagos_909 += p.monto_original
            
            if "salon-" in centro_costo:
                if tipo_contabilidad == "r":
                    pagos.append({
                        "n":"",
                        "v":_pagos,
                        "909":_pagos_909*0.0909,
                        "125":_pagos_909*0.125,
                        "5":_pagos_909*0.05,
                        "t":_pagos + (_pagos_909*0.0909) +(_pagos_909*0.125) + (_pagos_909*0.05)
                        })
                elif tipo_contabilidad == "p":
                    pagos.append({
                        "n":"",
                        "v":_pagos,
                        "909":_pagos*0.0909,
                        "125":_pagos*0.125,
                        "5":_pagos*0.05,
                        "t":_pagos + (_pagos*0.0909) +(_pagos*0.125) + (_pagos*0.05)
                        })
                else:
                    pagos.append({
                        "n":"",
                        "v":_pagos_909,
                        "909":_pagos_909*0.0909,
                        "125":_pagos_909*0.125,
                        "5":_pagos_909*0.05,
                        "t":_pagos_909 + (_pagos_909*0.0909) +(_pagos_909*0.125) + (_pagos_909*0.05)
                        })
                
            else:
                pago_total += _pagos
                pagos_909_total += _pagos_909

        a = timezone.now().year
        m = timezone.now().month

        periodos = []
        for i in range(18):
            periodos.append({
                "v":f"{a}-{m}",
                "t":f"{meses[m-1]} de {a}"
                })
            m -= 1
            if m == 0:
                m = 12
                a -= 1

        margen = monto_semana_total -(impuestos_semana_total + inversion_semana_total)
        if monto_semana_total>0:margen_porcent = (margen*100)/monto_semana_total 
        else:margen_porcent =  monto_semana_total

        puntos_venta_return = []

        puntos_ventas = PuntoVenta.objects.filter(activo=True)
        for pv in puntos_ventas:
            puntos_venta_return.append({
                "v":f"PV-{pv.id}",
                "n": pv.nombre
            })
            
        cocinas_return = []
        cocinas = Cocina.objects.filter(activo=True)
        for c in cocinas:
            cocinas_return.append({
                "v":f"C-{c.id}",
                "n": c.nombre
            })

        
        if "all" == centro_costo:
            if tipo_contabilidad == "r":
                pagos.append({
                    "n":"",
                    "v":pago_total,
                    "909":pagos_909_total*0.0909,
                    "125":pagos_909_total*0.125,
                    "5":pagos_909_total*0.05,
                    "t":pago_total + (pagos_909_total*0.0909) +(pagos_909_total*0.125) + (pagos_909_total*0.05)
                    })
            elif tipo_contabilidad == "p":
                pagos.append({
                    "n":"",
                    "v":pago_total,
                    "909":pago_total*0.0909,
                    "125":pago_total*0.125,
                    "5":pago_total*0.05,
                    "t":pago_total + (pago_total*0.0909) +(pago_total*0.125) + (pago_total*0.05)
                    })
            else:
                pagos.append({
                    "n":"",
                    "v":pagos_909_total,
                    "909":pagos_909_total*0.0909,
                    "125":pagos_909_total*0.125,
                    "5":pagos_909_total*0.05,
                    "t":pagos_909_total + (pagos_909_total*0.0909) +(pagos_909_total*0.125) + (pagos_909_total*0.05)
                    })
            

        monto_pagado = 0
        if len(pagos) > 0:monto_pagado = pagos[0]["v"]

        if centro_costo == "all" : gastos = GastoMensual.objects.filter(fecha__month=month, fecha__year=year)
        else:gastos = GastoMensual.objects.filter(centro_costo=centro_costo, fecha__month=month, fecha__year=year)

        gasto_total = gastos.aggregate(total = Sum("monto"))["total"]

        context = {
            "gastos":gastos,
            "puntos_venta":puntos_venta_return,
            "cocinas":cocinas_return,
            "contratos":contratos_list,
            "clientes_salon":clientes_salon_list,
            "pagos":pagos,
            "gasto_total":gasto_total,

            "periodos":periodos,

            "semanas_pv":semanas,
            
            # - datos finales
            "inversion_semana":inversion_semana_total,
            "monto_semana":monto_semana_total,
            "impuestos_10":impuestos_10_total,
            "impuestos_1":impuestos_1_total,
            "impuestos_35":impuestos_35_total,
            "impuestos_semana":impuestos_semana_total,
            "margen_semana":margen,
            "margen_real":margen - monto_pagado,
            "margen_semana_porcent":round(margen_porcent,2)
            }
        

        if centro_costo == "all":context["all_cc"] = True

        return render(request,'caja/estado_liquides/estado_liquides.html',context)
    
    def post(self,request,*args,**kwargs):
        data = request.POST
        data_get = request.GET
        url = str(request.build_absolute_uri())

        if "addGasto" in data and data["addGasto"] == "True":
            if "cc" not in data_get:
                centro_costo="all"
            else:
                centro_costo = data_get["cc"]

            GastoMensual.objects.create(
                centro_costo=centro_costo,
                motivo=data["motivo"],
                monto=data["amount"]
            )

        elif "deleteGasto" in data and data["deleteGasto"] == "True":
            gasto = GastoMensual.objects.get(id=data["gastoId"])
            gasto.delete()

        return redirect(url)

    
@method_decorator(login_required, name='dispatch')
class CrearPrenominaView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET

        fin = datetime.strptime(data["fin"], '%d/%m/%Y').replace(hour=23, minute=59, second=59)

        if Nomina.objects.filter(user_confirm = None).exists():
            messages.error(request, "Error al crear prenómina por existir una prenómina pendiente a ser confirmada.")
            return  redirect("http://" + str(request.get_host()) + f"/caja/salarios?select={Nomina.objects.filter(user_confirm = None).first().id}-nom")
        else:
            users_list = [UserAccount.objects.all(), Fotografo.objects.all()]
            
            prenomina = []
            monto_pagar_total = 0
            new_nomina = Nomina.objects.create(nomina={})

            for users in users_list:
                for u in users:
                    monto_pagar = round(u.monto_pagar(fin),2)
                    pago_acumulado = round(u.pago_acumulado(fin),2)
                    monto_descontar = round(u.monto_descontar(fin),2)

                    if monto_pagar > 0.0 or pago_acumulado > 0.0 or monto_descontar > 0.0:
                        monto_pagar_total += monto_pagar
                        d = {   
                            "nombre":u.user_str(),
                            "pago_acumulado":pago_acumulado,
                            "monto_descontar":monto_descontar,
                            "monto_pagar":monto_pagar
                        }
                        if "U-" in u.tag_id():
                            d["ci"]=u.ci
                            d["telefono"]=u.telefono

                        prenomina.append(d)
                        pagos = u.pagos(fin)
                        for pago in pagos:
                            new_nomina.pagos.add(pago)
                            
                        descuentos = u.descuentos(fin)
                        for descuento in descuentos:
                            new_nomina.descuentos.add(descuento)


            nomina =json.dumps({
                "total":round(monto_pagar_total,2),
                "pagos":prenomina
            })
            new_nomina.nomina = nomina
            new_nomina.save()

            return  redirect("http://" + str(request.get_host()) + f"/caja/salarios?select={new_nomina.id}-nom")