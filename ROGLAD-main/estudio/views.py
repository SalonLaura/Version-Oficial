import json
import threading
from django.shortcuts import render,redirect
from django.utils.decorators import method_decorator
from bot.bot import send_message
from bussiness.models import AlertaAdmin, Categoria, ConfigVar, Descuentos, Medida, Pago, Producto, StockAlmacen, StockPuntoVenta, StockUsuario, Transferencia, UserAccount
from bussiness.utils import punto_venta_required, login_required, toMoney, toMoneyList
from django.views import View
from django.contrib import messages
from datetime import datetime
from django.utils import timezone
from django.db.models import Q, Subquery, Sum
from django.core.exceptions import ObjectDoesNotExist
from caja.models import Caja, Operaciones
from estudio.models import Contrato, Editor, EnviosEdicion, EnviosImpresion, Estado, FichaCliente, Fotografo, GrupoEstado, CasaImpresion, Servicio, ServicioContrato, ServicioContratoCliente, StockEstudio, TipoContrato, Turno
from kitchen.models import StockCocina

def super_upper(text:str) -> str:
    return text.upper().translate({
                ord('á'): 'A',
                ord('é'): 'E',
                ord('í'): 'I',
                ord('ó'): 'O',
                ord('ú'): 'U',
            })

@method_decorator(login_required, name='dispatch')
class SubproductosView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        productos = Producto.objects.filter(Q(activo = True) & Q(categoria__nombre="ACCESORIOS, PRENDAS Y OTROS")).order_by("nombre")
        context = {
            "productos":productos,
            "medidas" : Medida.objects.filter(activo = True),
            "categorias" : Categoria.objects.filter(activo = True).exclude(nombre="ACCESORIOS, PRENDAS Y OTROS"),
            }
        return render(request,'estudio/subproductos.html',context)
    
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
            categoria = Categoria.objects.get_or_create(nombre="ACCESORIOS, PRENDAS Y OTROS")[0]
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
class NewClienteView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        razon_cambio_usd = float(ConfigVar.objects.get(key="precio_usd").value)
        
        tipos = TipoContrato.objects.filter(activo=True).order_by("nombre")
        
        contratos = Contrato.objects.filter(activo=True).order_by("nombre")
        if "t" in data and data["t"] != '':
            contratos = contratos.filter(tipo__id = data["t"])

        if "ca" in data  and data["ca"] != '':contrato_select= contratos.filter(id=data["ca"]).first()
        else:contrato_select= contratos.first()

        fotografos = Fotografo.objects.filter(activo=True).order_by("nombre")
        editor = Editor.objects.filter(activo=True).order_by("nombre")
        responsable = UserAccount.objects.filter(is_active=True,responsable_estudio_permission=True)
        responsable_revision = UserAccount.objects.filter(is_active=True,estudio_permission=True)

        servicios = Servicio.objects.filter(activo=True).order_by("nombre")

        context = {"servicios":servicios,"razon_cambio_usd":razon_cambio_usd, "tipos":tipos,"contratos":contratos,"contrato_select":contrato_select,
                   "fotografos":fotografos, "editores":editor, "responsables":responsable,"responsable_revision":responsable_revision}

        return render(request,'estudio/new_cliente.html',context)
    
    def post(self,request,*args,**kwargs):
        data_post = request.POST
        
        responsable_contrato = data_post["rc"]
        responsable_revicion = data_post["rr"]
        fotografo = data_post["f"]
        editor = data_post["e"]
        contrato = data_post["ca"]
        
        nombre = data_post["nombre"]
        edad = data_post["edad"]
        ci = data_post["ci"]
        calle = data_post["calle"]
        entre = data_post["entre"]
        numero = data_post["numero"]
        consejo_popular = data_post["consejo_popular"]
        muncp = data_post["muncp"]
        prov = data_post["prov"]
        pais = data_post["pais"]
        telefono = data_post["telefono"]
        correo = data_post["correo"]
        facebook = data_post["facebook"]
        instagram = data_post["instagram"]
        twitter = data_post["twitter"]
        telegram = data_post["telegram"]
        nombre_contrata = data_post["nombre_contrata"]
        ci_contrata = data_post["ci_contrata"]
        parentesco_contrata = data_post["parentesco_contrata"]
        nombre_contrata_2 = data_post["nombre_contrata_2"]
        ci_contrata_2 = data_post["ci_contrata_2"]
        parentesco_contrata_2 = data_post["parentesco_contrata_2"]
        autorizo_redes_sociales = data_post["autorizo_redes_sociales"]
        if autorizo_redes_sociales == "no":autorizo_redes_sociales = False
        else:autorizo_redes_sociales = True
        condiciones_publicacion = data_post["condiciones_publicacion"]
        anotaciones = data_post["anotaciones"]

        contrato = Contrato.objects.get(id=contrato)
        fecha_acordada = datetime.strptime(data_post["date-acordado"], '%d/%m/%Y')
        fecha_seleccion = datetime.strptime(data_post["date-seleccion"], '%d/%m/%Y')
        new_clint = FichaCliente.objects.create(
            responsable_contrato = UserAccount.objects.get(id=responsable_contrato),
            responsable_revicion = UserAccount.objects.get(id=responsable_revicion),
            fotografo = Fotografo.objects.get(id=fotografo),
            editor = Editor.objects.get(id=editor),
            contrato = contrato,
            nombre = nombre,
            edad = edad,
            ci = ci,
            calle = calle,
            entre = entre,
            numero = numero,
            consejo_popular = consejo_popular,
            muncp = muncp,
            prov = prov,
            pais = pais,
            telefono = telefono,
            correo = correo,
            facebook = facebook,
            instagram = instagram,
            twitter = twitter,
            telegram = telegram,
            nombre_contrata = nombre_contrata,
            ci_contrata = ci_contrata,
            parentesco_contrata = parentesco_contrata,
            nombre_contrata_2 = nombre_contrata_2,
            ci_contrata_2 = ci_contrata_2,
            parentesco_contrata_2 = parentesco_contrata_2,
            autorizo_redes_sociales = autorizo_redes_sociales,
            condiciones_publicacion = condiciones_publicacion,
            fecha_acordada = fecha_acordada,
            fecha_seleccion = fecha_seleccion
        )

        if anotaciones != "":
            new_clint.anotaciones = f"{request.user.user} - {str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))}: {anotaciones}"
        
        
        identificador = str(new_clint.numeroCliente()) + new_clint.fecha_solicitud.strftime("%b%d%Y")
        if contrato.moneda_anticipo == "USD":
            caja = Caja.objects.get_or_create(name = "CENTRAL",moneda = "USD")[0]
            Operaciones.objects.create(
                monto = float(contrato.anticipo),
                motivo = f"Monto cobrado al cliente {new_clint.nombre} en forma de anticipo correspondiente al contrato {identificador}",
                caja = caja
            )
            new_clint.precio_contrato_usd += float(contrato.anticipo)


        else:
            caja = Caja.objects.get_or_create(name = "CENTRAL",moneda = "CUP")[0]
            Operaciones.objects.create(
                monto = float(contrato.anticipo),
                motivo = f"Monto cobrado al cliente {new_clint.nombre} en forma de anticipo correspondiente al contrato {identificador}",
                caja = caja
            )
            new_clint.precio_contrato_cup += float(contrato.anticipo)

        for servicio in contrato.servicios.all():
            for _ in range(int(servicio.cantidad)):
                servicio = ServicioContratoCliente.objects.create(
                                                servicio=servicio.servicio,
                                                cantidad=1,
                                                fecha_acordada = fecha_acordada
                                            )
                new_clint.servicios_contrato.add(servicio)

        if "otros-servicios-fechas" in data_post.keys() and "otros-servicios-ids" in data_post.keys():
            otros_servicios_fechas = list(dict(data_post)["otros-servicios-fechas"])
            otros_servicios_ids = list(dict(data_post)["otros-servicios-ids"])
            otros_servicios_cantidades = list(dict(data_post)["otros-servicios-cantidades"])
        
            for index,id in enumerate(otros_servicios_ids,start=0):
                for _ in range(int(otros_servicios_cantidades[index])):
                    otro_servicio = ServicioContratoCliente.objects.create(
                                                    servicio=Servicio.objects.get(id=id),
                                                    cantidad=1,
                                                    fecha_acordada = datetime.strptime(otros_servicios_fechas[index], '%d/%m/%Y')
                                                )
                    new_clint.servicios_adicionales.add(otro_servicio)

        new_clint.save()
        return redirect("NewClienteEstudio")
    
@method_decorator(login_required, name='dispatch')
class ContratosPendientesView(View):
    def get(self,request,*args,**kwargs):
        razon_cambio_usd = float(ConfigVar.objects.get(key="precio_usd").value)
        data = request.GET
        contratos = FichaCliente.objects.filter(activo=True,fecha_realizacion=None).order_by("fecha_acordada")

        if request.user.responsable_estudio_permission:
            contratos = contratos.filter(responsable_contrato = request.user)
        
        context = {"contratos":contratos,"razon_cambio_usd":razon_cambio_usd}
        return render(request,'estudio/pendientes.html',context)
    
    def post(self,request,*args,**kwargs):
        data = request.POST
        ficha = FichaCliente.objects.get(id=data["fichacliente-id"])
        
        ficha.fecha_realizacion = datetime.now().date()

        precio_cup = float(data["precio_cup"])
        precio_usd = float(data["precio_usd"])

        ficha.precio_contrato_cup += precio_cup
        ficha.precio_contrato_usd += precio_usd
        ficha.save()
        
        identificador = str(ficha.numeroCliente()) + ficha.fecha_solicitud.strftime("%b%d%Y")
        if precio_usd  > 0.0:
            caja = Caja.objects.get_or_create(name = "CENTRAL",moneda = "USD")[0]
            Operaciones.objects.create(
                monto = precio_usd,
                motivo = f"Monto cobrado al cliente {ficha.nombre_contrata} correspondiente al contrato {identificador}",
                caja = caja
            )


        if precio_cup > 0.0:
            caja = Caja.objects.get_or_create(name = "CENTRAL",moneda = "CUP")[0]
            Operaciones.objects.create(
                monto = precio_cup,
                motivo = f"Monto cobrado al cliente {ficha.nombre_contrata} correspondiente al contrato {identificador}",
                caja = caja
            )

        if ficha.contrato.pago_fotografo > 0:
            pago = Pago.objects.create(
                monto_original = ficha.contrato.pago_fotografo,
                monto = ficha.contrato.pago_fotografo,
                descripcion = f"Pago a fotógrafo por el contrato {identificador}",
                user_id = f"F-{ficha.fotografo.id}",
                user_name = ficha.fotografo.nombre
            )

        if ficha.contrato.pago_responsable > 0:
            pago = Pago.objects.create(
                monto_original = ficha.contrato.pago_responsable,
                monto = ficha.contrato.pago_responsable,
                descripcion = f"Pago a responsable/maquillista del contrato {identificador}",
                user_id = f"U-{ficha.responsable_contrato.id}",
                user_name = ficha.responsable_contrato.user_str()
            )
        
        for servicio in ficha.servicios_adicionales.all():
            if servicio.servicio.pago_fotografo > 0:
                Pago.objects.create(
                    monto_original = servicio.servicio.pago_fotografo,
                    monto = servicio.servicio.pago_fotografo,
                    descripcion = f"Pago a fotógrafo por servicio adicional ({servicio.servicio.nombre}) en el contrato {identificador}",
                    user_id = f"F-{ficha.fotografo.id}",
                    user_name = ficha.fotografo.user_str()
                )
            if servicio.servicio.pago_responsable > 0:
                Pago.objects.create(
                    monto_original = servicio.servicio.pago_fotografo,
                    monto = servicio.servicio.pago_fotografo,
                    descripcion = f"Pago a responsable por servicio adicional ({servicio.servicio.nombre}) en el contrato {identificador}",
                    user_id = f"U-{ficha.responsable_contrato.id}",
                    user_name = ficha.responsable_contrato.user_str()
                )

        return redirect("PendientesEstudio")
    
@method_decorator(login_required, name='dispatch')
class EditContratoView(View):
    def get(self, request, id_contrato, *args,**kwargs):
        razon_cambio_usd = float(ConfigVar.objects.get(key="precio_usd").value)
        data = request.GET
        
        tipos = TipoContrato.objects.filter(activo=True)
        
        contratos = Contrato.objects.filter(activo=True)
        if "t" in data and data["t"] != '':
            contratos = contratos.filter(tipo__id = data["t"])

        if "ca" in data  and data["ca"] != '':contrato_select= contratos.filter(id=data["ca"]).first()
        else:contrato_select= contratos.first()

        fotografos = Fotografo.objects.filter(activo=True).order_by("nombre")
        editor = Editor.objects.filter(activo=True).order_by("nombre")
        responsable = UserAccount.objects.filter(is_active=True,responsable_estudio_permission = True).order_by("user")
        responsable_revision = UserAccount.objects.filter(is_active=True,estudio_permission=True).order_by("user")

        servicios = Servicio.objects.filter(activo=True).order_by("nombre")
        ficha_cliente = FichaCliente.objects.get(activo=True,id=id_contrato)

        context = {"servicios":servicios,"razon_cambio_usd":razon_cambio_usd, "tipos":tipos,"contratos":contratos,"contrato_select":contrato_select,
                   "fotografos":fotografos, "editores":editor, "responsables":responsable,"ficha_cliente":ficha_cliente,"responsable_revision":responsable_revision}
        
        return render(request,'estudio/edit_contrato.html',context)
    
    def post(self,request,*args,**kwargs):
        data_post = request.POST
        
        ficha_cliente_id = data_post["ficha_cliente_id"]
        ficha_cliente = FichaCliente.objects.get(id=ficha_cliente_id)

        cambios = []
        
        if "rc" in data_post and data_post["rc"] != str(ficha_cliente.responsable_contrato.id):
            nuevo_responsable_contrato = UserAccount.objects.get(id=data_post["rc"])
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio de responsable de contrato de {ficha_cliente.responsable_contrato.user} para {nuevo_responsable_contrato.user}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.responsable_contrato = nuevo_responsable_contrato

        if "rr" in data_post and data_post["rr"] != str(ficha_cliente.responsable_revicion.id):
            nuevo_responsable_revicion = UserAccount.objects.get(id=data_post["rr"])
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio de responsable de revición de {ficha_cliente.responsable_revicion.user} para {nuevo_responsable_revicion.user}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.responsable_revicion = nuevo_responsable_revicion
            

        if "f" in data_post and data_post["f"] != str(ficha_cliente.fotografo.id):
            nuevo_fotografo = Fotografo.objects.get(id=data_post["f"])
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio de fotógrafo de {ficha_cliente.fotografo.nombre} para {nuevo_fotografo.nombre}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.fotografo = nuevo_fotografo
            

        if "e" in data_post and data_post["e"] != str(ficha_cliente.editor.id):
            nuevo_editor = Editor.objects.get(id=data_post["e"])
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio de editor de {ficha_cliente.editor.nombre} para {nuevo_editor.nombre}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.editor = nuevo_editor

        if "ca" in data_post and data_post["ca"] != str(ficha_cliente.contrato.id):
            nuevo_contrato = Contrato.objects.get(id=data_post["ca"])
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio de editor de {ficha_cliente.contrato.nombre}({ficha_cliente.contrato.tipo.nombre}) para {nuevo_contrato.nombre}({nuevo_contrato.tipo.nombre})",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.contrato = nuevo_contrato

        if "nombre" in data_post and data_post["nombre"] != str(ficha_cliente.nombre):
            nuevo_nombre = data_post["nombre"]
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio de nombre de {ficha_cliente.nombre} para {nuevo_nombre}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.nombre = nuevo_nombre

        if "edad" in data_post and data_post["edad"] != str(ficha_cliente.edad):
            nuevo_edad = data_post["edad"]
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio de edad de {ficha_cliente.edad} para {nuevo_edad}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.edad = nuevo_edad

        if "ci" in data_post and data_post["ci"] != str(ficha_cliente.ci):
            nuevo = data_post["ci"]
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio de carné de identidad de {ficha_cliente.ci} para {nuevo}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.ci = nuevo

        if "calle" in data_post and data_post["calle"] != str(ficha_cliente.calle):
            nuevo = data_post["calle"]
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio de dirección de {ficha_cliente.calle} para {nuevo}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.calle = nuevo

        if "entre" in data_post and data_post["entre"] != str(ficha_cliente.entre):
            nuevo = data_post["entre"]
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio de dirección de {ficha_cliente.entre} para {nuevo}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.entre = nuevo
            
        if "numero" in data_post and data_post["numero"] != str(ficha_cliente.numero):
            nuevo = data_post["numero"]
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio de dirección de {ficha_cliente.numero} para {nuevo}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.numero = nuevo

        if "consejo_popular" in data_post and data_post["consejo_popular"] != str(ficha_cliente.consejo_popular):
            nuevo = data_post["consejo_popular"]
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio de dirección de {ficha_cliente.consejo_popular} para {nuevo}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.consejo_popular = nuevo


        if "muncp" in data_post and data_post["muncp"] != str(ficha_cliente.muncp):
            nuevo = data_post["muncp"]
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio de dirección de {ficha_cliente.muncp} para {nuevo}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.muncp = nuevo

        if "prov" in data_post and data_post["prov"] != str(ficha_cliente.prov):
            nuevo = data_post["prov"]
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio de dirección de {ficha_cliente.prov} para {nuevo}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.prov = nuevo

        if "pais" in data_post and data_post["pais"] != str(ficha_cliente.pais):
            nuevo = data_post["pais"]
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio de dirección de {ficha_cliente.pais} para {nuevo}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.pais = nuevo

        if "telefono" in data_post and data_post["telefono"] != str(ficha_cliente.telefono):
            nuevo = data_post["telefono"]
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio de teléfono de {ficha_cliente.telefono} para {nuevo}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.telefono = nuevo

        if "correo" in data_post and data_post["correo"] != str(ficha_cliente.correo):
            nuevo = data_post["correo"]
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio de dirección de correo de {ficha_cliente.correo} para {nuevo}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.correo = nuevo

        if "facebook" in data_post and data_post["facebook"] != str(ficha_cliente.facebook):
            nuevo = data_post["facebook"]
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio de cuenta de Facebook de {ficha_cliente.facebook} para {nuevo}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.facebook = nuevo

        if "instagram" in data_post and data_post["instagram"] != str(ficha_cliente.instagram):
            nuevo = data_post["instagram"]
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio de cuenta de Instagram de {ficha_cliente.instagram} para {nuevo}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.instagram = nuevo
            
        if "twitter" in data_post and data_post["twitter"] != str(ficha_cliente.twitter):
            nuevo = data_post["twitter"]
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio de cuenta de Twitter de {ficha_cliente.twitter} para {nuevo}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.twitter = nuevo

        if "telegram" in data_post and data_post["telegram"] != str(ficha_cliente.telegram):
            nuevo = data_post["telegram"]
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio de cuenta de Télegram de {ficha_cliente.telegram} para {nuevo}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.telegram = nuevo


        if "nombre_contrata" in data_post and data_post["nombre_contrata"] != str(ficha_cliente.nombre_contrata):
            nuevo = data_post["nombre_contrata"]
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio del nombre de la primera persona que contrata de {ficha_cliente.nombre_contrata} para {nuevo}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.nombre_contrata = nuevo
            

        if "ci_contrata" in data_post and data_post["ci_contrata"] != str(ficha_cliente.ci_contrata):
            nuevo = data_post["ci_contrata"]
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio del carné de identidad de la primera persona que contrata de {ficha_cliente.ci_contrata} para {nuevo}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.ci_contrata = nuevo

        if "parentesco_contrata" in data_post and data_post["parentesco_contrata"] != str(ficha_cliente.parentesco_contrata):
            nuevo = data_post["parentesco_contrata"]
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio del parentesco de la primera persona que contrata de {ficha_cliente.parentesco_contrata} para {nuevo}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.parentesco_contrata = nuevo


        if "nombre_contrata_2" in data_post and data_post["nombre_contrata_2"] != str(ficha_cliente.nombre_contrata_2):
            nuevo = data_post["nombre_contrata_2"]
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio del nombre de la segunda persona que contrata de {ficha_cliente.nombre_contrata_2} para {nuevo}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.nombre_contrata_2 = nuevo
            
        if "ci_contrata_2" in data_post and data_post["ci_contrata_2"] != str(ficha_cliente.ci_contrata_2):
            nuevo = data_post["ci_contrata_2"]
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio del carné de identidad de la segunda persona que contrata de {ficha_cliente.ci_contrata_2} para {nuevo}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.ci_contrata_2 = nuevo

        if "parentesco_contrata_2" in data_post and data_post["parentesco_contrata_2"] != str(ficha_cliente.parentesco_contrata_2):
            nuevo = data_post["parentesco_contrata_2"]
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio del parentesco de la segunda persona que contrata de {ficha_cliente.parentesco_contrata_2} para {nuevo}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.parentesco_contrata_2 = nuevo
            
            
        if "autorizo_redes_sociales" in data_post:
            autorizo_redes_sociales = data_post["autorizo_redes_sociales"]
            if autorizo_redes_sociales == "no":autorizo_redes_sociales = False
            else:autorizo_redes_sociales = True

            if autorizo_redes_sociales != ficha_cliente.autorizo_redes_sociales:
                nuevo = autorizo_redes_sociales
                nuevo_str = "No"
                if autorizo_redes_sociales:nuevo_str = "Si"
                cambios.append({
                    "autor":request.user.user,
                    "cambio":f"Cambio del autorizo de publicación para {nuevo_str}",
                    "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
                })
                ficha_cliente.autorizo_redes_sociales = nuevo

        if "condiciones_publicacion" in data_post and data_post["condiciones_publicacion"] != str(ficha_cliente.condiciones_publicacion):
            nuevo = data_post["condiciones_publicacion"]
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio de las condiciones de publicación {ficha_cliente.condiciones_publicacion} para {nuevo}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.condiciones_publicacion = nuevo



        if "date-acordado" in data_post and datetime.strptime(data_post["date-acordado"], '%d/%m/%Y').date() != ficha_cliente.fecha_acordada:
            nuevo = datetime.strptime(data_post["date-acordado"], '%d/%m/%Y').date()
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio de la fecha acordada de  {ficha_cliente.fecha_acordada} para {nuevo}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.fecha_acordada = nuevo

        if "date-seleccion" in data_post and datetime.strptime(data_post["date-seleccion"], '%d/%m/%Y').date() != ficha_cliente.fecha_seleccion:
            nuevo = datetime.strptime(data_post["date-seleccion"], '%d/%m/%Y').date()
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Cambio de la fecha selección de  {ficha_cliente.fecha_seleccion} para {nuevo}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })
            ficha_cliente.fecha_seleccion = nuevo
                      

        if "anotaciones" in data_post and data_post["anotaciones"] != "":
            anotaciones = data_post["anotaciones"]
            
            cambios.append({
                "autor":request.user.user,
                "cambio":f"Nueva nota: {anotaciones}",
                "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
            })

            ficha_cliente.anotaciones += f"\n{request.user.user} - {str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))}: {anotaciones}"  

        
        if not ficha_cliente.fecha_realizacion:
            ficha_cliente.servicios_contrato.all().delete()
            for servicio in ficha_cliente.contrato.servicios.all():
                for _ in range(int(servicio.cantidad)):
                    servicio = ServicioContratoCliente.objects.create(
                                                    servicio=servicio.servicio,
                                                    cantidad=1,
                                                    fecha_acordada = datetime.strptime(data_post["date-acordado"], '%d/%m/%Y').date()
                                                )
                    ficha_cliente.servicios_contrato.add(servicio)

            ficha_cliente.servicios_adicionales.all().delete()
            if "otros-servicios-fechas" in data_post.keys():
                otros_servicios_fechas = list(dict(data_post)["otros-servicios-fechas"])
                otros_servicios_ids = list(dict(data_post)["otros-servicios-ids"])
                otros_servicios_cantidades = list(dict(data_post)["otros-servicios-cantidades"])
            
                for index,id in enumerate(otros_servicios_ids,start=0):
                    for _ in range(int(otros_servicios_cantidades[index])):
                        otro_servicio = ServicioContratoCliente.objects.create(
                                                        servicio=Servicio.objects.get(id=id),
                                                        cantidad=1,
                                                        fecha_acordada = datetime.strptime(otros_servicios_fechas[index], '%d/%m/%Y')
                                                    )
                        ficha_cliente.servicios_adicionales.add(otro_servicio)

            ficha_cliente.add_cambios(cambios)
            ficha_cliente.save()
            return redirect("PendientesEstudio")
        
        else:
            for k in data_post.keys():
                if "seleccion-" in k:
                    id_seleccion = k.split("-")[1]
                    sc = ServicioContratoCliente.objects.get(id=id_seleccion)
                    nueva = data_post[k]
                    if nueva == "":nueva = None
                    if sc.seleccion != nueva:
                        de = "ninguna"
                        if sc.seleccion: de = f"{sc.seleccion}"
                        para = "ninguna"
                        if nueva: para = f"{nueva}"

                        cambios.append({
                            "autor":request.user.user,
                            "cambio":f"Cambio de selección del servicio {sc.servicio.nombre} de {de} para {nueva}",
                            "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
                        })

                        sc.seleccion = nueva
                        sc.save()

                elif "estado-" in k:
                    id_estado = k.split("-")[1]
                    sc = ServicioContratoCliente.objects.get(id=id_estado)
                    if data_post[k] == "ok": nueva = "Terminado"
                    elif data_post[k] != "": nueva = Estado.objects.get(id=data_post[k])
                    else: nueva = None
                    if sc.estado != nueva or (sc.terminado == True and nueva == None):

                        de = ""
                        if sc.estado: de = f"de {sc.estado.nombre}"

                        
                        para = "para el estado inicial"
                        if nueva == "Terminado": para = f"para Terminado"
                        elif nueva: para = f"para {nueva.nombre}"

                        idtf = ""
                        if sc.seleccion: idtf = f"({sc.seleccion})"

                        cambios.append({
                            "autor":request.user.user,
                            "cambio":f"Cambio de estado del servicio {sc.servicio.nombre}{idtf} {de} {para}",
                            "fecha":str(timezone.now().strftime('%d/%m/%Y %H:%M:%S'))
                        })

                        if nueva == "Terminado":
                            sc.estado = None
                            sc.terminado = True
                        else:
                            sc.estado = nueva
                            sc.terminado = False
                        sc.save()

            ficha_cliente.add_cambios(cambios)
            ficha_cliente.save()
            return redirect("RealizadosEstudio")
        

@method_decorator(login_required, name='dispatch')
class HistorialContratosView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        contratos = FichaCliente.objects.filter(fecha_fin__isnull=False)
        context = {"contratos":contratos}
        return render(request,'estudio/historial.html',context)
    
@method_decorator(login_required, name='dispatch')
class VerContratoTerminadoView(View):
    def get(self,request,id,*args,**kwargs):
        data = request.GET
        contrat = FichaCliente.objects.get(id=id)
        context = {"ficha_cliente":contrat}
        return render(request,'estudio/contrato_terminado.html',context)
    
    
@method_decorator(login_required, name='dispatch')
class ContratosRealizadosView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        contratos = FichaCliente.objects.filter(activo=True,fecha_realizacion__isnull=False,fecha_fin=None)
        context = {"contratos":contratos}
        return render(request,'estudio/realizados.html',context)
    
    def post(self,request,*args,**kwargs):
        data = request.POST
        ficha = FichaCliente.objects.get(id=data['fichacliente-id'])
        ficha.fecha_fin = timezone.now().date()
        for s in ficha.servicios_contrato.all():
            if s.servicio.moneda_precio == "USD":
                ficha.costo_usd += s.servicio.costo
            else:
                ficha.costo_cup += s.servicio.costo

        monto_bolsa = StockEstudio.objects.aggregate(total_deuda=Sum('deuda', default=0))['total_deuda']

        if float(monto_bolsa) >= ficha.contrato.monto_bolsa:
            ficha.costo_cup += ficha.contrato.monto_bolsa
            cantidad_descontar = ficha.contrato.monto_bolsa
        else:
            ficha.costo_cup += monto_bolsa
            cantidad_descontar = monto_bolsa
            
        deudas = StockEstudio.objects.filter(deuda__gt=0)

        for d in deudas:
            if cantidad_descontar <= 0:
                break
            elif d.deuda >= cantidad_descontar:
                d.deuda -= cantidad_descontar
                d.save()
                cantidad_descontar = 0
                break
            else:
                cantidad_descontar -= d.deuda
                d.deuda = 0
                d.save()

        razon_cambio_usd = float(ConfigVar.objects.get(key="precio_usd").value)
        ficha.tasa_cambio_usd = razon_cambio_usd
        ficha.save()
        identificador = ficha.identificador()
        
        if ficha.contrato.pago_gestor > 0:
            pago = Pago.objects.create(
                monto_original = ficha.contrato.pago_gestor,
                monto = ficha.contrato.pago_gestor,
                descripcion = f"Pago a responsable de revisión (gestor) del contrato {identificador}",
                user_id = f"U-{ficha.responsable_revicion.id}",
                user_name = ficha.responsable_revicion.user_str()
            )


        return redirect("RealizadosEstudio")
    
@method_decorator(login_required, name='dispatch')
class FichaClienteView(View):
    def get(self,request,*args,**kwargs):
        context = {}
        return render(request,'estudio/ficha_cliente.html',context)
    
@method_decorator(login_required, name='dispatch')
class FotosEdicionView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        editores = Editor.objects.filter(activo=True)

        context = {"editores":editores}

        if "e" in data:
            fotos_pendientes = ServicioContratoCliente.objects.filter(
                Q(seleccion__isnull=False) & Q(terminado=False) & 
                ( Q(servicios_contrato_ficha__editor__id=data["e"]) |  
                 Q(servicios_adicionales_ficha__editor__id=data["e"]))& 
                ( Q(servicios_contrato_ficha__fecha_fin__isnull = True) |  
                Q(servicios_adicionales_ficha__fecha_fin__isnull = True))
                ).exclude(foto_envia_editar__isnull = False
                          )
            context["fotos_pendientes"] = fotos_pendientes

            
            
            fotos_editando = EnviosEdicion.objects.filter(editor__id=data["e"],fecha_retorno__isnull=True)
            context["fotos_editando"] = fotos_editando

            servicios_en_impresion = EnviosImpresion.objects.values('servicio')
            fotos_editadas = EnviosEdicion.objects.filter(  Q(editor__id=data["e"]) &
                                                            Q(fecha_retorno__isnull=False) & 
                                                            ( Q(servicio__servicios_contrato_ficha__fecha_fin__isnull = True) |  
                                                            Q(servicio__servicios_adicionales_ficha__fecha_fin__isnull = True))
                                                          ).exclude(servicio__in=Subquery(servicios_en_impresion))
            context["fotos_editadas"] = fotos_editadas

        return render(request,'estudio/envios_edicion.html',context)
    
    def post(self,request,*args,**kwargs):
        data = request.POST
            
        if "foto-editar" in data:
            fotos_editar = list(dict(data)["foto-editar"])

            lote = 0
            
            try:
                ultimo_registro = EnviosEdicion.objects.latest('fecha_envio')
            except ObjectDoesNotExist:
                ultimo_registro = None
                
            if ultimo_registro is not None:
                lote = ultimo_registro.lote + 1

            for id in fotos_editar:
                foto = ServicioContratoCliente.objects.get(id=id)
                
                if foto.servicios_contrato_ficha.all().exists():
                    editor = foto.servicios_contrato_ficha.all().first().editor
                else:
                    editor = foto.servicios_adicionales_ficha.all().first().editor

                EnviosEdicion.objects.create(
                    editor = editor,
                    servicio=foto,
                    lote = lote
                )

        elif "action" in data and data["action"] == "back":
            envios = []
            if "foto-editada" in data: envios = list(dict(data)["foto-editada"])
            for id in envios:
                EnviosEdicion.objects.get(id=id).delete()

        elif "action" in data and data["action"] == "next":
            envios = []
            if "foto-editada" in data: envios = list(dict(data)["foto-editada"])
            for id in envios:
                envio = EnviosEdicion.objects.get(id=id)
                envio.fecha_retorno = timezone.now()
                envio.save()

        elif "action" in data and data["action"] == "back-edicion":
            envios = []
            if "foto-editada-ok" in data: envios = list(dict(data)["foto-editada-ok"])
            for id in envios:
                envio = EnviosEdicion.objects.get(id=id)
                envio.fecha_retorno = None
                envio.save()
        elif  "action" in data and data["action"] == "next-imp":
            envios = []
            if "foto-editada-ok" in data: envios = list(dict(data)["foto-editada-ok"])
            
            lote = 0
            
            try:
                ultimo_registro = EnviosImpresion.objects.latest('fecha_envio')
            except ObjectDoesNotExist:
                ultimo_registro = None
                
            if ultimo_registro is not None:
                lote = ultimo_registro.lote + 1

            for id in envios:
                envio = EnviosEdicion.objects.get(id=id)
                EnviosImpresion.objects.create(
                    servicio = envio.servicio,
                    lote=lote
                )
                
                pago = Pago.objects.create(
                    monto_original = envio.editor.pago,
                    monto = envio.editor.pago,
                    descripcion = f"Pago por editar {envio.servicio.seleccion}",
                    user_id = f"E-{envio.editor.id}",
                    user_name = envio.editor.nombre
                )
                


        return redirect(str(request.build_absolute_uri()))

@method_decorator(login_required, name='dispatch')
class FotosImpresionView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        casas = CasaImpresion.objects.filter(activo=True)

        context = {"casas_impresion":casas}

        fotos_pendientes = EnviosImpresion.objects.filter(
                Q(fecha_envio__isnull=True) & Q(fecha_retorno__isnull=True)
                ).exclude( ( Q(servicio__servicios_contrato_ficha__fecha_fin__isnull = False) |  
                Q(servicio__servicios_adicionales_ficha__fecha_fin__isnull = False))
                )
        context["fotos_pendientes"] = fotos_pendientes

        
        
        fotos_imprimiendo = EnviosImpresion.objects.filter(
                Q(fecha_envio__isnull=False) & Q(fecha_retorno__isnull=True)
                ).exclude( Q(servicio__servicios_contrato_ficha__fecha_fin__isnull = False) |  
                Q(servicio__servicios_adicionales_ficha__fecha_fin__isnull = False))
        context["fotos_imprimiendo"] = fotos_imprimiendo

        fotos_impresas = EnviosImpresion.objects.filter(
                Q(fecha_envio__isnull=False) & Q(fecha_retorno__isnull=False)
                ).exclude( ( Q(servicio__servicios_contrato_ficha__fecha_fin__isnull = False) |  
                Q(servicio__servicios_adicionales_ficha__fecha_fin__isnull = False))
            )
        context["fotos_impresas"] = fotos_impresas

        return render(request,'estudio/envios_impresion.html',context)
    
    def post(self,request,*args,**kwargs):
        data = request.POST
        
        if "foto-imprimir" in data:
            fotos_imprimir = []
            if "foto-imprimir" in data: fotos_imprimir = list(dict(data)["foto-imprimir"])
            for id in fotos_imprimir:
                envio = EnviosImpresion.objects.get(id=id)
                envio.casa = CasaImpresion.objects.get(id=data["casa-impresion"])
                envio.fecha_envio = timezone.now()
                envio.save()

        elif "action" in data and data["action"] == "back":
            envios = []
            if "foto-impresa" in data: envios = list(dict(data)["foto-impresa"])
            for id in envios:
                envio = EnviosImpresion.objects.get(id=id)
                envio.casa = None
                envio.fecha_envio = None
                envio.save()

        elif "action" in data and data["action"] == "next":
            envios = []
            if "foto-impresa" in data: envios = list(dict(data)["foto-impresa"])
            for id in envios:
                envio = EnviosImpresion.objects.get(id=id)
                envio.fecha_retorno = timezone.now()
                envio.save()

        elif "action" in data and data["action"] == "back-impresion":
            envios = []
            if "foto-impresa-ok" in data: envios = list(dict(data)["foto-impresa-ok"])

            for id in envios:
                envio = EnviosImpresion.objects.get(id=id)
                envio.fecha_retorno = None
                envio.save()


        return redirect(str(request.build_absolute_uri()))

@method_decorator(login_required, name='dispatch')
class BolsaView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        stock = StockEstudio.objects.filter(activo=True, cantidad_actual__gt = 0)
        total_reponer = stock.aggregate(total_reponer=Sum("deuda"))
        

        context = {"stock":stock,"reponer":total_reponer}

        return render(request,'estudio/ipv_bolsa.html',context)
    
@method_decorator(login_required, name='dispatch')
class ConfigView(View):
    def get(self,request,*args,**kwargs):
        servicios = Servicio.objects.filter(activo=True)
        tipos = TipoContrato.objects.filter(activo=True)
        contratos = Contrato.objects.filter(activo=True)
        fotografos = Fotografo.objects.filter(activo=True)
        editor = Editor.objects.filter(activo=True)
        casas_impresion = CasaImpresion.objects.filter(activo=True)
        grupo_estado = GrupoEstado.objects.filter(activo=True)
        
        context = {"servicios":servicios,"tipos":tipos,"contratos":contratos,"fotografos":fotografos,
                   "editores":editor,"casas_impresion":casas_impresion,"estados":grupo_estado}
        return render(request,'estudio/config/config.html',context)
    
def add_fotografo(request):
    if request.method == 'POST':
        data = request.POST

        if "id-delete" in data and data["id-delete"] != "":
            d = Fotografo.objects.get(id = data["id-delete"])
            d.activo  = False
            d.save()
            return redirect("ConfigEstudio")

        nombre = super_upper(data["nombre"])
        if "id-edit" in data and data["id-edit"] != "":
            fotografo = Fotografo.objects.get(id = data["id-edit"])
            fotografo.nombre = nombre
            fotografo.save()
            return redirect("ConfigEstudio")

        fotografo = Fotografo.objects.create(nombre=nombre)                
        return redirect("ConfigEstudio")
    else:
        return redirect("ConfigEstudio")
  
def add_editor(request):
    if request.method == 'POST':
        data = request.POST

        if "id-delete" in data and data["id-delete"] != "":
            d = Editor.objects.get(id = data["id-delete"])
            d.activo  = False
            d.save()
            return redirect("ConfigEstudio")

        nombre = super_upper(data["nombre"])
        pago = float(data["pago_trabajador"])
        if "id-edit" in data and data["id-edit"] != "":
            e = Editor.objects.get(id = data["id-edit"])
            e.nombre = nombre
            e.pago = pago
            e.save()
            return redirect("ConfigEstudio")
        

        editor = Editor.objects.create(nombre=nombre)
        editor.pago = pago
        editor.save()
        
        return redirect("ConfigEstudio")
    else:
        return redirect("ConfigEstudio")
  
def add_casa_impresion(request):
    if request.method == 'POST':
        data = request.POST

        if "id-delete" in data and data["id-delete"] != "":
            d = CasaImpresion.objects.get(id = data["id-delete"])
            d.activo  = False
            d.save()
            return redirect("ConfigEstudio")

        nombre = super_upper(data["nombre"])

        if "id-edit" in data and data["id-edit"] != "":
            r = CasaImpresion.objects.get(id = data["id-edit"])
            r.nombre = nombre
            r.save()
            return redirect("ConfigEstudio")
        
        responsable = CasaImpresion.objects.create(nombre=nombre)
        return redirect("ConfigEstudio")
    else:
        return redirect("ConfigEstudio")
      
def add_servicio(request):
    if request.method == 'POST':
        data = request.POST

        if "id-delete" in data and data["id-delete"] != "":
            d = Servicio.objects.get(id = data["id-delete"])
            ServicioContrato.objects.filter(servicio=d).delete()
            d.activo  = False
            d.save()
            return redirect("ConfigEstudio")

        nombre = super_upper(data["nombre"])
        descripcion = data["descripcion"]
        costo = data["costo"]
        if "servicio-contrato" not in data or data["servicio-contrato"] == "":
            precio = data["precio"]
        else:
            precio = data["costo"]
            
        moneda_precio = data["moneda_precio"]
        
        if "id-edit" in data and data["id-edit"] != "":
            s = Servicio.objects.get(id = data["id-edit"])
            s.nombre = nombre
            s.descripcion = descripcion
            s.costo = costo
            s.precio = precio
            s.moneda_precio = moneda_precio

            if "servicio-contrato" not in data or data["servicio-contrato"] == "":
                if "pago_fotografo" in data and data["pago_fotografo"] != "":
                    s.pago_fotografo = data["pago_fotografo"]
                else:
                    s.pago_fotografo = 0.0

                if "pago_responsable" in data and data["pago_responsable"] != "":
                    s.pago_responsable = data["pago_responsable"]
                else:
                    s.pago_responsable = 0.0

            if "estado" in data.keys():
                estado = GrupoEstado.objects.get(id=data["estado"])
            else:
                estado = None            
            if s.estado != estado: s.estado = estado
            s.save()
            return redirect("ConfigEstudio")

        new_servicio = Servicio.objects.get_or_create(nombre=nombre)
        if new_servicio[1] == False:
            messages.error(request, f'Ya existe el servicio {nombre}')
            return redirect("ConfigEstudio")
        
        servicio = new_servicio[0]
        servicio.descripcion = descripcion
        servicio.costo = costo
        servicio.precio = precio
        servicio.moneda_precio = moneda_precio
        
        if "servicio-contrato" not in data or data["servicio-contrato"] == "":
            servicio.contrato = False
            if "pago_fotografo" in data and data["pago_fotografo"] != "":
                servicio.pago_fotografo = data["pago_fotografo"]
            else:
                servicio.pago_fotografo = 0.0
                
            if "pago_responsable" in data and data["pago_responsable"] != "":
                servicio.pago_responsable = data["pago_responsable"]
            else:
                servicio.pago_responsable = 0.0

        if "estado" in data.keys():
            servicio.estado = GrupoEstado.objects.get(id=data["estado"])

        servicio.save()

        return redirect("ConfigEstudio")
    else:
        return redirect("ConfigEstudio")

def add_estados(request):
    if request.method == 'POST':
        data = request.POST

        if "id-delete" in data and data["id-delete"] != "":
            d = GrupoEstado.objects.get(id = data["id-delete"])
            d.activo  = False
            d.save()
            return redirect("ConfigEstudio")

        nombre = super_upper(data["nombre"])
        if "id-edit" in data and data["id-edit"] != "":
            ge = GrupoEstado.objects.get(id = data["id-edit"])
            ge.nombre = nombre

            if "id-estado" in data:
                ids_estado = list(dict(data)["id-estado"])
                estado_nombre = list(dict(data)["estado-nombre"])
                estado_duracion = list(dict(data)["estado-duracion"])
                i = 0
                for s in ge.estados.all():
                    if str(s.id) not in ids_estado:
                        s.delete()
                    else:
                        s.nombre = estado_nombre[i]
                        s.duracion = estado_duracion[i]
                        s.save()

                        i += 1
                
                for est in ids_estado:
                    if est == "":
                        ge.estados.add(
                            Estado.objects.create(nombre=estado_nombre[i],duracion=estado_duracion[i])
                        )
                        i += 1

                
            ge.save()
            return redirect("ConfigEstudio")


        grupo = GrupoEstado.objects.create(nombre=nombre)

        if "estado-nombre" in data.keys():
            estado_nombre = list(dict(data)["estado-nombre"])
            estado_duracion = list(dict(data)["estado-duracion"])

            for index,nombre in enumerate(estado_nombre,start=0):
                estado = Estado.objects.create(nombre=nombre,duracion=estado_duracion[index])
                grupo.estados.add(estado)

        grupo.save()

        return redirect("ConfigEstudio")
    else:
        return redirect("ConfigEstudio")

def add_tipo_contrato(request):
    if request.method == 'POST':
        data = request.POST

        if "id-delete" in data and data["id-delete"] != "":
            d = TipoContrato.objects.get(id = data["id-delete"])
            d.activo  = False
            d.save()
            return redirect("ConfigEstudio")

        nombre = super_upper(data["nombre"])

        if "id-edit" in data and data["id-edit"] != "":
            tc = TipoContrato.objects.get(id = data["id-edit"])
            tc.nombre = nombre
            tc.save()
            return redirect("ConfigEstudio")
        
        new_tipo = TipoContrato.objects.create(nombre=nombre)                
        return redirect("ConfigEstudio")
    else:
        return redirect("ConfigEstudio")
    
def add_contrato(request):
    if request.method == 'POST':
        data = request.POST

        if "id-delete" in data and data["id-delete"] != "":
            d = Contrato.objects.get(id = data["id-delete"])
            d.activo  = False
            d.save()
            return redirect("ConfigEstudio")
        
        nombre = super_upper(data["nombre"])
        precio = data["precio"]
        moneda_precio = data["moneda_precio"]
        anticipo = data["anticipo"]
        moneda_anticipo = data["moneda_anticipo"]
        pago_fotografo = data["pago_fotografo"]
        pago_responsable = data["pago_responsable"]
        pago_gestor = data["pago_gestor"]
        monto_bolsa = data["monto_bolsa"]

        tipo = TipoContrato.objects.get(id=data["tipo"])

        if "id-edit" in data and data["id-edit"] != "":
            contrato = Contrato.objects.get(id=data["id-edit"])
            contrato.nombre=nombre
            contrato.tipo=tipo
            contrato.precio = precio
            contrato.moneda_precio = moneda_precio
            contrato.anticipo = anticipo
            contrato.moneda_anticipo = moneda_anticipo
            contrato.pago_fotografo = pago_fotografo
            contrato.pago_responsable = pago_responsable
            contrato.pago_gestor = pago_gestor
            contrato.monto_bolsa = monto_bolsa

            contrato.servicios.all().delete()
            if "servicio" in data.keys() and data["servicio"] != "":
                servicios = list(dict(data)["servicio"])
                cantidades = list(dict(data)["cantidad"])
                for index,servicio in enumerate(servicios,start=0):
                    new_servicio = ServicioContrato.objects.create(servicio=Servicio.objects.get(id=servicio),cantidad=cantidades[index])
                    contrato.servicios.add(new_servicio)

            contrato.save()

            return redirect("ConfigEstudio")
        


        new_contrato = Contrato.objects.get_or_create(nombre=nombre,tipo=tipo)
        if new_contrato[1] == False:
            messages.error(request, f'Ya existe el contrato {nombre} de tipo {tipo.nombre}')
            return redirect("ConfigEstudio")
        
        contrato = new_contrato[0]
        contrato.precio = precio
        contrato.moneda_precio = moneda_precio
        contrato.anticipo = anticipo
        contrato.moneda_anticipo = moneda_anticipo
        contrato.pago_fotografo = pago_fotografo
        contrato.pago_responsable = pago_responsable
        contrato.pago_gestor = pago_gestor
        contrato.monto_bolsa = monto_bolsa

        if "servicio" in data.keys() and data["servicio"] != "":
            servicios = list(dict(data)["servicio"])
            cantidades = list(dict(data)["cantidad"])

            for index,servicio in enumerate(servicios,start=0):
                new_servicio = ServicioContrato.objects.create(servicio=Servicio.objects.get(id=servicio),cantidad=cantidades[index])
                contrato.servicios.add(new_servicio)

        contrato.save()

        return redirect("ConfigEstudio")
    else:
        return redirect("ConfigEstudio")


# Para la responsable de contratos/maquillista/responsable de la bolsa
    
@method_decorator(login_required, name='dispatch')
class TransferenciasView(View):
    def get(self,request,*args,**kwargs):
        turno = Turno.objects.get(user=request.user,fin=None)
        transferencias = Transferencia.objects.filter(Q(receptor_id=f"bolsa-estudio") & (Q(turno_id=f"E-{turno.id}") | Q(turno_id=None)) & Q(mensaje_cancelacion__isnull = True)).order_by("alta").reverse()
        
        context = {"transferencias":transferencias}

        return render(request,'estudio/transferencias.html',context)
    
    def post(self,request,*args,**kwargs):
        data = request.POST

        pv_ids = list(dict(data)["producto-pv-id"])
        cantidades = list(dict(data)["cantidad"])
        try:
            turno = Turno.objects.get(user=request.user,fin=None)
            for index,id in enumerate(pv_ids,start=0):
                stock = StockEstudio.objects.get(id=id)
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

                stock.costo = stock.lote.costo_real()
                stock.deuda = stock.lote.costo_real()
                stock.cantidad_inicial = cant
                stock.cantidad_actual = cant
                stock.existencia = existencia
                stock.activo = True
                stock.save()

                if stock.transferencia.turno_id is None and index + 1 == len(pv_ids):
                    stock.transferencia.date_confirm = timezone.now()
                    stock.transferencia.user_confirmacion = request.user.user_str()
                    stock.transferencia.turno_id = f"E-{turno.id}"
                    stock.transferencia.save()
        except Exception as e:
            print(e)
            messages.error(request, "Error al confirmar transferencia, puede que el remitente haya cancelado la transferencia.")

        return redirect("TransferenciasEstudio")

@method_decorator(login_required, name='dispatch')
class RecibirTurnoView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        stock_ids = []
        stock = []
        stock_bolsa = StockEstudio.objects.filter(cantidad_actual__gt=0)

        for s in stock_bolsa:
            if s.producto.id not in stock_ids:
                stock_ids.append(s.producto.id)
                stock.append(s)
            else:
                
                stock[stock_ids.index(s.producto.id)].cantidad_actual += s.cantidad_actual

        context = {"stock":stock}
        return render(request,'estudio/recibir_turno.html',context)

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
                    motivo = f"Inicio de turno de {request.user.user} en el ESTUDIO efectuado con {len(motivos_ajuste)} incidencias."
                )
                    
                message = f"<b>📸 ESTUDIO</b>\n\n"
                message += f"Inicio de turno de {request.user.user} en el ESTUDIO efectuado con {len(motivos_ajuste)} incidencias."
                
                t = threading.Thread(target=lambda:send_message(message,alert.id))
                t.start()
                
            else:
                alert = AlertaAdmin.objects.create(
                    tipo=None,
                    centro_costo = f"S-{turno[0].id}",
                    motivo = f"Inicio de turno de {request.user.user} en el ESTUDIO efectuado sin incidencias."
                )
                message = f"<b>📸 ESTUDIO</b>\n\n"
                message += f"Inicio de turno de {request.user.user} en el ESTUDIO efectuado sin incidencias."
                
                t = threading.Thread(target=lambda:send_message(message,alert.id))
                t.start()
            
            for index,id in enumerate(ids,start=0):
                stock = StockEstudio.objects.filter(producto__id=id,cantidad_actual__gt=0).order_by("alta")
                
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
                    stock = StockEstudio.objects.filter(producto__id=id).order_by("alta")
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
                
            return redirect("TransferenciasEstudio")
        
        #except Exception as e:
            print("Error en el cuadre: ",e)
            return redirect("RecibirTurnoSalon")

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
        return render(request,'estudio/entregar_turno.html',context)
    
    
    def post(self,request,*args,**kwargs):
        data = request.POST
        turno = Turno.objects.get(user=request.user,fin=None)
        turno.fin = timezone.now()
        turno.save()

        return redirect("http://" + str(request.get_host()) + "/logout/?for=estudio")
    
