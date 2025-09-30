import json
from datetime import timedelta,datetime
import sys
import threading
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.contrib.auth import logout,authenticate,login
from django.views import View
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.db.models import Q, Sum
from django.views.decorators.csrf import csrf_exempt

from bot.bot import send_message
from bussiness.models import (AlertaAdmin, CantidadSubproducto, ConfigVar, Descuentos, Formula as FormulaPv, Almacen, FormulaTransformacion, GastosRecepcion, Nota, Pago, 
Servicios, StockAlmacen, Categoria, Cuadre, Cuenta, InformeRecepcion, 
Medida, Producto, PuntoVenta, StockPuntoVenta, StockUsuario, Transferencia, Transformacion, Turno, UserAccount, UserAccountManager, Venta)
from bussiness.utils import punto_venta_required, login_required, set_cookie, toMoney
from caja.models import Caja, Operaciones, ReciboEfectivo
from almacen.models import CambiosAlmacen, Turno as TurnoAlmacen, Nota as NotaAlmacen
from estudio.models import StockEstudio, Turno as TurnoEstudio
from salon.models import Turno as TurnoSalon
from otherworkers.models import Turno as TurnoTrabajador
from kitchen.models import Cocina, Consumo, Formula, NotaCocina, SolicitudCocina, StockCocina, StockProductoCompuestoCocina,Turno as TurnoCosina, Cuadre as CuadreCocina, Nota as NotaCuadreCocina

def super_upper(text:str) -> str:
    return text.upper().translate({
                ord('á'): 'A',
                ord('é'): 'E',
                ord('í'): 'I',
                ord('ó'): 'O',
                ord('ú'): 'U',
            })


# -- Superadmin
@method_decorator(login_required, name='dispatch')
class ConfigView(View):
    def get(self,request,area,*args,**kwargs):
        
        """cocina = Cocina.objects.get(id=5)
        forms = Formula.objects.all()
        for f in forms:
            f.cocinas.add(cocina)
            f.save()"""

        if area == "categorias":
            Categoria.objects.get_or_create(nombre="SUBPRODUCTOS")
            Categoria.objects.get_or_create(nombre="MEDIOS BASICOS")
            Categoria.objects.get_or_create(nombre="UTILES")
            Categoria.objects.get_or_create(nombre="SUBPRODUCTOS SALON")
            Categoria.objects.get_or_create(nombre="ACCESORIOS, PRENDAS Y OTROS")
            
        if area == "medidas":
            Medida.objects.get_or_create(nombre="GALON",abreviatura="GAL")
            Medida.objects.get_or_create(nombre="LITRO",abreviatura="L")
            Medida.objects.get_or_create(nombre="MILILITRO",abreviatura="ML")
            Medida.objects.get_or_create(nombre="UNIDAD",abreviatura="U")
            Medida.objects.get_or_create(nombre="KILOGRAMO",abreviatura="KG")
            Medida.objects.get_or_create(nombre="LIBRA",abreviatura="LB")
            Medida.objects.get_or_create(nombre="GRAMO",abreviatura="GR")
            Medida.objects.get_or_create(nombre="ONZA",abreviatura="OZ")

        for f in Formula.objects.filter(producto__is_compuesto = False):
            f.producto.is_compuesto = True
            f.producto.save()
        
        productos_compuestos = Producto.objects.filter(activo = True,is_compuesto=True).exclude(categoria__nombre = "SUBPRODUCTOS").order_by("nombre")

        if area == "medios_basicos":
            productos = Producto.objects.filter(activo = True,categoria__nombre = "MEDIOS BASICOS",is_compuesto=False).order_by("nombre")
        elif area == "utiles":
            productos = Producto.objects.filter(activo = True,categoria__nombre = "UTILES",is_compuesto=False).order_by("nombre")
        elif area == "productos":
            productos = Producto.objects.filter(activo = True,is_compuesto=False
                                                ).exclude(categoria__nombre = "MEDIOS BASICOS"
                                                ).exclude(categoria__nombre = "UTILES"
                                                ).exclude(categoria__nombre = "SUBPRODUCTOS"
                                                ).exclude(categoria__nombre = "SUBPRODUCTOS SALON"
                                                ).exclude(categoria__nombre = "ACCESORIOS, PRENDAS Y OTROS"
                                                ).order_by("nombre")


        elif area == "subproductos":
            productos = Producto.objects.filter(activo = True,categoria__nombre = "SUBPRODUCTOS",is_compuesto=False).exclude(is_compuesto = True).order_by("nombre")
        elif area == "subproductos_elaborados":
            productos = Producto.objects.filter(activo = True,categoria__nombre = "SUBPRODUCTOS",is_compuesto=True).order_by("nombre")
        elif area == "formulas":
            productos_compuestos = Producto.objects.filter(activo = True,is_compuesto=True).order_by("nombre")
            productos = Producto.objects.filter(activo = True
                                                ).exclude(categoria__nombre = "SUBPRODUCTOS SALON"
                                                ).exclude(categoria__nombre = "ACCESORIOS, PRENDAS Y OTROS"
                                                ).order_by("nombre")#categoria__nombre = "SUBPRODUCTOS"
        else:
            productos = Producto.objects.filter(activo = True
                                                ).exclude(categoria__nombre = "SUBPRODUCTOS SALON"
                                                ).exclude(categoria__nombre = "ACCESORIOS, PRENDAS Y OTROS"
                                                ).order_by("nombre")

                
        conf = ConfigVar.objects.get_or_create(key="precio_usd")
        if conf[1]:
            precio_usd = conf[0]
            precio_usd.value = 270
            precio_usd.save()
            
        precio_usd = conf[0].value
        
        context = { 
                "precio_usd" : precio_usd,
                #"usuarios":UserAccount.objects.filter(is_active = True).order_by("user"),
                "usuarios":UserAccount.objects.all().order_by("user"),
                #"trabajadores_servicio":TrabajadorServicio.objects.filter(activo = True).order_by("nombre"),
                "puntos_venta" : PuntoVenta.objects.filter(activo = True).reverse(),
                "productos" : productos,
                "productos_compuestos" : productos_compuestos,
                "formulas" : Formula.objects.filter(activo=True).order_by("producto__nombre"),
                "medidas" : Medida.objects.filter(activo = True),
                "categorias" : Categoria.objects.filter(activo = True).exclude(nombre="SUBPRODUCTOS SALON").exclude(nombre="ACCESORIOS, PRENDAS Y OTROS"),
                "almacenes" : Almacen.objects.filter(activo = True).order_by("nombre"),
                "cocinas" : Cocina.objects.filter(activo = True),
                "formulas_pv" : FormulaPv.objects.filter(activo = True),
                "servicios" : Servicios.objects.filter(activo = True),
                "formulas_transformacion" : FormulaTransformacion.objects.filter(activo = True)
            }

        return render(request,f'config/{area}.html',context)

@method_decorator(login_required, name='dispatch')
class ConfigVariablesView(View):
    def post(self,request,*args,**kwargs):
        try:
            data = request.POST
            precio_usd = data["precio_usd"]
            conf = ConfigVar.objects.get(key="precio_usd")
            conf.value = precio_usd
            conf.save()

            return redirect("Config",area="variables")
        except Exception as error:
            messages.error(request,"Error al actualizar variables")
            return redirect("Config",area="variables")

@method_decorator(login_required, name='dispatch')
class ConfigUsuarioView(View):
    def post(self,request,*args,**kwargs):
        try:
            data = request.POST
            # Para el DELETE
            if "delete-id" in data.keys():
                user = UserAccount.objects.get(id=data["delete-id"])
                user.is_active = False
                moment = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                user.user = f"{user.user} (Borrado:{moment})"
                user.save()
                return redirect("Config",area="trabajadores")

            if "edit_id" in data.keys() and data["edit_id"] != "":
                user = UserAccount.objects.get(id=data["edit_id"])
                if (UserAccount.objects.filter(user=data["user"], is_active = True).exists() and 
                    UserAccount.objects.filter(user=data["user"], is_active = True).first() != user):
                    messages.error(request, f'Ya existe otro usuario de nombre {user}')
                    return redirect("Config",area="trabajadores")

                if "user" in data.keys() and data["user"] != "": user.user = data['user']
                if "password" in data.keys() and data["password"] != "": user.set_password(data['password'])
                user.ci = data["ci"]
                user.telefono = data["telefono"]
                
                uploaded_files = request.FILES
                if "image-user" in uploaded_files.keys(): user.imagen = uploaded_files["image-user"]                
                elif data["avatar"] == "men-user": user.imagen = "/static/images/men.jpg"
                else: user.imagen = "/static/images/women.jpg"
                
                user.save()
                return redirect("Config",area="trabajadores")
            
            user = data['user']
            password = data['password']            
            roles = list(dict(data)["roles"])

            new_user = UserAccount.objects.filter(user=user, is_active = True)
            if new_user.exists():
                messages.error(request, f'Ya existe un usuario de nombre {user}')
                return redirect("Config",area="trabajadores")
            
            else:
                new_user = UserAccount.objects.create_user(user,password)
                uploaded_files = request.FILES
                new_user.ci = data["ci"]
                new_user.telefono = data["telefono"]
                
                if "image-user" in uploaded_files.keys(): new_user.imagen = uploaded_files["image-user"]                
                elif data["avatar"] == "men-user": new_user.imagen = "/static/images/men.jpg"
                else: new_user.imagen = "/static/images/women.jpg"
                
                for rool in roles:

                    if rool == "superusuario": 
                        new_user.super_permission = True
                        break
                    elif rool == "admin": 
                        new_user.admin_permission = True
                        break
                    elif rool == "salon": 
                        new_user.salon_permission = True
                        break
                    elif rool == "estudio": 
                        new_user.estudio_permission = True
                        break
                    elif rool == "responsable-estudio": 
                        new_user.responsable_estudio_permission = True
                        break

                    elif rool == "balancista":
                        new_user.balanc_permission = True
                        break

                    elif rool == "almacenero":
                        new_user.almacen_permission = True #almacenes.add(Almacen.objects.get(id=rool.replace("A-","")))

                    elif "servicio-" in rool:
                        new_user.pago_servicios.add(Servicios.objects.get(id=rool.split("-")[1]))

                    elif "C-" in rool:
                        cocina = Cocina.objects.get(id=rool.replace("C-",""))
                        cocina.users_access.add(new_user)

                    elif "PV-" in rool:
                        pv = PuntoVenta.objects.get(id=rool.replace("PV-",""))
                        new_user.puntos_venta.add(pv)

                if "pago_909" in data.keys():
                    new_user.pago_909 = True
                else:
                    new_user.pago_909 = False

                new_user.save()


                return redirect("Config",area="trabajadores")
    
        except Exception as error:
            messages.error(request,"Error al agregar usuario")
            return redirect("Config",area="trabajadores")

"""@method_decorator(login_required, name='dispatch')
class ConfigTrabajadorServicioView(View):
    def post(self,request,*args,**kwargs):
        try:
            data = request.POST
            # Para el DELETE
            if "delete-id" in data.keys():
                user = TrabajadorServicio.objects.get(id=data["delete-id"])
                user.delete()
                return redirect("Config",area="trabajadores")
            
            user = data['user']

            new_user = TrabajadorServicio.objects.filter(nombre=user, activo = True)
            if new_user.exists():
                return redirect("Config",area="trabajadores")
            
            else:
                new_user = TrabajadorServicio.objects.create(nombre=user)
                uploaded_files = request.FILES
                
                if "image-user" in uploaded_files.keys(): new_user.imagen = uploaded_files["image-user"]                
                elif data["avatar"] == "men-user": new_user.imagen = "/static/images/men.jpg"
                else: new_user.imagen = "/static/images/women.jpg"

                
                if "pago_909" in data.keys():
                    new_user.pago_909 = True
                else:
                    new_user.pago_909 = False

                pago_servicios = list(dict(data)["pago_servicios"])
                
                for id in pago_servicios:
                    pago_servicio = Servicios.objects.get(id=id)
                    new_user.pago_servicios.add(pago_servicio)
                new_user.save()


                return redirect("Config",area="trabajadores")
        
        except Exception as error:
            print("Error al agregar trabajador:",error)
            return redirect("Config",area="trabajadores")"""

@method_decorator(login_required, name='dispatch')
class ConfigProductoView(View):
    
    def post(self,request,*args,**kwargs):
        try:
            data = request.POST            

            # Para el DELETE
            if "delete-id" in data.keys():
                producto = Producto.objects.get(id=data["delete-id"])
                producto.delete()

                return redirect("Config",area= data["redirect"])
            
            nombre = super_upper(data['nombre'])
            if "codigo" in data.keys():
                codigo = data['codigo']
                if "LINT-" in codigo:
                    codigo = "LINT-"
            else:codigo = "LINT-"
            categoria = data['categoria']
            medida = data['medida']

            if (((codigo != "LINT-" and Producto.objects.filter(Q(codigo=codigo),Q(activo=True)).exists()) or Producto.objects.filter(nombre=nombre,activo=True).exists()) and 
                ("edit-id" not in data.keys() or data['edit-id'] == '')):
                messages.error(request, f'Ya existe un producto de nombre {nombre}')
                return redirect("Config",area= data["redirect"])
            
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

                if "cantidad_ideal_pv" in data:
                    cantidad_ideal = list(dict(data)["cantidad_ideal"])
                    cantidad_ideal_pv = list(dict(data)["cantidad_ideal_pv"])

                    cantidades_ideales_pedidos = []
                    for i, id in enumerate(cantidad_ideal_pv,start=0):
                        pv_c = cantidad_ideal[i]
                        if pv_c != "":
                            cantidades_ideales_pedidos.append(f"{id}:{pv_c}")

                    new_producto.cantidades_ideales_pedidos = "|".join(cantidades_ideales_pedidos)



                if categoria and str(categoria).isnumeric():
                    new_producto.categoria = Categoria.objects.get(id=categoria)
                if medida and str(medida).isnumeric():
                    new_producto.medida = Medida.objects.get(id=medida)
                
                if "producto-compuesto" in data:
                    new_producto.is_compuesto = True
                new_producto.save()
                
                return redirect("Config",area= data["redirect"])
            
        except Exception as e:
            print(e)
            return redirect("Config",area="productos")

def addProducto(request):
    if not request.user.is_authenticated:
        logout(request)
        return redirect('login')
    
    if request.method == 'POST':
        try:
            data = request.POST

            nombre = super_upper(data['nombre'])
            if "codigo" in data.keys():
                codigo = data['codigo']
                if "LINT-" in codigo:
                    codigo = "LINT-"
            else:codigo = "LINT-"


            if (codigo != "LINT-"  and Producto.objects.filter(Q(codigo=codigo),Q(activo=True)).exists()) or Producto.objects.filter(nombre=nombre,activo=True).exists():
                csrf = str(render(request,"csrf.html").content).replace('''b'<input type="hidden" name="csrfmiddlewaretoken" value="''',"").replace("""">'""","")
                returned = {"csrf":csrf,"register":"exist"}
                data =json.dumps(returned)
                return HttpResponse(data,"application/json")
            
            else:
                new_producto = Producto.objects.create(nombre=nombre)
                if codigo == "LINT-":codigo += str(new_producto.id)
                new_producto.codigo = codigo
                uploaded_files = request.FILES
                
                if "image-product" in uploaded_files.keys(): 
                    new_producto.imagen = uploaded_files["image-product"]
                    new_producto.save()
                    imagen = new_producto.imagen.url
                else: 
                    imagen = data["image-product"]
                    imagen = f"/static/images/productos/{imagen}.jpg"
                    new_producto.imagen = imagen

                descripcion = data['descripcion']
                new_producto.descripcion = descripcion

                precio_venta = data['precio_venta']
                if precio_venta != "":new_producto.precio_venta = precio_venta


                categoria = data['categoria']
                medida = data['medida']
                if categoria and str(categoria).isnumeric():
                    new_producto.categoria = Categoria.objects.get(id=categoria)
                if medida and str(medida).isnumeric():
                    new_producto.medida = Medida.objects.get(id=medida)
                new_producto.save()


                csrf = str(render(request,"csrf.html").content).replace('''b'<input type="hidden" name="csrfmiddlewaretoken" value="''',"").replace("""">'""","")
                
                new_producto_return = {
                    "id":new_producto.id,                    
                    "codigo":new_producto.codigo,
                    "nombre":new_producto.nombre,
                    "descripcion":new_producto.descripcion,
                    "precio_venta":toMoney(new_producto.precio_venta),
                    "medida":new_producto.medida.nombre,
                    "imagen":new_producto.img(),
                }
                
                if new_producto.categoria: new_producto_return["categoria"] = new_producto.categoria.nombre
                else: new_producto_return["categoria"] = "-"

                
                returned = {
                    "csrf":csrf,
                    "register":"success",
                    "new_producto":new_producto_return
                }

                data =json.dumps(returned)
                return HttpResponse(data,"application/json")
            
        except Exception as e:
            print(e)
            csrf = str(render(request,"csrf.html").content).replace('''b'<input type="hidden" name="csrfmiddlewaretoken" value="''',"").replace("""">'""","")
            returned = {"csrf":csrf,"register":"error"}
            data =json.dumps(returned)
            return HttpResponse(data,"application/json")
        
    else:
        csrf = str(render(request,"csrf.html").content).replace('''b'<input type="hidden" name="csrfmiddlewaretoken" value="''',"").replace("""">'""","")
        returned = {"csrf":csrf,"register":"error"}
        data =json.dumps(returned)
        return HttpResponse(data,"application/json")
    
@method_decorator(login_required, name='dispatch')
class ConfigMedidaView(View):
    def post(self,request,*args,**kwargs):
        #try:
            data = request.POST

            # Para el DELETE
            if "delete-id" in data.keys():
                medida = Medida.objects.get(id=data["delete-id"])
                medida.delete()

                return redirect("Config",area="medidas")
            
            nombre = super_upper(data['medida'])
            abreviatura = super_upper(data['abreviatura'])
            
            if "edit-id" in data.keys() and data['edit-id'] != '':
                medida = Medida.objects.get(id=data['edit-id'])
                medida.nombre = nombre
                medida.abreviatura = abreviatura
                medida.save()

                return redirect("Config",area="medidas")
            
            # Para el CREATE
            new_medida = Medida.objects.get_or_create(nombre=nombre,abreviatura=abreviatura,activo=True)
            
            if new_medida[1] == True:
                return redirect("Config",area="medidas")
            
            else:
                messages.error(request, f'Ya existe una unidad de medida de nombre {nombre}')
                return redirect("Config",area="medidas")
        #except Exception as e:
            print(e)
            return redirect("Config",area="medidas")

@method_decorator(login_required, name='dispatch')
class ConfigCategoriaView(View):
    def post(self,request,*args,**kwargs):
        try:
            data = request.POST

            # Para el DELETE
            if "delete-id" in data.keys():
                categoria = Categoria.objects.get(id=data["delete-id"])
                categoria.delete()
                return redirect("Config",area="categorias")
            
            if "edit-id" in data.keys() and data['edit-id'] != '':
                c = Categoria.objects.get(id=data['edit-id'])
                c.nombre = super_upper(data["categoria"])
                c.save()
                return redirect("Config",area="categorias")


            # Para el CREATE
            new_categoria = Categoria.objects.get_or_create(nombre=super_upper(data['categoria']),activo=True)
            
            if new_categoria[1] == True:
                return redirect("Config",area="categorias")
            
            else:
                n = super_upper(data['categoria'])
                messages.error(request, f'Ya existe una categoría de nombre {n}')
                return redirect("Config",area="categorias")
            
        except:
            return redirect("Config",area="categorias")

@method_decorator(login_required, name='dispatch')
class ConfigPuntoVentaView(View):
    def post(self,request,*args,**kwargs):
        try:
            data = request.POST
            
            # Para el DELETE
            if "delete-id" in data.keys():
                pv = PuntoVenta.objects.get(id=data["delete-id"])
                pv.delete()
                
                return redirect("Config",area="puntos_venta")


            if "edit-id" in data.keys() and data['edit-id'] != '':
                pv = PuntoVenta.objects.get(id=data['edit-id'])
                pv.nombre = super_upper(data["nombre"])
                pv.direccion = super_upper(data["direccion"])
                pv.codigo = data["codigo"]

                if "pago_ganancia" in data.keys() and str(data['pago_ganancia']) != "": 
                    pv.pago_ganancia = data['pago_ganancia']
                else:
                    pv.pago_ganancia = None

                if "pago_venta" in data.keys() and str(data['pago_venta']) != "": 
                    pv.pago_venta = data['pago_venta']
                else:
                    pv.pago_venta = None
                    
                if "pago_minutos" in data.keys() and str(data['pago_minutos']) != "":
                    pv.pago_minutos = data['pago_minutos']
                else:
                    pv.pago_minutos = None
                    
                if "pago_fijo" in data.keys() and  str(data['pago_fijo']) != "": 
                    pv.pago_fijo = data['pago_fijo']
                else:
                    pv.pago_fijo = None

                if "pago_asociado" in data.keys() and  str(data['pago_asociado']) != "": 
                    pv.pago_asociado = data['pago_asociado']
                else:
                    pv.pago_asociado = None
                    
                if ("pago_conciliado1" in data.keys() and  str(data['pago_conciliado1']) != "" and
                "pago_conciliado2" in data.keys() and  str(data['pago_conciliado2']) != "" ): 
                    pv.pago_conciliado = f"{data['pago_conciliado1']}|{data['pago_conciliado2']}"
                else:
                    pv.pago_conciliado = None

                pv.save()

                return redirect("Config",area="puntos_venta")


            # Para el CREATE
            pv_create = PuntoVenta.objects.get_or_create(nombre=data['nombre'],activo=True)
            
            if pv_create[1] == True:
                pv = pv_create[0]
                pv.direccion = data["direccion"]
                pv.codigo = data["codigo"]
                pv.save()
                
                if "pago_ganancia" in data.keys() and str(data['pago_ganancia']).isnumeric(): pv.pago_ganancia = data['pago_ganancia']
                if "pago_venta" in data.keys() and str(data['pago_venta']).isnumeric(): pv.pago_venta = data['pago_venta']
                if "pago_minutos" in data.keys() and str(data['pago_minutos']).isnumeric(): pv.pago_minutos = data['pago_minutos']
                if "pago_fijo" in data.keys() and  str(data['pago_fijo']).isnumeric(): pv.pago_fijo = data['pago_fijo']
                if ("pago_conciliado1" in data.keys() and  str(data['pago_conciliado1']).isnumeric() and
                "pago_conciliado2" in data.keys() and  str(data['pago_conciliado2']).isnumeric() ): 
                    pv.pago_conciliado = f"{data['pago_conciliado1']}|{data['pago_conciliado2']}"

                if "pago_conciliado1" in data.keys() and  str(data['pago_asociado']).isnumeric():pv.pago_asociado = data['pago_asociado']
                
                return redirect("Config",area="puntos_venta")
            
            else:
                n = data['nombre']
                messages.error(request, f'Ya existe un punto de venta de nombre {n}')
                return redirect("Config",area="puntos_venta")

        except Exception as e:
            print("Error: ",e)
            
            return redirect("Config",area="puntos_venta")

@method_decorator(login_required, name='dispatch')
class ConfigAlmacenView(View):
    def post(self,request,*args,**kwargs):
        try:
            data = request.POST
            
            # Para el DELETE
            if "delete-id" in data.keys():
                almacen = Almacen.objects.get(id=data["delete-id"])
                almacen.delete()
                
                return redirect("Config",area="almacenes")

            if "edit-id" in data.keys() and data['edit-id'] != '':
                almacen = Almacen.objects.get(id=data['edit-id'])
                almacen.nombre = super_upper(data["nombre"])
                almacen.direccion = super_upper(data["direccion"])
                almacen.codigo = data["codigo"]
                if "audit" in data.keys():almacen.is_audit = True
                else:almacen.is_audit = False
                almacen.save()

                return redirect("Config",area="almacenes")
        
            # Para el CREATE
            almacen_create = Almacen.objects.get_or_create(nombre=data['nombre'],activo=True)
            
            if almacen_create[1] == True:
                almacen = almacen_create[0]
                almacen.direccion = data["direccion"]
                almacen.codigo = data["codigo"]
                if "audit" in data.keys():almacen.is_audit = True
                else:almacen.is_audit = False
                almacen.save()                
                return redirect("Config",area="almacenes")
            else:
                n = data['nombre']
                messages.error(request, f'Ya existe un almacén de nombre {n}')
                return redirect("Config",area="almacenes")

        except Exception as e:
            print(e)
            return redirect("Config",area="almacenes")

@method_decorator(login_required, name='dispatch')
class ConfigServicioView(View):
    def post(self,request,*args,**kwargs):
        try:
            data = request.POST
            #print(data)
            
            # Para el DELETE
            if "delete-id" in data.keys():
                almacen = Servicios.objects.get(id=data["delete-id"])
                almacen.delete()
                return redirect("http://" + str(request.get_host()) + "/config/servicios/")

            servicio = Servicios.objects.create(nombre=data['nombre'])
            servicio.descripcion = data['descripcion']

            """nombres_pagos = list(dict(data)["pago-nombre"])
            cantidad_pagos = list(dict(data)["pago-cantidad"])
            
            for index,nombre in enumerate(nombres_pagos,start=0):
                pago_servicio = PagoServicio.objects.create(nombre=nombre,monto=cantidad_pagos[index])
                servicio.pagos.add(pago_servicio)"""

            servicio.save()
            return redirect("http://" + str(request.get_host()) + "/config/servicios/")

        except:
            return redirect("http://" + str(request.get_host()) + "/config/servicios/")

@method_decorator(login_required, name='dispatch')
class ConfigCocinaView(View):
    def post(self,request,*args,**kwargs):
        try:
            data = request.POST          
            
            # Para el DELETE
            if "delete-id" in data.keys():
                cocina = Cocina.objects.get(id=data["delete-id"])
                cocina.delete()
                return redirect("Config",area="cocinas")

            puntos_venta = list(dict(data)["puntos_venta"])

            if "edit-id" in data.keys() and data["edit-id"] != "":
                cocina = Cocina.objects.get(id=data["edit-id"])            
                cocina.nombre=data['nombre']
                cocina.activo=True
                cocina.direccion = data["direccion"]
                cocina.categoria = data["categoria"]
                cocina.codigo = data["codigo"]
                cocina.puntos_venta.clear()
                for pv in puntos_venta:
                    cocina.puntos_venta.add(PuntoVenta.objects.get(id = pv))                
                
                if "pago_fijo_cocinero" in data.keys(): 
                    cocina.pago_fijo_cocinero = float(data['pago_fijo_cocinero'])
                else:
                    cocina.pago_fijo_cocinero = 0.0

                if "pago_fijo_ayudante" in data.keys(): 
                    cocina.pago_fijo_ayudante = float(data['pago_fijo_ayudante'])
                else:
                    cocina.pago_fijo_ayudante = 0.0

                if "pago_porciento_cocinero" in data.keys(): 
                    cocina.porciento_cocinero = float(data['pago_porciento_cocinero'])
                else:
                    cocina.porciento_cocinero = 0.0

                cocina.save()
                return redirect("Config",area="cocinas")

            # Para el CREATE
            cocina_create = Cocina.objects.get_or_create(nombre=data['nombre'],activo=True)
            
            if cocina_create[1] == True:
                cocina = cocina_create[0]
                cocina.direccion = data["direccion"]
                cocina.categoria = data["categoria"]
                cocina.codigo = data["codigo"]
                
                    
                if "pago_fijo_cocinero" in data.keys() and str(data['pago_fijo_cocinero']).isnumeric(): 
                    cocina.pago_fijo_cocinero = data['pago_fijo_cocinero']
                else:
                    cocina.pago_fijo_cocinero = None

                if "pago_fijo_ayudante" in data.keys() and str(data['pago_fijo_ayudante']).isnumeric(): 
                    cocina.pago_fijo_ayudante = data['pago_fijo_ayudante']
                else:
                    cocina.pago_fijo_ayudante = None

                if "pago_porciento_cocinero" in data.keys() and str(data['pago_porciento_cocinero']).isnumeric(): 
                    cocina.porciento_cocinero = data['pago_porciento_cocinero']
                else:
                    cocina.porciento_cocinero = None

                for pv in puntos_venta:
                    cocina.puntos_venta.add(PuntoVenta.objects.get(id = pv))
                cocina.save()

                return redirect("Config",area="cocinas")
            else:
                n = data['nombre']
                messages.error(request, f'Ya existe una cocina de nombre {n}')
                return redirect("Config",area="cocinas")

        except Exception as e:
            print(e)
            return redirect("Config",area="cocinas")

@method_decorator(login_required, name='dispatch')
class ConfigFormulaView(View):
    def post(self,request,*args,**kwargs):
        try:
            data = request.POST
            
            # Para el DELETE
            if "delete-id" in data.keys():
                formula = FormulaPv.objects.get(id=data["delete-id"])
                formula.delete()
                return redirect("Config",area="formulas_venta")

            # Para el CREATE
            if "actualizar-id" in data:
                formula = FormulaPv.objects.get(id=data['actualizar-id'])

                formula.subproductos.clear()

                cantidad_subproducto = list(dict(data)["cantidad-subproducto"])
                subproducto_id = list(dict(data)["subproducto-id"])

                formula.nombre = super_upper(data['nombre'])
                #formula.tipo = data['tipo']
                formula.descripcion = data['descripcion']
                for index,id in enumerate(subproducto_id,start=0):
                    cant_subproducto = CantidadSubproducto.objects.create(producto=Producto.objects.get(id=id),cantidad=cantidad_subproducto[index])
                    formula.subproductos.add(cant_subproducto)

                if "pago-elaboracion-monto" in data and data["pago-elaboracion-monto"] != "":
                    formula.pago = data["pago-elaboracion-monto"]
                else:formula.pago = 0.0

                if "precio-venta" in data and data["precio-venta"] != "":
                    formula.precio = data["precio-venta"]
                else:formula.precio = 0.0
                
                formula.save()

            else:
                formula = FormulaPv.objects.get_or_create(nombre=super_upper(data['nombre']),activo=True)

                cantidad_subproducto = list(dict(data)["cantidad-subproducto"])
                subproducto_id = list(dict(data)["subproducto-id"])
                
                if formula[1] == True:
                    formula = formula[0]
                    formula.nombre = super_upper(data['nombre'])
                    #formula.tipo = data['tipo']
                    formula.descripcion = data['descripcion']
                    #formula.medida = Medida.objects.get(id=data['medida'])
                    for index,id in enumerate(subproducto_id,start=0):
                        cant_subproducto = CantidadSubproducto.objects.create(producto=Producto.objects.get(id=id),cantidad=cantidad_subproducto[index])
                        formula.subproductos.add(cant_subproducto)

                    if "pago-elaboracion-monto" in data and data["pago-elaboracion-monto"] != "":
                        formula.pago = data["pago-elaboracion-monto"]
                    else:formula.pago = 0.0

                    if "precio-venta" in data and data["precio-venta"] != "":
                        formula.precio = data["precio-venta"]
                    else:formula.precio = 0.0
                    
                    formula.save()


            return redirect("Config",area="formulas_venta")

        except Exception as e:
            print(e)
            return redirect("Config",area="formulas_venta")

@method_decorator(login_required, name='dispatch')
class ConfigTransformacionView(View):
    def post(self,request,*args,**kwargs):
        try:
            data = request.POST

            # Para el DELETE
            if "delete-id" in data.keys():
                formula = FormulaTransformacion.objects.get(id=data["delete-id"])
                formula.delete()
                return redirect("http://" + str(request.get_host()) + "/config/formulas_transformacion/")
            
                
            # Para el CREATE
            producto_inicial = data["producto_inicial"]
            producto_final = data["producto_final"]
            cantidad_inicial = data["cantidad_inicial"]
            cantidad_final = data["cantidad_final"]
            
            if "edit_id" in data.keys() and data["edit_id"] != "":
                formula = FormulaTransformacion.objects.filter(
                    producto_inicial = Producto.objects.get(id=producto_inicial),
                    producto_final = Producto.objects.get(id=producto_final),
                    cantidad_inicial = cantidad_inicial,
                    cantidad_final = cantidad_final
                )
                
                formula_edit = FormulaTransformacion.objects.get(id=data["edit_id"])

                if formula.exists() and formula.first() != formula_edit: messages.error(request, f'Ya existe la fórmula de transformación')
                
                formula_edit.producto_inicial = Producto.objects.get(id=producto_inicial)
                formula_edit.producto_final = Producto.objects.get(id=producto_final)

                if "free_transform" in data: formula_edit.cantidad_final = cantidad_final
                else: formula_edit.cantidad_final = 0.0

                formula_edit.cantidad_inicial = cantidad_inicial

                formula_edit.save()

                return redirect("http://" + str(request.get_host()) + "/config/formulas_transformacion/")
            
            new_formula = FormulaTransformacion.objects.get_or_create(
                producto_inicial = Producto.objects.get(id=producto_inicial),
                producto_final = Producto.objects.get(id=producto_final),
                cantidad_inicial = cantidad_inicial,
            )
            
            if new_formula[1] == True:
                formula = new_formula[0]
                
                if "free_transform" in data:
                    formula.cantidad_final = cantidad_final
                    formula.save()
                return redirect("http://" + str(request.get_host()) + "/config/formulas_transformacion/")
            
            else:
                messages.error(request, f'Ya existe la fórmula de transformación')
                return redirect("http://" + str(request.get_host()) + "/config/formulas_transformacion/")

        except:
            messages.error(request,"Error al agregar fórmula de transformación")
            return redirect("http://" + str(request.get_host()) + "/config/formulas_transformacion/")

def getNotas(request):
    if request.method == 'GET':
        count = int(request.GET["count"])
        notas = Nota.objects.all().order_by("-fecha")

        cant_sumar = 9

        if len(notas) > count+cant_sumar:
            end = False
        else:
            end = True

        notas = notas[count:count+cant_sumar]
        
        notas_return = []

        for nota in notas:
            notas_return.append({
                "origen":nota.origen,
                "motivo":nota.motivo,
                "detalles":nota.detalles,
                "momento":nota.momento,
                "fecha":nota.fecha.strftime('%d/%m/%Y %I:%M:%S %p'),
                "date":nota.fecha.strftime('%d/%m/%Y')
            })

        returned = {
            "success":"YES",
            "end":end,
            "notas":notas_return
        }
        
        return HttpResponse(json.dumps(returned),"application/json")
    else:
        returned = {
            "success":"NO"
        }
        
        return HttpResponse(json.dumps(returned),"application/json")

@method_decorator(login_required, name='dispatch')
class MenuView(View):
    def get(self,request,pv_id,*args,**kwargs):

        productos_list = []
        pv = PuntoVenta.objects.get(id=pv_id)
        productos = StockPuntoVenta.objects.filter(punto_venta=pv)
        for producto in productos:
            if producto.producto not in productos_list:productos_list.append(producto.producto)

                
        context = {"productos":productos_list}

        return render(request,'menu.html',context)

# -- Genericos
class Login(View):
    def get(self,request,*args,**kwargs):
        if not UserAccount.objects.filter(user="Administrador").exists():
            superuser = UserAccount.objects.create(user='Administrador')
            superuser.set_password('Admin799160***')
            superuser.is_superuser = True
            superuser.is_staff = True
            superuser.super_permission = True
            superuser.save()

        if request.user.is_authenticated:
            if request.user.super_permission == True:
                return redirect("AdminAlertas")            
            if request.user.balanc_permission == True:
                return redirect("AdminAlertas")
            if request.user.almacen_permission == True:
                if TurnoAlmacen.objects.filter(user=request.user,fin=None).exists():
                    return redirect("StockAlmacen")
                
                elif TurnoAlmacen.objects.filter(fin=None).exists():
                    logout(request)
                    messages.error(request, "Almacenero con turno activo")
                    return redirect("login")
            
                else:
                    return redirect("RecibirTurnoAlmacen")
            
            if request.user.admin_permission == True:
                return redirect("InformeRecepcion")




            if request.user.estudio_permission == True:
                return redirect("RealizadosEstudio")
            
            if request.user.responsable_estudio_permission == True:
                if TurnoEstudio.objects.filter(user=request.user,fin=None).exists():
                    return redirect("TransferenciasEstudio")
                
                elif TurnoEstudio.objects.filter(fin=None).exists():
                    logout(request)

                else:
                    return redirect("RecibirTurnoEstudio")
            
            if request.user.salon_permission == True:
                if request.user.super_permission or request.user.balanc_permission:
                    return redirect("ServiciosSalon")
                
                if TurnoSalon.objects.filter(user=request.user,fin=None).exists():
                    return redirect("ClientesSalon")
                else:
                    return redirect("RecibirTurnoSalon")

            if request.user.punto_venta():
                punto_venta=request.user.punto_venta()

                if Turno.objects.filter(user=request.user,punto_venta=punto_venta,fin=None).exists():
                    return redirect("CuentasPuntoVenta")
                
                elif Turno.objects.filter(punto_venta=punto_venta,fin=None).exists():
                    logout(request)
                    
                    messages.error(request, "Punto de Venta en funcionamiento, si su intención es entrar como trabajador auxiliar pídale al trabajador principal que le agregue.")
                    return redirect("http://" + str(request.get_host()) + f'/?for=PV-{punto_venta.id}')
                
                else:
                    return redirect("RecibirTurno", pv_id="")
        
            if request.user.pago_servicios.all().exists(): return redirect("IpvTrabajador")
                
        puntos_ventas = PuntoVenta.objects.filter(activo=True)
        cocinas = Cocina.objects.filter(activo=True)

        data = request.GET 
        rool = "admin"
        for_select = None

        if "for" in data:
            rool = data["for"]

            if "estudio" == rool:
                for_select = "Estudio"
                users =  UserAccount.objects.filter(
                            Q(estudio_permission = True) | 
                            Q(super_permission = True) |
                            Q(balanc_permission = True) |
                            Q(responsable_estudio_permission = True)
                    ).exclude(is_active = False)

            elif "salon" == rool:
                for_select = "Salon"
                users =  UserAccount.objects.filter(Q(salon_permission = True) | 
                                                    Q(super_permission = True) |
                                                    Q(balanc_permission = True)
                                                ).exclude(is_active = False)

            elif "C-" in rool:
                for_select = cocinas.filter(id=rool.replace("C-","")).first()
                users = for_select.users_access.all().exclude(is_active = False)

            elif "PV-" in rool:
                id = rool.replace("PV-","")
                for_select = puntos_ventas.filter(id=id).first()
                users = UserAccount.objects.filter(puntos_venta__id=id).exclude(is_active = False)

            elif "servicio" == rool:
                for_select = "Trabajador de servicios"
                users = UserAccount.objects.filter(pago_servicios__isnull=False).exclude(is_active = False)

            else:
                for_select = "Administración/Balance/Almacenes"
                users = UserAccount.objects.filter(Q(super_permission = True) | Q(balanc_permission = True) | Q(almacen_permission = True) | Q(admin_permission = True)).exclude(is_active = False)

            if for_select and type(for_select) != str: for_select = for_select.nombre

        else:
            users = UserAccount.objects.filter(Q(super_permission = True) | Q(balanc_permission = True) | Q(almacen_permission = True) | Q(admin_permission = True)).exclude(is_active = False)
            for_select = "Administración/Balance/Almacenes"

        context = {"puntos_ventas":puntos_ventas,"cocinas":cocinas,"for_select":for_select,"users":users.distinct(),"for_url":rool}


        return render(request,'login.html',context)
    
    def post(self,request,*args,**kwargs):
        user_send = request.POST['user']
        password = request.POST['password']
        for_open = request.POST['for']
        
        user = authenticate(request, user=user_send, password=password)

        

        if user is not None:
            login(request, user)

            if for_open == "admin":
                if user.super_permission == True:

                    """ TSOK
                    if TurnoTrabajador.objects.filter(user=request.user,fin=None).exists():
                        return redirect("AdminAlertas")
                    else:
                        return redirect("RecibirTurnoTrabajador") """

                    return redirect("AdminAlertas")

                if user.balanc_permission == True:

                    """ TSOK
                    if TurnoTrabajador.objects.filter(user=request.user,fin=None).exists():
                        return redirect("AdminAlertas")
                    else:
                        return redirect("RecibirTurnoTrabajador") """
                        
                    return redirect("AdminAlertas")

                if user.almacen_permission == True:
                    if TurnoAlmacen.objects.filter(user=request.user,fin=None).exists():
                        return redirect("StockAlmacen")
                    
                    elif TurnoAlmacen.objects.filter(fin=None).exists():
                        logout(request)

                        messages.error(request, "Almacenero con turno activo")
                        return redirect("http://" + str(request.get_host()) + f'/?for={for_open}')
                
                    else:
                        return redirect("RecibirTurnoAlmacen")

                if user.admin_permission == True:
                    return redirect("InformeRecepcion")


            if for_open == "estudio":

                if request.user.super_permission or request.user.balanc_permission:
                    return redirect("NewClienteEstudio")
                
                if request.user.responsable_estudio_permission == True:
                    if TurnoEstudio.objects.filter(user=request.user,fin=None).exists():
                        return redirect("TransferenciasEstudio")                    
                
                    elif TurnoEstudio.objects.filter(fin=None).exists():
                        turno = TurnoEstudio.objects.filter(fin=None).first()
                        logout(request)                        
                        messages.error(request, f"El usuario {turno.user} tiene un turno abierto en el estido")
                        return redirect("http://" + str(request.get_host()) + f'/?for={for_open}')
                    
                    else:
                        return redirect("RecibirTurnoEstudio")
                
                return redirect("RealizadosEstudio")

            if for_open == "salon":
                if request.user.super_permission or request.user.balanc_permission:
                    return redirect("ServiciosSalon")
                if user.salon_permission == True:
                    if TurnoSalon.objects.filter(user=request.user,fin=None).exists():
                        return redirect("ClientesSalon")
                    else:
                        return redirect("RecibirTurnoSalon") 

            if for_open == "servicio" :
                if TurnoTrabajador.objects.filter(user=request.user,fin=None).exists():
                    return redirect("IpvTrabajador")
                else:
                    return redirect("RecibirTurnoTrabajador") 

            if "C-" in for_open:
                if TurnoCosina.objects.filter(user=request.user,cocina__id=for_open.replace("C-",""),fin=None).exists():
                    response = redirect("StockCocina")
                    set_cookie(response,"cocina_id",for_open)
                    set_cookie(response,"cocina_name",Cocina.objects.get(id=for_open.replace("C-","")).nombre)
                    return response
                
                elif TurnoCosina.objects.filter(cocina__id=for_open.replace("C-",""),fin=None).exists():
                    logout(request)

                    messages.error(request, "Cocina con turno activo")
                    return redirect("http://" + str(request.get_host()) + f'/?for={for_open}')
                
                else:
                    response = redirect("RecibirTurnoCocina", coc_id=int(for_open.replace("C-","")))
                    set_cookie(response,"cocina_id",for_open)
                    set_cookie(response,"cocina_name",Cocina.objects.get(id=for_open.replace("C-","")).nombre)
                    return response
                
            if "PV-" in for_open:
                pv_id = for_open.replace("PV-","")
                if Turno.objects.filter(user=request.user, punto_venta__id=pv_id, fin=None).exists():
                    return redirect("CuentasPuntoVenta")
                
                elif Turno.objects.filter(users_extra=request.user, fin=None).exists():
                    return redirect("CuentasPuntoVenta")
                
                elif Turno.objects.filter(user=request.user, fin=None).exists():

                    turno = Turno.objects.filter(user=request.user, fin=None).first()

                    logout(request)
                    
                    messages.error(request, f"El usuario {turno.user} tiene un turno abierto en {turno.punto_venta.nombre}")
                    return redirect("http://" + str(request.get_host()) + f'/?for={for_open}')
                
                
                elif Turno.objects.filter(punto_venta__id=pv_id, fin=None).exists():
                    logout(request)
                    
                    messages.error(request, "Punto de Venta en funcionamiento, si su intención es entrar como trabajador auxiliar pídale al trabajador principal que le agregue.")
                    return redirect("http://" + str(request.get_host()) + f'/?for={for_open}')
            
                else:
                    return redirect("RecibirTurno", pv_id=pv_id)

        else:messages.error(request, "La contraseña proporcionada no es correcta")

        return redirect("http://" + str(request.get_host()) + f'/?for={for_open}')

class Logout(View):
    def get(self,request,*args,**kwargs):
        logout(request)
        return  redirect(str(request.build_absolute_uri()).replace("logout/",""))#

# -- Administrador
@method_decorator(login_required, name='dispatch')
class GestionTurnosView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        puntos_venta = PuntoVenta.objects.all()
        cocinas = Cocina.objects.filter(activo=True)
        almacenes = Almacen.objects.filter(activo=True)

        cuadre = None
        ventas = None
        salario = None
        notas = None
        recibo_efectivo = None
        elaboraciones = None
        users = None
        users_extra = None
    
        if "inicio" in data.keys() and "fin" in data.keys():
            inicio = datetime.strptime(data["inicio"], '%d/%m/%Y')
            fin = datetime.strptime(data["fin"], '%d/%m/%Y')
        else:
            fin = datetime.now().date()
            inicio = fin - timedelta(days=2)
        

        if "centro_costo" in data.keys() and "C-" in data["centro_costo"]:
            centro_costo = Cocina.objects.get(id=data["centro_costo"].replace("C-",""))
        
            if "analisis" in data.keys() and data["analisis"] != "": analisis = data["analisis"]
            else: analisis = "all"

            turnos = TurnoCosina.objects.filter(
                (Q(inicio__date__range=[inicio, fin]) |
                Q(fin__date__range=[inicio, fin])) &
                Q(cocina=centro_costo)
            ).order_by("-inicio")

            if "opc" in data.keys() and data["opc"] != "": opcion = data["opc"]
            else: opcion = "cuadre"
            

            turno = None
            if "turno-c" in data.keys() and data["turno-c"] != "":
                turno = TurnoCosina.objects.get(id = data["turno-c"])
            elif len(turnos) > 0:
                turno = turnos.first()
            context = {}
            if turno != None:
                if opcion == "cuadre":
                    cuadre = CuadreCocina.objects.filter(turno=turno).order_by("producto__nombre")
                    
                    
                    if "analisis" in data.keys() and data["analisis"] != "": analisis = data["analisis"]
                    else: analisis = "all"

                    if  analisis != "all":
                        try:
                            p = ((turno.costo_ext*100)/turno.costo)/100
                        except:
                            p = 100
                            
                        context["costo_total"] = turno.costo_ext
                        context["monto_total"] = turno.monto * p
                    else:
                        context["costo_total"] = turno.costo
                        context["monto_total"] = turno.monto
                    
                elif opcion == "elaboraciones":
                    if turno.fin:
                        subproductos = StockCocina.objects.filter(consumo__isnull=False,alta__range=[turno.inicio,turno.fin],cocina=turno.cocina).order_by("-alta")
                    else:
                        subproductos = StockCocina.objects.filter(consumo__isnull=False,alta__gte=turno.inicio,cocina=turno.cocina).order_by("-alta")
                    elaboraciones = {
                        "platos":StockProductoCompuestoCocina.objects.filter(turno=turno).order_by("-fecha_fabricacion"),
                        "subproductos": subproductos
                    }

                elif opcion == "notas":
                    notas = NotaCuadreCocina.objects.filter(cuadre__turno = turno)
                elif opcion == "recibo-efectivo":
                    recibo_efectivo = turno
                elif opcion == "salario":
                    salario = turno
                elif opcion == "trab-ayudante":
                    users = centro_costo.users_access.all()
                    users_extra = turno.ayudantes.all()
            else:
                cuadre = []            

            centro_costo_select = f"C-{centro_costo.id}"

            template = "gestion_turnos/gestion_turnos_cocina.html"

        elif "centro_costo" in data.keys() and "A-all" in data["centro_costo"]:
            centro_costo_select = "A-all"
            context = {}
            
            turnos = TurnoAlmacen.objects.filter(
                (Q(inicio__date__range=[inicio, fin]) |
                Q(fin__date__range=[inicio, fin]))
            ).order_by("-inicio")
            
            turno = None
            if "turno-a" in data.keys() and data["turno-a"] != "":
                turno = TurnoAlmacen.objects.get(id = data["turno-a"])
            elif len(turnos) > 0:
                turno = turnos.first()

                
            if "opc" in data.keys() and data["opc"] != "": opcion = data["opc"]
            else: opcion = "entradas"

            if opcion == "entradas":
                entradas = []
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

                entradas_ordenadas = sorted(entradas, key=lambda x: x["fecha"])
                context = {"entradas":entradas_ordenadas}

            elif opcion == "salidas":
                salidas = []
                almacenes = Almacen.objects.filter(activo=True)
                for a in almacenes:
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
                                })
                    
                salidas_ordenadas = sorted(salidas, key=lambda x: x["fecha"])

                context = {"salidas":salidas_ordenadas}

            elif opcion == "notas":
                notas = NotaAlmacen.objects.filter(turno = turno)
                context = {}

            template = "gestion_turnos/gestion_turnos_almacenes.html"
        
        else:
            if "centro_costo" in data.keys() and "PV-" in data["centro_costo"]:
                centro_costo = PuntoVenta.objects.get(id=data["centro_costo"].replace("PV-",""))
            else:
                centro_costo = puntos_venta[0]

        
            if "analisis" in data.keys() and data["analisis"] != "": analisis = data["analisis"]
            else: analisis = "all"

            turnos = Turno.objects.filter(
                (Q(inicio__date__range=[inicio, fin]) |
                Q(fin__date__range=[inicio, fin])) &
                Q(punto_venta=centro_costo)
            ).order_by("-inicio")

            if "opc" in data.keys() and data["opc"] != "": opcion = data["opc"]
            else: opcion = "cuadre"

            turno = None
            if "turno-pv" in data.keys() and data["turno-pv"] != "":
                turno = Turno.objects.get(id = data["turno-pv"])
            elif len(turnos) > 0:
                turno = turnos.first()           
            context = {}
            if turno != None:
                if opcion == "cuadre":
                    cuadre = Cuadre.objects.filter(turno=turno).order_by("producto__nombre")
                    
                    costo_total = 0
                    monto_total = 0

                    if analisis != "all":
                        cuadre_new = []
                        for c in cuadre:
                            if c.recibido_ext > 0 or c.cantidad_insertada_producto_ext() > 0:
                                cuadre_new.append(c)
                                costo_total += c.costo_vendido_ext()
                                monto_total += c.monto_vendido_ext()

                        cuadre = cuadre_new
                    else:
                        for c in cuadre:
                            costo_total += c.costo_vendido()
                            monto_total += c.monto_vendido()

                    context["costo_total"] = costo_total
                    context["monto_total"] = monto_total

                elif opcion == "ventas":
                    ventas = Venta.objects.filter(cuenta__turno = turno).order_by("-instante")
                    if analisis != "all":
                        ventas = ventas.filter(monto_ext__gt = 0)

                elif opcion == "notas":
                    notas = Nota.objects.filter(cuadre__turno = turno)
                elif opcion == "recibo-efectivo":
                    recibo_efectivo = turno
                elif opcion == "salario":
                    salario = turno
                elif opcion == "trab-asociados":
                    users = UserAccount.objects.filter( Q(puntos_venta__id=centro_costo.id) ).exclude(is_active = False)
                    users_extra = turno.users_extra.all()
            else:
                cuadre = []
            

            centro_costo_select = f"PV-{centro_costo.id}"
            
            template = "gestion_turnos/gestion_turnos_pv.html"


        context.update({
            "puntos_venta":puntos_venta,
            "cocinas":cocinas,
            "almacenes":almacenes,
            "turnos":turnos,
            "users":users,
            "users_extra":users_extra,

            "cuadre":cuadre,
            "ventas":ventas,
            "salario":salario,
            "notas":notas,
            "recibo_efectivo":recibo_efectivo,
            "elaboraciones":elaboraciones,

            "inicio":inicio.strftime('%d/%m/%Y'),
            "fin":fin.strftime('%d/%m/%Y'),
            "inicio_url":inicio.strftime('%d/%m/%Y').replace("/","%2F"),
            "fin_url":fin.strftime('%d/%m/%Y').replace("/","%2F"),
            "centro_costo_select":centro_costo_select,
            })
        
        if len(turnos) > 0:
            if turno.fin: context["estado_turno"] = False 
            else:context["estado_turno"] = True
            context["turno_select"]=turno

        return render(request,template,context)

def reabrirTurno(request):
    if request.method == 'POST':
        try:
            turno = Turno.objects.get(id=request.POST["turno-id"])
            turno.pagos.all().delete()
            turno.fin = None
            turno.recibido = None
            turno.monto_caja = None
            turno.monto_maquina = None
            turno.monto_puerta = None
            turno.monto_letra = None
            turno.save()
            re = ReciboEfectivo.objects.get(origen=f"PV-{turno.id}")
            re.delete()
        except:
            pass

        
    #return redirect("GestionTurnos")
    return redirect(str(request.build_absolute_uri()))
     
def restringirVentas(request):
    if not request.user.is_authenticated:
        logout(request)
        return redirect('login')
    
    if request.method == 'POST':
        try:
            turno = Turno.objects.get(id=request.POST["turno-id"])
            if turno.punto_venta.edit_venta:
                turno.punto_venta.edit_venta = False
            else:
                turno.punto_venta.edit_venta = True
            
            turno.punto_venta.save()
        except:
            pass

        
    return redirect("GestionTurnos")

@method_decorator(login_required, name='dispatch')
class AdminAlertasView(View):
    def get(self,request,*args,**kwargs):        
        data = request.GET
        centro_costo = []
        turnos = TurnoAlmacen.objects.filter(fin=None)
        turnos_prev = []
        
        if turnos.exists():
            range_turnos = TurnoAlmacen.objects.all().order_by("-inicio")[1:5]
            for t in range_turnos:
                turnos_prev.append(
                    {
                        "trabajador":t.user.user_str(),
                        "inicio":t.inicio.strftime("%d/%m/%Y %H:%M:%S"),
                        "fin":t.fin.strftime("%d/%m/%Y %H:%M:%S") if t.fin else "En curso",
                        "incidencias":NotaAlmacen.objects.filter(turno = t).count()
                    }
                )
            inicio = turnos.first().inicio.strftime("%d/%m/%Y %H:%M:%S")
            centro_costo.append({
                "centro_costo":"Almaceneres",
                "estado":f"Turno abierto por {turnos.first().user} Inicio: {inicio}",
                "color":"green",
                "turnos":turnos_prev,
            })
        else:
            range_turnos = TurnoAlmacen.objects.all().order_by("-inicio")[:4]
            for t in range_turnos:
                turnos_prev.append(
                    {
                        "trabajador":t.user.user_str(),
                        "inicio":t.inicio.strftime("%d/%m/%Y %H:%M:%S"),
                        "fin":t.fin.strftime("%d/%m/%Y %H:%M:%S") if t.fin else "En curso",
                        "incidencias":NotaAlmacen.objects.filter(turno = t).count()
                    }
                )
            centro_costo.append({
                "centro_costo":"Almaceneres",
                "estado":"Cerrados en estos momentos",
                "color":"red",
                "turnos":turnos_prev,
            })

        puntos_venta = PuntoVenta.objects.filter(activo=True)
        for pv in puntos_venta:
            turnos = Turno.objects.filter(punto_venta=pv,fin=None)
            turnos_prev = []
            if turnos.exists():
                range_turnos = Turno.objects.filter(punto_venta=pv).order_by("-inicio")[1:5]
                for t in range_turnos:
                    turnos_prev.append(
                        {
                            "trabajador":t.user.user_str(),
                            "inicio":t.inicio.strftime("%d/%m/%Y %H:%M:%S"),
                            "fin":t.fin.strftime("%d/%m/%Y %H:%M:%S") if t.fin else "En curso",
                            "incidencias":Nota.objects.filter(cuadre__turno = t).count()
                        }
                    )
                inicio = turnos.first().inicio.strftime("%d/%m/%Y %H:%M:%S")
                centro_costo.append({
                    "centro_costo":pv.nombre,
                    "estado":f"Turno abierto por {turnos.first().user} Inicio: {inicio}",
                    "color":"green",
                    "turnos":turnos_prev,
                })
            else:
                range_turnos = Turno.objects.filter(punto_venta=pv).order_by("-inicio")[:4]
                for t in range_turnos:
                    turnos_prev.append(
                        {
                            "trabajador":t.user.user_str(),
                            "inicio":t.inicio.strftime("%d/%m/%Y %H:%M:%S"),
                            "fin":t.fin.strftime("%d/%m/%Y %H:%M:%S") if t.fin else "En curso",
                            "incidencias":Nota.objects.filter(cuadre__turno = t).count()
                        }
                    )
                centro_costo.append({
                    "centro_costo":pv.nombre,
                    "estado":f"Cerrado en estos momentos",
                    "color":"red",
                    "turnos":turnos_prev,
                })

        cocinas = Cocina.objects.filter(activo=True)
        for c in cocinas:
            turnos = TurnoCosina.objects.filter(cocina=c,fin=None)
            turnos_prev = []
            if turnos.exists():
                range_turnos = TurnoCosina.objects.filter(cocina=c).order_by("-inicio")[1:5]
                for t in range_turnos:
                    turnos_prev.append(
                        {
                            "trabajador":t.user.user_str(),
                            "inicio":t.inicio.strftime("%d/%m/%Y %H:%M:%S"),
                            "fin":t.fin.strftime("%d/%m/%Y %H:%M:%S") if t.fin else "En curso",
                            "incidencias":NotaCuadreCocina.objects.filter(cuadre__turno = t).count()
                        }
                    )
                inicio = turnos.first().inicio.strftime("%d/%m/%Y %H:%M:%S")
                centro_costo.append({
                    "centro_costo":c.nombre,
                    "estado":f"Turno abierto por {turnos.first().user} Inicio: {inicio}",
                    "color":"green",
                    "turnos":turnos_prev,
                })
            else:
                range_turnos = TurnoCosina.objects.filter(cocina=c).order_by("-inicio")[:4]
                for t in range_turnos:
                    turnos_prev.append(
                        {
                            "trabajador":t.user.user_str(),
                            "inicio":t.inicio.strftime("%d/%m/%Y %H:%M:%S"),
                            "fin":t.fin.strftime("%d/%m/%Y %H:%M:%S") if t.fin else "En curso",
                            "incidencias":NotaCuadreCocina.objects.filter(cuadre__turno = t).count()
                        }
                    )
                centro_costo.append({
                    "centro_costo":c.nombre,
                    "estado":f"Cerrada en estos momentos",
                    "color":"red",
                    "turnos":turnos_prev,
                })


        alertas = AlertaAdmin.objects.filter(activo=True).order_by("-fecha")
        return render(request,'alertas.html',{"alertas":alertas,"centros_costo":centro_costo})
    
    def post(self,request,*args,**kwargs):
        data = request.POST
        
        if "alerts-leido" in data:
            for id in list(dict(data)["alerts-leido"]):
                a = AlertaAdmin.objects.get(id=id)
                a.activo = False
                a.save()

        return redirect("AdminAlertas")
        
#- Balancista y Almacenero
@method_decorator(login_required, name='dispatch')
class InformeRecepcionView(View):
    def get(self,request,*args,**kwargs):
        productos_return = Producto.objects.filter(
            activo = True, is_compuesto=False
            ).order_by("nombre")#.exclude(categoria__nombre = "MEDIOS BASICOS")
        
        almacenes = Almacen.objects.filter(activo = True).order_by("nombre")
        max_id = InformeRecepcion.objects.all()
        numero = len(max_id) + 1

        medida = Medida.objects.filter(activo = True)
        categoria = Categoria.objects.filter(activo = True)
        context = {
                    "productos":productos_return,
                    "almacenes":almacenes,
                    "numero":numero,
                    "medidas":medida,
                    "categorias":categoria,
                }

        return render(request,'recepcion/informe.html',context)
    
    def post(self,request,*args,**kwargs):
        data = request.POST
        #print(data)

        if "product-id" in data.keys():
            almacen = Almacen.objects.get(id=data['almacen'])
            informe_recepcion = InformeRecepcion.objects.create(
                almacen = almacen,                
                proveedor = data['suministrador'],
                codigo = data['codigo'],
                factura = data['factura'],
                conduce = data['conduce'],
                contrato = data['contrato'],
                manifiesto = data['manifiesto'],
                partida = data['partida'],
                conoc_embarque = data['embarque'],
                orden_expedicion = data['expedicion'],
                transportador = data['transportador'],
                carne_identidad = data['ci'],
                chapa = data['chapa'],
                numero = data['numero'],
                user_recepcion = request.user.user_str()
            )

            ids = list(dict(data)["product-id"])
            fecha_vencimiento = list(dict(data)["product-vencimiento"])
            cantidades = list(dict(data)["product-cantidad"])
            precios_1 = list(dict(data)["product-precio-1"])
            precios_2 = list(dict(data)["product-precio-2"])

            for index,id in enumerate(ids,start=0):
                precio = float(precios_1[index] + "." + precios_2[index])
                producto = Producto.objects.get(id=int(id))


                StockAlmacen.objects.create(
                    almacen = almacen,
                    producto = producto,
                    lote = datetime.now().strftime('%Y%m%d%H%M%S%f'),
                    cantidad_factura = cantidades[index],
                    vencimiento = fecha_vencimiento[index],
                    costo_cup = precio,
                    informe_recepcion = informe_recepcion
                )
            
            if "gasto-nombre" in data.keys():
                nombres_gastos = list(dict(data)["gasto-nombre"])
                cantidad_gastos = list(dict(data)["gasto-cantidad"])
            else:
                nombres_gastos = []

            for index,nombre in enumerate(nombres_gastos,start=0):
                gasto = GastosRecepcion.objects.create(nombre=nombre,monto=cantidad_gastos[index])
                informe_recepcion.gastos.add(gasto)

            informe_recepcion.save()

        return redirect("InformeRecepcion")

@method_decorator(login_required, name='dispatch')
class ConfirmRecepcionView(View):
    def get(self,request,*args,**kwargs):
        
        informes_recepcion = InformeRecepcion.objects.filter(activo = False).order_by("-fecha")
        context = {"informes_recepcion":informes_recepcion}

        return render(request,'recepcion/confirmacion.html',context)
    
    def post(self,request,*args,**kwargs):
        id_ir = int(request.POST['informe-recepcion-id'])
        ir = InformeRecepcion.objects.get(id = id_ir)

        gastos = ir.monto_gastos()

        almacen = StockAlmacen.objects.filter(informe_recepcion=ir)
        monto_total = 0
        for stock in almacen:
            monto_total += (stock.costo_cup*stock.cantidad_inicial)

        save_ir = False
        for item in almacen:
            if item.cantidad_inicial == 0.0:
                item.delete()
                continue
            existencia = item.existencia_almacen() + item.cantidad_inicial
            save_ir = True

            por_confirmar = StockPuntoVenta.objects.filter(producto=item.producto,transferencia__turno_id = None, transferencia__emisor_id = f"A-{item.almacen.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
            if por_confirmar is not None:
                existencia = existencia + por_confirmar

            por_confirmar = StockCocina.objects.filter(producto=item.producto, transferencia__turno_id = None, transferencia__emisor_id = f"A-{item.almacen.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
            if por_confirmar is not None:
                existencia = existencia + por_confirmar

            por_confirmar = StockAlmacen.objects.filter(producto=item.producto, cantidad_inicial = None, transferencia__emisor_id = f"A-{item.almacen.id}").aggregate(total = Sum("cantidad_factura"))["total"]
            if por_confirmar is not None:
                existencia = existencia + por_confirmar

            por_confirmar = StockUsuario.objects.filter(producto=item.producto,transferencia__turno_id = None, transferencia__emisor_id = f"A-{item.almacen.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
            if por_confirmar is not None:
                existencia = existencia + por_confirmar

            por_confirmar = StockEstudio.objects.filter(producto=item.producto,transferencia__turno_id = None, transferencia__emisor_id = f"A-{item.almacen.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
            if por_confirmar is not None:
                existencia = existencia + por_confirmar

            item.cantidad_actual = item.cantidad_inicial
            item.existencia = existencia
            item.activo = True
            item.gasto = ((item.costo_cup*item.cantidad_inicial*gastos)/monto_total)/item.cantidad_inicial
            item.save()
            
            precio = item.costo_cup
            if StockAlmacen.objects.filter(producto = item.producto).count() > 1:
                stock = StockAlmacen.objects.filter(producto = item.producto).order_by("-alta")[1]
                margen_porciento = round(((precio * 100) / stock.costo_cup) - 100,2)
                margen_dinero = toMoney(precio - stock.costo_cup)

                if margen_porciento > 10 :
                    alert = AlertaAdmin.objects.create(
                        tipo=False,
                        centro_costo = f"A-{item.almacen.id}",
                        motivo = f"Entrada por informe de recepción de {item.producto.nombre} con un costo superior de ${margen_dinero}({margen_porciento}%) respecto a la última compra"
                    )
                    
                    
                    message = f"<b>⚠️ {item.almacen.nombre}</b>\n\n"
                    message += f"Entrada por informe de recepción de {item.producto.nombre} con un costo superior de ${margen_dinero}({margen_porciento}%) respecto a la última compra"
                    
                    t = threading.Thread(target=lambda:send_message(message,alert.id))
                    t.start()

            
            
            if item.producto.precio_venta:

                margen_porciento = round(100 - ((precio * 100) / item.producto.precio_venta),2)
                margen_dinero = toMoney(item.producto.precio_venta - precio)

                if margen_porciento < 30:
                    tipo=False
                    if margen_porciento < 25: tipo = True

                    alert = AlertaAdmin.objects.create(
                        tipo=tipo,
                        centro_costo = f"A-{item.almacen.id}",
                        motivo = f"Entrada por informe de recepción de {item.producto.nombre} con un margen de beneficio de ${margen_dinero}({margen_porciento}%)"
                    )                    
                    
                    message = f"<b>⚠️ {item.almacen.nombre}</b>\n\n"
                    message += f"Entrada por informe de recepción de {item.producto.nombre} con un margen de beneficio de ${margen_dinero}({margen_porciento}%)"
                    
                    t = threading.Thread(target=lambda:send_message(message,alert.id))
                    t.start()

                    

        if save_ir:
            ir.activo = True
            ir.date_confirm = timezone.now()
            ir.user_confirmacion = request.user.user_str()
            ir.save()


            
            caja = Caja.objects.get_or_create(name = "CENTRAL",moneda = "CUP")[0]
            monto_extraido = ir.monto()

            Operaciones.objects.create(
                monto = float(monto_extraido) * -1,
                motivo = f"Monto extraido correspondiente al informe de recpción de fehca {ir.fecha}",
                caja = caja
            )
            messages.success(request, f'Confirme el retiro de ${toMoney(monto_extraido)} de la caja CENTRAL(CUP)')

        else:
            messages.success(request, 'El informe de recepción fue eliminado debido a que la cantidad recepcionada era 0.')
            ir.delete()
        
        return redirect("ConfirmRecepcionView")

@method_decorator(login_required, name='dispatch')
class HistorialRecepcionView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        almacenes = Almacen.objects.filter(activo = True)

        if "inicio" in data.keys() and "fin" in data.keys():
            inicio = datetime.strptime(data["inicio"], '%d/%m/%Y')
            fin = datetime.strptime(data["fin"], '%d/%m/%Y')
        else:
            fin = datetime.now().date()
            inicio = datetime.now().date()


        almacen = None
        if "almacen" in data.keys() and data["almacen"] != "all":
            almacen = Almacen.objects.get(id=data["almacen"])

        informes_recepcion = InformeRecepcion.objects.filter(
            Q(activo = True) & 
            Q(fecha__date__range=[inicio, fin])
            )
        
        if almacen:
            informes_recepcion = informes_recepcion.filter(Q(almacen=almacen))

        informes_recepcion = informes_recepcion.order_by("-fecha")


        context = {
            "informes_recepcion":informes_recepcion,
            "almacenes":almacenes,
            "inicio":inicio.strftime('%d/%m/%Y'),
            "fin":fin.strftime('%d/%m/%Y')
            }
            
        
        if almacen:context["almacen_select"]=almacen
        
        if not request.user.almacen_permission: context["base"] = "base.html"
        else: context["base"] = "almacen/base.html"

        return render(request,'recepcion/historial.html',context)
    
@method_decorator(login_required, name='dispatch')
class RecepcionarStockView(View):
    def get(self,request,*args,**kwargs):
        informes_recepcion = InformeRecepcion.objects.filter(Q(activo = None) | Q(activo = False)).order_by("-fecha")
        context = {"informes_recepcion":informes_recepcion}
           
        if request.user.super_permission: context["base"] = "base.html"
        else: context["base"] = "almacen/base.html"
        return render(request,'almacen/recepcion.html',context)
    
    def post(self,request,*args,**kwargs):
        data = request.POST
        ids = list(dict(data)["almacen-id"])
        cantidades = list(dict(data)["cantidad"])
        ir = InformeRecepcion.objects.get(id=data['informe-recepcion-id'])
        if ir.activo == True:
            messages.error(request, 'No fue posible actualizar la recepción debido a que ya ha sido comfirmado por el balancista.')
            return redirect("RecepcionarStockView")
        
        for index,id in enumerate(ids,start=0):
            item = StockAlmacen.objects.get(id=id)
            if item.activo != True:
                item.cantidad_inicial = cantidades[index]
                item.save()
        
        ir.activo = False
        ir.save()
        
        return redirect("RecepcionarStockView")

@method_decorator(login_required, name='dispatch')
class AlmacenView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET

        puntos_venta = []
        cocinas = []

        almacenes = Almacen.objects.filter(activo = True).order_by("nombre")

        if request.user.super_permission == True:
            puntos_venta = PuntoVenta.objects.filter(activo = True).order_by("nombre")
            cocinas = Cocina.objects.filter(activo = True).order_by("nombre")
        
        if "almacen" in  data.keys():
            almacen_select_get = data["almacen"]
            if "A-" in almacen_select_get:
                id_select = almacen_select_get.replace("A-","")
                almacen = StockAlmacen.objects.filter(almacen__id=id_select,activo=True).exclude(cantidad_actual=0.0).exclude(cantidad_actual=None).order_by("producto__nombre")
                almacen_select = Almacen.objects.get(id = id_select)
                textIndicadorStock = "A"
            elif "PV-" in almacen_select_get :
                id_select = almacen_select_get.replace("PV-","")
                almacen = StockPuntoVenta.objects.filter(punto_venta__id=id_select,activo=True).exclude(cantidad_actual=0.0).exclude(cantidad_actual=None).order_by("producto__nombre")
                almacen_select = PuntoVenta.objects.get(id = id_select)
                textIndicadorStock = "PV"
            elif "C-" in almacen_select_get :
                id_select = almacen_select_get.replace("C-","")
                almacen = StockCocina.objects.filter(cocina__id=id_select,activo=True).exclude(cantidad_actual=0.0).exclude(cantidad_actual=None).order_by("producto__nombre")
                almacen_select = Cocina.objects.get(id = id_select)
                textIndicadorStock = "C"
        else:
            almacen = StockAlmacen.objects.filter(almacen=almacenes[0],activo=True).exclude(cantidad_actual=0.0).exclude(cantidad_actual=None).order_by("producto__nombre")
            almacen_select = almacenes[0]
            textIndicadorStock = "A"
            almacen_select_get = f"A-{almacen_select.id}"

        productos = []

        productos_almacen = []
        almacen_return = []

        monto_total_almacen = 0.0
        monto_base_almacen = 0.0
        monto_total_subproductos = 0.0
        monto_total_mb = 0.0

        for lote in almacen:
            if lote.producto.id not in productos_almacen:
                productos_almacen.append(lote.producto.id)
                p = {"producto":lote.producto,
                    "existencia":lote.cantidad_actual,
                    "transform":FormulaTransformacion.objects.filter(producto_inicial=lote.producto),
                    "lotes":[
                        lote
                    ]
                }
                almacen_return.append(p)
                
                if "A-" in almacen_select_get:
                    if lote.producto.categoria.nombre == "MEDIOS BASICOS":
                        monto_total_mb += (lote.producto.precio_venta * lote.cantidad_actual)
                    elif lote.producto.precio_venta:
                        monto_total_almacen += (lote.producto.precio_venta * lote.cantidad_actual)
                        monto_base_almacen += (lote.costo_cup * lote.cantidad_actual)

                    elif lote.producto.categoria.nombre == "SUBPRODUCTOS":
                        monto_total_subproductos += (lote.costo_cup * lote.cantidad_actual)

                elif "PV-" in almacen_select_get:
                    if lote.producto.precio_venta:
                        monto_total_almacen += (lote.producto.precio_venta * lote.cantidad_actual)
                        monto_base_almacen += (lote.costo_cup() * lote.cantidad_actual)
                    else:
                        monto_total_almacen += (lote.costo_cup() * lote.cantidad_actual)
                        monto_base_almacen += (lote.costo_cup() * lote.cantidad_actual)

            else:
                index = productos_almacen.index(lote.producto.id)
                almacen_return[index]["existencia"] += lote.cantidad_actual
                almacen_return[index]["lotes"].append(lote)
                
                if "A-" in almacen_select_get:
                    if lote.producto.categoria.nombre == "MEDIOS BASICOS":
                        monto_total_mb += (lote.producto.precio_venta * lote.cantidad_actual)
                    elif lote.producto.precio_venta:
                        monto_total_almacen += lote.producto.precio_venta
                        monto_base_almacen += lote.costo_cup

                    elif lote.producto.categoria.nombre == "SUBPRODUCTOS":
                        monto_total_subproductos += (lote.costo_cup * lote.cantidad_actual)

                        
                elif "PV-" in almacen_select_get:
                    if lote.producto.precio_venta:
                        monto_total_almacen += lote.producto.precio_venta
                        monto_base_almacen += lote.costo_cup()
                    else:
                        monto_total_almacen += lote.costo_cup()
                        monto_base_almacen += lote.costo_cup()

        if  "A-" in almacen_select_get:
            for a in almacen_return:
                lotes = a["lotes"]
                ganancia = 0.0
                for l in lotes:
                    ganancia += l.ganancia_porciento()
                
                a["margen_ganancia"] = ganancia/len(lotes)

        elif "PV-" in almacen_select_get:
            for a in almacen_return:
                lotes = a["lotes"]
                ganancia = 0.0
                for l in lotes:
                    ganancia += l.ganancia_porciento()
                
                a["margen_ganancia"] = ganancia/len(lotes)
                

        margen = monto_total_almacen-monto_base_almacen
        try:
            porciento_margen = ((monto_total_almacen-monto_base_almacen) / monto_total_almacen) * 100
        except:
            porciento_margen = 0.0

        #print("Almacen  ",almacen_return)
        

        context = {"almacen":almacen_return,"almacenes":almacenes,"almacen_select":almacen_select,"productos":productos,
                    "monto_total_almacen":round(monto_total_subproductos + monto_total_mb + monto_base_almacen,2),"monto_base_almacen":round(monto_base_almacen,2),
                    "monto_total_subproductos":round(monto_total_subproductos,2),"monto_total_mb":round(monto_total_mb,2),
                    "puntos_venta":puntos_venta,"cocinas":cocinas,"almacen_select_get":almacen_select_get,
                    "margen":round(margen,2),"porciento_margen":round(porciento_margen,2),"textIndicadorStock":textIndicadorStock}


        if not request.user.almacen_permission: context["base"] = "base.html"
        else: context["base"] = "almacen/base.html"

        return render(request,'almacen/almacen.html',context)

    def post(self,request,*args,**kwargs):
        data = request.POST

        cantidad_descontar = float(data["cantidad-convertir"])
        cantidad_final = float(data["cantidad-final"])

        if not cantidad_descontar:
            return redirect(str(request.build_absolute_uri()))

        almacen_select = data["almacen"]
        if "A-" in almacen_select:
            almacen = Almacen.objects.get(id=almacen_select.replace("A-",""))

            formula = FormulaTransformacion.objects.get(id = data["formula"])
            lotes = StockAlmacen.objects.filter(almacen=almacen,cantidad_actual__gt=0,producto = formula.producto_inicial)
            existencia = lotes[0].existencia_almacen()
            
            for lote in lotes:
                if cantidad_descontar == 0: break
                elif cantidad_descontar <= lote.cantidad_actual:
                    lote.cantidad_actual -= cantidad_descontar
                    if lote.cantidad_actual == 0:
                        lote.activo = False
                    lote.save()
                    cantidad_descontar = 0
                else:
                    cantidad_descontar -= lote.cantidad_actual
                    lote.cantidad_actual = 0
                    lote.activo = False
                    lote.save()

            # Esto es para las transferencias de un almacen a otro
            por_confirmar = StockPuntoVenta.objects.filter(producto=formula.producto_inicial,transferencia__turno_id = None, transferencia__emisor_id = f"A-{almacen.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
            if por_confirmar is not None:
                existencia = existencia + por_confirmar

            por_confirmar = StockCocina.objects.filter(producto=formula.producto_inicial, transferencia__turno_id = None, transferencia__emisor_id = f"A-{almacen.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
            if por_confirmar is not None:
                existencia = existencia + por_confirmar

            por_confirmar = StockAlmacen.objects.filter(producto=formula.producto_inicial, cantidad_inicial = None, transferencia__emisor_id = f"A-{almacen.id}").aggregate(total = Sum("cantidad_factura"))["total"]
            if por_confirmar is not None:
                existencia = existencia + por_confirmar

            por_confirmar = StockUsuario.objects.filter(producto=formula.producto_inicial,transferencia__turno_id = None, transferencia__emisor_id = f"A-{almacen.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
            if por_confirmar is not None:
                existencia = existencia + por_confirmar

            por_confirmar = StockEstudio.objects.filter(producto=formula.producto_inicial,transferencia__turno_id = None, transferencia__emisor_id = f"A-{almacen.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
            if por_confirmar is not None:
                existencia = existencia + por_confirmar

            #cant = (float(data["cantidad-convertir"]) * formula.cantidad_final)/formula.cantidad_inicial
            cant = cantidad_final
            new_stock = StockAlmacen.objects.create(
                almacen = almacen,
                producto = formula.producto_final,
                lote = datetime.now().strftime('%Y%m%d%H%M%S%f'),
                cantidad_factura = cant,
                cantidad_inicial = cant,
                cantidad_actual = cant,
                costo_cup = (float(data["cantidad-convertir"]) * lote.costo_cup) / cant,
                transformacion = formula,
                activo = True
            )
            
            existencia_receptor = new_stock.existencia_almacen()

            # Esto es para las transferencias de un almacen a otro
            por_confirmar = StockPuntoVenta.objects.filter(producto=formula.producto_final,transferencia__turno_id = None, transferencia__emisor_id = f"A-{almacen.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
            if por_confirmar is not None:
                existencia_receptor = existencia_receptor + por_confirmar

            por_confirmar = StockCocina.objects.filter(producto=formula.producto_final, transferencia__turno_id = None, transferencia__emisor_id = f"A-{almacen.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
            if por_confirmar is not None:
                existencia_receptor = existencia_receptor + por_confirmar

            por_confirmar = StockAlmacen.objects.filter(producto=formula.producto_final, cantidad_inicial = None, transferencia__emisor_id = f"A-{almacen.id}").aggregate(total = Sum("cantidad_factura"))["total"]
            if por_confirmar is not None:
                existencia_receptor = existencia_receptor + por_confirmar

            new_stock.existencia = existencia  - float(data["cantidad-convertir"])
            new_stock.existencia_receptor = existencia_receptor
            new_stock.save()

        elif "PV-" in almacen_select:
            pv = PuntoVenta.objects.get(id=almacen_select.replace("PV-",""))
            
            formula = FormulaTransformacion.objects.get(id = data["formula"])
            lotes = StockPuntoVenta.objects.filter(punto_venta=pv,cantidad_actual__gt=0,producto = formula.producto_inicial)
            
            last_turno = pv.last_turno()
            if last_turno: last_turno = f"PV-{last_turno.id}"
            registro_trasnformacion = Transformacion.objects.create(
                turno_id = last_turno,
                formula = formula,
            )
            
            for lote in lotes:
                if cantidad_descontar == 0: break
                elif cantidad_descontar <= lote.cantidad_actual:
                    
                    StockPuntoVenta.objects.create(
                        punto_venta = pv,
                        producto = formula.producto_final,
                        costo_produccion = lote.costo_cup(),
                        transformacion = registro_trasnformacion,
                        cantidad_recibida = cantidad_descontar,
                        cantidad_inicial = cantidad_descontar,
                        cantidad_actual = cantidad_descontar,
                        lote_auditable = lote.lote.almacen.is_audit
                    )

                    lote.cantidad_actual -= cantidad_descontar
                    if lote.cantidad_actual == 0:
                        lote.activo = False
                    lote.save()
                    cantidad_descontar = 0
                else:
                    
                    StockPuntoVenta.objects.create(
                        punto_venta = pv,
                        producto = formula.producto_final,
                        costo_produccion = lote.costo_cup(),
                        transformacion = registro_trasnformacion,
                        cantidad_recibida = lote.cantidad_actual,
                        cantidad_inicial = lote.cantidad_actual,
                        cantidad_actual = lote.cantidad_actual,
                        lote_auditable = lote.lote.almacen.is_audit
                    )

                    cantidad_descontar -= lote.cantidad_actual
                    lote.cantidad_actual = 0
                    lote.activo = False
                    lote.save()


            #cant = (float(data["cantidad-convertir"]) * formula.cantidad_final)/formula.cantidad_inicial
            cant = cantidad_final

            
            turno = Turno.objects.filter(punto_venta=pv).order_by("-inicio").first()
            if not Cuadre.objects.filter(turno = turno,producto = formula.producto_final).exists():
                Cuadre.objects.create(
                    turno = turno,
                    producto = formula.producto_final,
                    recibido = 0
                )

        elif "C-" in almacen_select:
            cocina = Cocina.objects.get(id=almacen_select.replace("C-",""))
            
            formula = FormulaTransformacion.objects.get(id = data["formula"])
            lotes = StockCocina.objects.filter(cocina=cocina,cantidad_actual__gt=0,producto = formula.producto_inicial)
            
            for lote in lotes:
                if cantidad_descontar == 0: break
                elif cantidad_descontar <= lote.cantidad_actual:
                    lote.cantidad_actual -= cantidad_descontar
                    if lote.cantidad_actual == 0:
                        lote.activo = False
                    lote.save()
                    cantidad_descontar = 0
                else:
                    cantidad_descontar -= lote.cantidad_actual
                    lote.cantidad_actual = 0
                    lote.activo = False
                    lote.save()


            #cant = (float(data["cantidad-convertir"]) * formula.cantidad_final)/formula.cantidad_inicial
            cant = cantidad_final
            
            last_turno = cocina.last_turno()
            if last_turno: last_turno = f"C-{last_turno.id}"
            registro_trasnformacion = Transformacion.objects.create(
                turno_id = last_turno,
                formula = formula,
            )

            new_stock = StockCocina.objects.create(
                cocina = cocina,
                producto = formula.producto_final,
                costo_produccion = lote.costo_cup(),
                transformacion = registro_trasnformacion,
                cantidad_recibida = cant,
                cantidad_inicial = cant,
                cantidad_actual = cant,
            )
            
            turno = TurnoCosina.objects.filter(cocina=cocina).order_by("-inicio").first()
            if not CuadreCocina.objects.filter(turno = turno,producto = formula.producto_final).exists():
                new_cuadre = CuadreCocina.objects.create(
                    turno = turno,
                    producto = formula.producto_final,
                    recibido = 0
                )

        return redirect(str(request.build_absolute_uri()))

@method_decorator(login_required, name='dispatch')
class TransferenciaSimpleView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        #print(data)
        almacenes = Almacen.objects.filter(activo = True).order_by("nombre")
        puntos_ventas = PuntoVenta.objects.filter(activo = True).order_by("nombre")
        cocinas = Cocina.objects.filter(activo = True).order_by("nombre")
        trabajadores_salon = UserAccount.objects.filter(is_active = True, salon_permission=True).order_by("user")
        trabajadores_office = UserAccount.objects.filter(Q(is_active = True) & (Q(admin_permission=True) | Q(estudio_permission=True))).order_by("user")
        trabajadores_servicios = UserAccount.objects.filter(is_active = True, pago_servicios__isnull=False).order_by("user")
        
        context = {"almacenes":almacenes,"puntos_ventas":puntos_ventas,"cocinas":cocinas,
                   "trabajadores_salon":trabajadores_salon,"trabajadores_office":trabajadores_office,
                   "trabajadores_servicios":trabajadores_servicios}

        if "emisor" in data.keys():
            emisor_id = data["emisor"].split("-")
            if emisor_id[0]  == "PV":
                emisor = PuntoVenta.objects.get(id = emisor_id[1])
            else:
                emisor = Almacen.objects.get(id = emisor_id[1])

            context["emisor"] = emisor
            productos = emisor.productos()
            #print(productos)
        elif len(almacenes) > 0:
            emisor = almacenes[0]
            context["emisor"] = emisor
            productos = emisor.productos()
            
        productos_return = []
        if "receptor" in data.keys():
            receptor_id = data["receptor"].split("-")
            if receptor_id[0]  == "PV":
                receptor = PuntoVenta.objects.get(id = receptor_id[1])

                for producto in productos:                    
                    if producto["categoria"] != "SUBPRODUCTOS" and producto["categoria"] != "ACCESORIOS, PRENDAS Y OTROS" and producto["categoria"] != "SUBPRODUCTOS SALON":
                        productos_return.append(producto)

            elif receptor_id[0]  == "C":
                receptor = Cocina.objects.get(id = receptor_id[1])                

                for producto in productos:
                    if producto["categoria"] == "SUBPRODUCTOS" or  producto["categoria"] == "MEDIOS BASICOS":
                        productos_return.append(producto)

            elif receptor_id[0]  == "U":
                receptor = UserAccount.objects.get(id = receptor_id[1])

                for producto in productos:
                    if producto["categoria"] != "SUBPRODUCTOS" and producto["categoria"] != "ACCESORIOS, PRENDAS Y OTROS":
                        productos_return.append(producto)
                        
            elif receptor_id[0]  == "bolsa":
                receptor = "bolsa-estudio"

                for producto in productos:
                    if producto["categoria"] == "ACCESORIOS, PRENDAS Y OTROS":
                        productos_return.append(producto)

            else:
                receptor = Almacen.objects.get(id = receptor_id[1])
                productos_return = productos
            #print(productos)

            context["receptor"] = receptor
            
        elif len(almacenes) > 0:
            receptor = almacenes[0]
            context["receptor"] = receptor
            productos_return = productos
        
        context["productos"] = productos_return
        if request.user.super_permission: context["base"] = "base.html"
        else: context["base"] = "almacen/base.html" 

        return render(request,'almacen/transferencia_simple.html',context)
    
    def post(self,request,*args,**kwargs):
        data = request.POST
        #print(data)
        emisor = data['emisor']
        receptor = data['receptor']
        
        if emisor == receptor:
            messages.error(request,"Seleccione un receptor diferente")
            return redirect(str(request.build_absolute_uri()))

        entrega = data['nombre_entrega']
        recibe = data['nombre_recibe']
        autoriza = data['nombre_autoriza']

        if "productos-ids" not in data.keys():
            messages.error(request,"Debe seleccionar los productos a transferir")
            return redirect("TransferenciaSimple")
            
        productos_ids = list(dict(data)["productos-ids"])
        #print(productos_ids)
        lotes_ids = list(dict(data)["lote-id"])
        #print(lotes_ids)
        cantidades = list(dict(data)["cantidad"])
        #print(cantidades)

        transferencia = Transferencia.objects.create(
            emisor_id = emisor,
            receptor_id = receptor,
            entrega = entrega,
            recibe = recibe,
            autoriza = autoriza,
            user_transfiere = request.user.user_str()
        )
        
        success = False
        if "A-" in emisor:
            almacen_id = int(emisor.replace("A-",""))
            if "PV-" in receptor:
                punto_venta = PuntoVenta.objects.get(id = receptor.replace("PV-",""))
                for index,id in enumerate(productos_ids,start=0):
                    if float(cantidades[index]) > 0.0:
                    # Aqui se ordena el stock del almacen por lotes para a la hora de transferir rebaje del producto mas antiguo o por fecha de vencimiento
                        lotes = StockAlmacen.objects.filter(almacen__id=almacen_id,cantidad_actual__gt=0,producto__id = id).order_by("lote")
                        #lotes = StockAlmacen.objects.filter(almacen__id=almacen_id,cantidad_actual__gt=0,producto__id = id).order_by("vencimiento")                         
                        cantidad_descontar = float(cantidades[index])                        
                        existencia = lotes.first().producto.existencia(almacen_id)                        

                        for lote in lotes:                            
                            #if cantidad_descontar == 0:                                 
                            #    break
                            if cantidad_descontar <= lote.cantidad_actual:
                                cantidad = cantidad_descontar
                                lote.cantidad_actual -= cantidad_descontar
                                if lote.cantidad_actual == 0:
                                    lote.activo = False
                                lote.existencia = lote.cantidad_actual
                                lote.save()
                                cantidad_descontar = 0                                
                                StockPuntoVenta.objects.create(
                                    punto_venta =punto_venta,
                                    producto = lote.producto,                                    
                                    lote = lote,
                                    transferencia = transferencia,
                                    lote_auditable = lote.almacen.is_audit,
                                    cantidad_remitida = cantidad,
                                )
                                break 
                            else:
                                cantidad_descontar -= lote.cantidad_actual
                                cantidad = lote.cantidad_actual
                                lote.cantidad_actual = 0
                                lote.existencia = lote.cantidad_actual
                                lote.activo = False
                                lote.save() 
                                #print(cantidad)
                                StockPuntoVenta.objects.create(
                                    punto_venta =punto_venta,
                                    producto = lote.producto,                                    
                                    lote = lote,
                                    transferencia = transferencia,
                                    lote_auditable = lote.almacen.is_audit,
                                    cantidad_remitida = cantidad,
                                )                    
                        
                        success = True

            elif "C-" in receptor and "A-" in emisor:

                cocina = Cocina.objects.get(id = receptor.replace("C-",""))
                for index,id in enumerate(productos_ids,start=0):
                    if float(cantidades[index]) > 0.0:
                         # Aqui se ordena el stock del almacen por lotes para a la hora de transferir rebaje del producto mas antiguo o por fecha de vencimiento
                        lotes = StockAlmacen.objects.filter(almacen__id=almacen_id,cantidad_actual__gt=0,producto__id = id).order_by("lote")
                        #lotes = StockAlmacen.objects.filter(almacen__id=almacen_id,cantidad_actual__gt=0,producto__id = id).order_by("vencimiento")                         
                        cantidad_descontar = float(cantidades[index])                        
                        existencia = lotes.first().producto.existencia(almacen_id)                        

                        for lote in lotes:                            
                            #if cantidad_descontar == 0:                                 
                            #    break
                            if cantidad_descontar <= lote.cantidad_actual:
                                cantidad = cantidad_descontar
                                lote.cantidad_actual -= cantidad_descontar
                                if lote.cantidad_actual == 0:
                                    lote.activo = False
                                lote.existencia = lote.cantidad_actual
                                lote.save()
                                cantidad_descontar = 0                                
                                StockCocina.objects.create(
                                    cocina =cocina,
                                    producto = lote.producto,                                    
                                    lote = lote,
                                    transferencia = transferencia,                                    
                                    cantidad_remitida = cantidad,
                                )
                                break 
                            else:
                                cantidad_descontar -= lote.cantidad_actual
                                cantidad = lote.cantidad_actual
                                lote.cantidad_actual = 0
                                lote.existencia = lote.cantidad_actual
                                lote.activo = False
                                lote.save() 
                                #print(cantidad)
                                StockCocina.objects.create(
                                    cocina =cocina,
                                    producto = lote.producto,                                    
                                    lote = lote,
                                    transferencia = transferencia,                                    
                                    cantidad_remitida = cantidad,
                                )                    
                        
                        success = True               
            
            elif "A-" in receptor:
                for index,id in enumerate(productos_ids,start=0):
                    if float(cantidades[index]) > 0.0:
                        lote = StockAlmacen.objects.get(id=lotes_ids[index])
                        
                        lotes = StockAlmacen.objects.filter(almacen__id=almacen_id,cantidad_actual__gt=0,producto__id = id).order_by("lote")
                        cantidad_descontar = float(cantidades[index])
                        existencia = lotes.first().producto.existencia(almacen_id)
                        
                        for lote in lotes:
                            if cantidad_descontar == 0: break
                            elif cantidad_descontar <= lote.cantidad_actual:
                                lote.cantidad_actual -= cantidad_descontar
                                if lote.cantidad_actual == 0:
                                    lote.activo = False
                                lote.save()
                                cantidad_descontar = 0
                            else:
                                cantidad_descontar -= lote.cantidad_actual
                                lote.cantidad_actual = 0
                                lote.activo = False
                                lote.save()

                        almacen_receptor = Almacen.objects.get(id=receptor.replace("A-",""))
                        existencia_receptor = lote.producto.existencia(almacen_id=receptor.replace("A-",""))

                        StockAlmacen.objects.create(
                            almacen = almacen_receptor,
                            producto = lote.producto,
                            existencia = existencia_receptor + float(cantidades[index]),
                            lote = lote.lote,#datetime.now().strftime('%Y%m%d%H%M%S%f'),
                            cantidad_factura = float(cantidades[index]),
                            cantidad_inicial = float(cantidades[index]),
                            cantidad_actual = float(cantidades[index]),
                            costo_cup = lote.costo_cup,
                            transferencia = transferencia,
                            activo = True
                        )
                        success = True

            elif "U-" in receptor:
                for index,id in enumerate(productos_ids,start=0):
                    if float(cantidades[index]) > 0.0:
                        lotes = StockAlmacen.objects.filter(almacen__id=almacen_id,cantidad_actual__gt=0,producto__id = id).order_by("lote")
                        cantidad_descontar = float(cantidades[index])
                        existencia = lotes.first().producto.existencia(almacen_id)
                        
                        for lote in lotes:
                            if cantidad_descontar == 0: break
                            elif cantidad_descontar <= lote.cantidad_actual:
                                lote.cantidad_actual -= cantidad_descontar
                                if lote.cantidad_actual == 0:
                                    lote.activo = False
                                lote.save()
                                cantidad_descontar = 0
                            else:
                                cantidad_descontar -= lote.cantidad_actual
                                lote.cantidad_actual = 0
                                lote.activo = False
                                lote.save()


                        u = UserAccount.objects.get(id = receptor.replace("U-",""))
                        StockUsuario.objects.create(
                            user = u,
                            producto = lote.producto,
                            lote = lote,
                            lote_auditable = lote.almacen.is_audit,
                            transferencia = transferencia,                          
                            cantidad_remitida = cantidades[index]
                        )
                        success = True
            
            elif "bolsa-estudio" in receptor:
                
                for index,id in enumerate(productos_ids,start=0):
                    if float(cantidades[index]) > 0.0:
                        lotes = StockAlmacen.objects.filter(almacen__id=almacen_id,cantidad_actual__gt=0,producto__id = id).order_by("lote")
                        cantidad_descontar = float(cantidades[index])                        
                        for lote in lotes:
                            if cantidad_descontar == 0: break
                            elif cantidad_descontar <= lote.cantidad_actual:
                                lote.cantidad_actual -= cantidad_descontar
                                if lote.cantidad_actual == 0:
                                    lote.activo = False
                                lote.save()
                                cantidad_descontar = 0
                            else:
                                cantidad_descontar -= lote.cantidad_actual
                                lote.cantidad_actual = 0
                                lote.activo = False
                                lote.save()

                        StockEstudio.objects.create(
                            producto = lote.producto,
                            costo = lote.costo_cup,
                            deuda = lote.costo_cup,
                            cantidad_remitida = cantidades[index],
                            transferencia=transferencia
                        )
                        success = True

        if "PV-" in emisor:
            almacen_id = int(emisor.replace("PV-",""))
            if "A-" in receptor:
                for index,id in enumerate(productos_ids,start=0):
                    if float(cantidades[index]) > 0.0:
                        lote = StockPuntoVenta.objects.get(id=lotes_ids[index])
                        
                        lotes = StockPuntoVenta.objects.filter(almacen__id=almacen_id,cantidad_actual__gt=0,producto__id = id).order_by("lote")
                        cantidad_descontar = float(cantidades[index])
                        existencia = lotes.first().producto.existencia(almacen_id)
                        
                        for lote in lotes:
                            if cantidad_descontar == 0: break
                            elif cantidad_descontar <= lote.cantidad_actual:
                                lote.cantidad_actual -= cantidad_descontar
                                if lote.cantidad_actual == 0:
                                    lote.activo = False
                                lote.save()
                                cantidad_descontar = 0
                            else:
                                cantidad_descontar -= lote.cantidad_actual
                                lote.cantidad_actual = 0
                                lote.activo = False
                                lote.save()

                        almacen_receptor = Almacen.objects.get(id=receptor.replace("A-",""))
                        existencia_receptor = lote.producto.existencia(almacen_id=receptor.replace("A-",""))

                        StockAlmacen.objects.create(
                            almacen = almacen_receptor,
                            producto = lote.producto,
                            existencia = existencia_receptor + float(cantidades[index]),
                            lote = lote.lote,#datetime.now().strftime('%Y%m%d%H%M%S%f'),
                            cantidad_factura = float(cantidades[index]),
                            cantidad_inicial = float(cantidades[index]),
                            cantidad_actual = float(cantidades[index]),
                            costo_cup = lote.costo_cup,
                            transferencia = transferencia,
                            activo = True
                        )
                        success = True
  


        if success == False:
            transferencia.delete()

        return redirect(str(request.build_absolute_uri()))
   
@method_decorator(login_required, name='dispatch')
class TransferenciaCompuestaView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        almacenes = Almacen.objects.filter(activo = True).order_by("nombre")
        puntos_ventas = PuntoVenta.objects.filter(activo = True).order_by("nombre")
        cocinas = Cocina.objects.filter(activo = True).order_by("nombre")
        
        context = {"almacenes":almacenes,"puntos_ventas":puntos_ventas,"cocinas":cocinas}

        if "emisor" in data.keys():
            emisor_id = data["emisor"].split("-")
            emisor = Almacen.objects.get(id = emisor_id[1])
            context["emisor"] = emisor

        elif len(almacenes) > 0:
            emisor = almacenes[0]
            context["emisor"] = emisor
        

        context["formulas"] = Formula.objects.filter(Q(producto__nombre__contains="KIT DE") |Q(producto__nombre__contains="(DULCERIA)"),activo=True).order_by("producto__nombre")

        if "formula-id" in data.keys():

            cantidad = float(data["cantidad"])
            context["cantidad"] = cantidad

            formula = Formula.objects.get(id=data["formula-id"])
            #formula.disponible = formula.disponibilidad_almacen(emisor.id) * formula.cantidad

            subproductos_existentes = []
            subproductos_faltantes = []
            
            subproductos = formula.subproducto.all().order_by("producto__nombre")

            for subproducto in subproductos:
                lote_asignar = subproducto.producto.lote_asignar(almacen_id=emisor.id)
                if lote_asignar:
                    subproducto.costo_cup = lote_asignar.costo_cup
                else:
                    subproducto.costo_cup = 0.0

                existencia = subproducto.producto.existencia(almacen_id=emisor.id)
                subproducto.existencia = existencia
                subproducto.cant_kit = (subproducto.cantidad * cantidad)/formula.cantidad
                       
                
                if existencia >= subproducto.cant_kit:
                    subproductos_existentes.append(subproducto)
                else:
                    subproductos_faltantes.append(subproducto)

            formula.subproductos = subproductos
            
            """if formula in formulas and formula.disponible >= 0: 
                context["formula"] = formula"""
            
            context["formula"] = formula
            context["subproductos_faltantes"] = subproductos_faltantes            
            context["subproductos_existentes"] = subproductos_existentes

        if request.user.super_permission: context["base"] = "base.html"
        else: context["base"] = "almacen/base.html"

        return render(request,'almacen/transferencia_compuesta.html',context)
    
    def post(self,request,*args,**kwargs):
        data = request.POST
        emisor = data['emisor']
        receptor = data['receptor']

        entrega = data['nombre_entrega']
        recibe = data['nombre_recibe']
        autoriza = data['nombre_autoriza']
        
        subproductos_transferir = []

        for k in data.keys():
            if "subproducto-transferir" in k:
                subproductos_transferir.append(data[k])
        
        if len(subproductos_transferir) > 0:
            cantidad = float(data["cantidad"])

            transferencia = Transferencia.objects.create(
                emisor_id = emisor,
                receptor_id = receptor,
                entrega = entrega,
                recibe = recibe,
                autoriza = autoriza,
                cant_elaborar = cantidad,
                user_transfiere = request.user.user_str()
            )
            
            formula = Formula.objects.get(id=data["formula-id"])
            subproductos = formula.subproducto.all()

            almacen_id = int(emisor.replace("A-",""))

            cocina = Cocina.objects.get(id = receptor.replace("C-",""))
            for subproducto in subproductos:
                if str(subproducto.id) in subproductos_transferir:
                    lotes = StockAlmacen.objects.filter(almacen__id=almacen_id,cantidad_actual__gt=0,producto = subproducto.producto).order_by("lote")
                    cantidad_descontar = (cantidad * subproducto.cantidad)/formula.cantidad  
                    cantidad_remitida = cantidad_descontar        

                    for lote in lotes:                            
                            #if cantidad_descontar == 0:                                 
                            #    break
                            if cantidad_descontar <= lote.cantidad_actual:
                                cantidad_prod = cantidad_descontar
                                lote.cantidad_actual -= cantidad_descontar
                                if lote.cantidad_actual == 0:
                                    lote.activo = False
                                lote.existencia = lote.cantidad_actual
                                lote.save()
                                cantidad_descontar = 0                        

                                StockCocina.objects.create(
                                    cocina =cocina,
                                    producto = lote.producto,                                    
                                    lote = lote,
                                    transferencia = transferencia,                                    
                                    cantidad_remitida = cantidad_remitida,
                                    objetivo = formula
                                )
                                break 
                            else:
                                cantidad_descontar -= lote.cantidad_actual
                                cantidad_prod = lote.cantidad_actual
                                lote.cantidad_actual = 0
                                lote.existencia = lote.cantidad_actual
                                lote.activo = False
                                lote.save() 
                                
                                StockCocina.objects.create(
                                    cocina =cocina,
                                    producto = lote.producto,                                    
                                    lote = lote,
                                    transferencia = transferencia,                                    
                                    cantidad_remitida = cantidad_remitida,
                                    objetivo = formula
                                )   

        
            messages.success(request, f"Se transfirió exitosamente un kit para elaborar {cantidad} {formula.producto.nombre}")

        else:
            messages.error(request, "Debe seleccionar los productos transferidos para la elaboracn.")

        return redirect(str(request.build_absolute_uri()))

@method_decorator(login_required, name='dispatch')
class TransferenciaPedidosView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        almacenes = Almacen.objects.filter(activo = True).order_by("nombre")
        puntos_ventas = PuntoVenta.objects.filter(activo = True).order_by("nombre")
        cocinas = Cocina.objects.filter(activo = True).order_by("nombre")
        
        context = {"almacenes":almacenes,"puntos_ventas":puntos_ventas,"cocinas":cocinas}

        if "emisor" in data.keys():
            emisor_id = data["emisor"].split("-")
            if emisor_id[0]  == "PV":
                emisor = PuntoVenta.objects.get(id = emisor_id[1])
            else:
                emisor = Almacen.objects.get(id = emisor_id[1])

            context["emisor"] = emisor
            productos = emisor.productos()
        elif len(almacenes) > 0:
            emisor = almacenes[0]
            context["emisor"] = emisor
            productos = emisor.productos()
            
        productos_return = []
        if "receptor" in data.keys():
            receptor_id = data["receptor"].split("-")

            if receptor_id[0]  == "PV":
                receptor = PuntoVenta.objects.get(id = receptor_id[1])

                for producto in productos:
                    if producto["categoria"] != "SUBPRODUCTOS" and producto["categoria"] != "ACCESORIOS, PRENDAS Y OTROS" and producto["categoria"] != "SUBPRODUCTOS SALON"  and  producto["categoria"] != "MEDIOS BASICOS":
                        
                        cantidad_solicitud, ipv = Producto.objects.get(
                            id = producto["id"]
                        ).get_cantidad_solicitud(receptor.id)
                        producto["cantidad_solicitud"] = cantidad_solicitud
                        producto["ipv"] = ipv
                        producto["existencia_actual"] = producto["existencia"] - producto["cantidad_solicitud"]
                        productos_return.append(producto)

            elif receptor_id[0]  == "C":
                receptor = Cocina.objects.get(id = receptor_id[1])                

                for producto in productos:
                    if producto["categoria"] == "SUBPRODUCTOS":
                        
                        cantidad_solicitud, ipv = Producto.objects.get(
                            id = producto["id"]
                        ).get_cantidad_solicitud(f"C-{receptor.id}")
                        
                        producto["cantidad_solicitud"] = cantidad_solicitud
                        producto["ipv"] = ipv
                        producto["existencia_actual"] = producto["existencia"] - producto["cantidad_solicitud"]

                        productos_return.append(producto)

            context["receptor"] = receptor
                    
        context["productos"] =  sorted(productos_return, key=lambda x: x['cantidad_solicitud'],reverse=True)
        if request.user.super_permission: context["base"] = "base.html"
        else: context["base"] = "almacen/base.html" 

        return render(request,'almacen/transferencia_pedidos.html',context)
    
    def post(self,request,*args,**kwargs):
        data = request.POST

        emisor = data['emisor']
        receptor = data['receptor']
        
        if emisor == receptor:
            messages.error(request,"Seleccione un receptor diferente")
            return redirect(str(request.build_absolute_uri()))

        entrega = data['nombre_entrega']
        recibe = data['nombre_recibe']
        autoriza = data['nombre_autoriza']

        if "productos-ids" not in data.keys():
            messages.error(request,"Debe seleccionar los productos a transferir")
            return redirect("TransferenciaSimple")
            
        productos_ids = list(dict(data)["productos-ids"])
        lotes_ids = list(dict(data)["lote-id"])
        cantidades = list(dict(data)["cantidad"])

        transferencia = Transferencia.objects.create(
            emisor_id = emisor,
            receptor_id = receptor,
            entrega = entrega,
            recibe = recibe,
            autoriza = autoriza,
            user_transfiere = request.user.user_str()
        )
        
        success = False
        if "A-" in emisor:
            almacen_id = int(emisor.replace("A-",""))
            if "PV-" in receptor:
                for index,id in enumerate(productos_ids,start=0):
                    if float(cantidades[index]) > 0.0:
                        lotes = StockAlmacen.objects.filter(almacen__id=almacen_id,cantidad_actual__gt=0,producto__id = id).order_by("lote")
                        cantidad_descontar = float(cantidades[index])
                        existencia = lotes.first().producto.existencia(almacen_id)
                        
                        for lote in lotes:
                            if cantidad_descontar == 0: break
                            elif cantidad_descontar <= lote.cantidad_actual:
                                lote.cantidad_actual -= cantidad_descontar
                                if lote.cantidad_actual == 0:
                                    lote.activo = False
                                lote.save()
                                cantidad_descontar = 0
                            else:
                                cantidad_descontar -= lote.cantidad_actual
                                lote.cantidad_actual = 0
                                lote.activo = False
                                lote.save()


                        punto_venta = PuntoVenta.objects.get(id = receptor.replace("PV-",""))
                        StockPuntoVenta.objects.create(
                            punto_venta =punto_venta,
                            producto = lote.producto,
                            lote = lote,
                            transferencia = transferencia,
                            lote_auditable = lote.almacen.is_audit,
                            cantidad_remitida = cantidades[index],
                        )
                        success = True

            elif "C-" in receptor and "A-" in emisor:
                for index,id in enumerate(productos_ids,start=0):
                    if float(cantidades[index]) > 0.0:
                        lotes = StockAlmacen.objects.filter(almacen__id=almacen_id,cantidad_actual__gt=0,producto__id = id).order_by("lote")
                        cantidad_descontar = float(cantidades[index])
                        existencia = lotes.first().producto.existencia(almacen_id)
                        
                        for lote in lotes:
                            if cantidad_descontar == 0: break
                            elif cantidad_descontar <= lote.cantidad_actual:
                                lote.cantidad_actual -= cantidad_descontar
                                if lote.cantidad_actual == 0:
                                    lote.activo = False
                                lote.save()
                                cantidad_descontar = 0
                            else:
                                cantidad_descontar -= lote.cantidad_actual
                                lote.cantidad_actual = 0
                                lote.activo = False
                                lote.save()


                        cocina = Cocina.objects.get(id = receptor.replace("C-",""))
                        StockCocina.objects.create(
                            cocina =cocina,
                            producto = lote.producto,
                            lote = lote,
                            transferencia = transferencia,
                            existencia = existencia,
                            cantidad_remitida = cantidades[index],
                        )
                        success = True
            
        if success == False:
            transferencia.delete()

        return redirect(str(request.build_absolute_uri()))
  
@method_decorator(login_required, name='dispatch')
class HistorialTransferenciasView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET

        if "inicio" in data.keys() and "fin" in data.keys():
            inicio = datetime.strptime(data["inicio"], '%d/%m/%Y')
            fin = datetime.strptime(data["fin"], '%d/%m/%Y')
        else:
            fin = datetime.now().date()
            inicio = datetime.now().date()

        almacenes_origenes = Almacen.objects.filter(activo = True)
        if "almacen" in data.keys():
            almacen = data['almacen']
        else:
            almacen = almacenes_origenes.first()
            if almacen != None: almacen= f"A-{almacen.id}"
        

        if "operacion" not in data.keys() or  data["operacion"] == "post": 
            transferencias = Transferencia.objects.filter(
                Q(activo = True) & 
                Q(alta__date__range=[inicio, fin]) &
                Q(emisor_id=almacen))

        elif data["operacion"] == "get": 
            transferencias = Transferencia.objects.filter(
                Q(activo = True) & 
                Q(alta__date__range=[inicio, fin]) &
                Q(mensaje_cancelacion__isnull = True) & 
                Q(receptor_id=almacen))

        if request.user.balanc_permission:transferencias = transferencias.exclude(date_confirm=None)
        transferencias = transferencias.order_by("-alta")

        for transferencia in transferencias:
            emisor = transferencia.emisor()
            if isinstance(emisor, str):
                transferencia.emisor_cosina = Cocina.objects.get(id=emisor.replace("C-",""))

        context = {
            "almacenes_origenes":almacenes_origenes,
            "transferencias":transferencias,
            "inicio":inicio.strftime('%d/%m/%Y'),
            "fin":fin.strftime('%d/%m/%Y')
            }
            
        if "almacen" in data.keys(): context["almacen"]=int(almacen.replace("A-",""))
        if ("operacion" in data.keys() and data["operacion"] == "post") or "operacion" not in data.keys(): context["operacion"] = "post"
        else:context["operacion"] = "get"

        if not request.user.almacen_permission: context["base"] = "base.html"
        else: context["base"] = "almacen/base.html"

        return render(request,'almacen/historial_transferencias.html',context)
    
    def post(self,request,*args,**kwargs):
        data_get = request.GET
        data = request.POST
        cantidades = list(dict(data)["cantidad"])
        transferencia_id = data["transferencia-id"]

        transferencia = Transferencia.objects.get(id = transferencia_id)
        transferencia.mensaje_cancelacion = None
        transferencia.save()

        almacen_id = transferencia.emisor_id.replace("A-","") 
        receptor = transferencia.receptor_id
        emisor = transferencia.emisor_id
        productos_ids = []

        if ("operacion" in data_get.keys() and data_get["operacion"] == "get") or "operacion" not in data_get.keys():
            if "PV-" in transferencia.receptor_id:
                stock_transferencia = StockPuntoVenta.objects.filter(transferencia = transferencia)
                for s in stock_transferencia:
                    s.existencia = s.existencia_almacen_emisor()
                    
                    por_confirmar = StockPuntoVenta.objects.filter(producto=s.producto,transferencia__turno_id = None, transferencia__emisor_id = transferencia.emisor_id).aggregate(total = Sum("cantidad_remitida"))["total"]
                    if por_confirmar is not None:
                        existencia = existencia + por_confirmar

                    por_confirmar = StockCocina.objects.filter(producto=s.producto, transferencia__turno_id = None, transferencia__emisor_id = transferencia.emisor_id).aggregate(total = Sum("cantidad_remitida"))["total"]
                    if por_confirmar is not None:
                        existencia = existencia + por_confirmar

                    por_confirmar = StockAlmacen.objects.filter(producto=s.producto, cantidad_inicial = None, transferencia__emisor_id = transferencia.emisor_id).aggregate(total = Sum("cantidad_factura"))["total"]
                    if por_confirmar is not None:
                        existencia = existencia + por_confirmar

                    por_confirmar = StockUsuario.objects.filter(producto=s.producto,transferencia__turno_id = None, transferencia__emisor_id = transferencia.emisor_id).aggregate(total = Sum("cantidad_remitida"))["total"]
                    if por_confirmar is not None:
                        existencia = existencia + por_confirmar

                    por_confirmar = StockEstudio.objects.filter(producto=s.producto,transferencia__turno_id = None, transferencia__emisor_id = transferencia.emisor_id).aggregate(total = Sum("cantidad_remitida"))["total"]
                    if por_confirmar is not None:
                        existencia = existencia + por_confirmar

                    s.existencia = existencia - float(s.cantidad_remitida)
                    s.cantidad_recibida = s.cantidad_remitida
                    s.cantidad_inicial = s.cantidad_remitida
                    s.cantidad_actual = s.cantidad_remitida
                    s.activo = True
                    s.save()

                    transferencia.date_confirm = timezone.now()
                    transferencia.user_confirmacion = request.user.user_str()
                    transferencia.save()

            elif "A-" in transferencia.receptor_id and "A-" in transferencia.emisor_id:
                stock_transferencia = StockAlmacen.objects.filter(transferencia = transferencia)
                for s in stock_transferencia:

                    almacen_receptor = Almacen.objects.get(id=receptor.replace("A-",""))
                    existencia_receptor = s.existencia_almacen()

                    # Esto es para las transferencias de un almacen a otro
                    por_confirmar = StockPuntoVenta.objects.filter(producto=s.producto,transferencia__turno_id = None, transferencia__emisor_id = f"A-{almacen_receptor.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
                    if por_confirmar is not None:
                        existencia_receptor = existencia_receptor + por_confirmar

                    por_confirmar = StockCocina.objects.filter(producto=s.producto, transferencia__turno_id = None, transferencia__emisor_id = f"A-{almacen_receptor.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
                    if por_confirmar is not None:
                        existencia_receptor = existencia_receptor + por_confirmar

                    por_confirmar = StockAlmacen.objects.filter(producto=s.producto, cantidad_inicial = None, transferencia__emisor_id = f"A-{almacen_receptor.id}").aggregate(total = Sum("cantidad_factura"))["total"]
                    if por_confirmar is not None:
                        existencia_receptor = existencia_receptor + por_confirmar

                    por_confirmar = StockUsuario.objects.filter(producto=s.producto,transferencia__turno_id = None, transferencia__emisor_id = f"A-{almacen_receptor.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
                    if por_confirmar is not None:
                        existencia = existencia + por_confirmar

                    por_confirmar = StockEstudio.objects.filter(producto=s.producto,transferencia__turno_id = None, transferencia__emisor_id = f"A-{almacen_receptor.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
                    if por_confirmar is not None:
                        existencia = existencia + por_confirmar


                    s.existencia_receptor = existencia_receptor + float(s.cantidad_factura)


                    almacen_emisor = Almacen.objects.get(id=emisor.replace("A-",""))
                    existencia = s.existencia_almacen_emisor()
                    
                    por_confirmar = StockPuntoVenta.objects.filter(producto=s.producto,transferencia__turno_id = None, transferencia__emisor_id = f"A-{almacen_emisor.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
                    if por_confirmar is not None:
                        existencia = existencia + por_confirmar

                    por_confirmar = StockCocina.objects.filter(producto=s.producto, transferencia__turno_id = None, transferencia__emisor_id = f"A-{almacen_emisor.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
                    if por_confirmar is not None:
                        existencia = existencia + por_confirmar

                    por_confirmar = StockAlmacen.objects.filter(producto=s.producto, cantidad_inicial = None, transferencia__emisor_id = f"A-{almacen_emisor.id}").aggregate(total = Sum("cantidad_factura"))["total"]
                    if por_confirmar is not None:
                        existencia = existencia + por_confirmar

                    por_confirmar = StockUsuario.objects.filter(producto=s.producto,transferencia__turno_id = None, transferencia__emisor_id = f"A-{almacen_emisor.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
                    if por_confirmar is not None:
                        existencia = existencia + por_confirmar

                    por_confirmar = StockEstudio.objects.filter(producto=s.producto,transferencia__turno_id = None, transferencia__emisor_id = f"A-{s.almacen.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
                    if por_confirmar is not None:
                        existencia = existencia + por_confirmar


                    s.existencia = existencia - float(s.cantidad_factura)

                    s.cantidad_inicial = s.cantidad_factura
                    s.cantidad_actual = s.cantidad_factura

                    
                    s.activo = True
                    s.save()

                    transferencia.date_confirm = timezone.now()
                    transferencia.user_confirmacion = request.user.user_str()
                    transferencia.save()

            elif "A-" in transferencia.receptor_id and "C-" in transferencia.emisor_id:
                stock_transferencia = StockAlmacen.objects.filter(transferencia = transferencia)

                for s in stock_transferencia:
                    almacen_receptor = Almacen.objects.get(id=receptor.replace("A-",""))
                    existencia_receptor = s.existencia_almacen()

                    # Esto es para las transferencias de un almacen a otro
                    por_confirmar = StockPuntoVenta.objects.filter(producto=s.producto,transferencia__turno_id = None, transferencia__emisor_id = f"A-{almacen_receptor.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
                    if por_confirmar is not None:
                        existencia_receptor = existencia_receptor + por_confirmar

                    por_confirmar = StockCocina.objects.filter(producto=s.producto, transferencia__turno_id = None, transferencia__emisor_id = f"A-{almacen_receptor.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
                    if por_confirmar is not None:
                        existencia_receptor = existencia_receptor + por_confirmar

                    por_confirmar = StockAlmacen.objects.filter(producto=s.producto, cantidad_inicial = None, transferencia__emisor_id = f"A-{almacen_receptor.id}").aggregate(total = Sum("cantidad_factura"))["total"]
                    if por_confirmar is not None:
                        existencia_receptor = existencia_receptor + por_confirmar

                    s.existencia_receptor = existencia_receptor + float(s.cantidad_factura)


                    s.cantidad_inicial = s.cantidad_factura
                    s.cantidad_actual = s.cantidad_factura
                    s.activo = True
                    s.save()

                    transferencia.date_confirm = timezone.now()
                    transferencia.user_confirmacion = request.user.user_str()
                    transferencia.save()
        
        else:
            #Eliminando los productos transferidos anteriormente
            if "PV-" in transferencia.receptor_id:
                stock_transferencia = StockPuntoVenta.objects.filter(transferencia = transferencia)
                for s in stock_transferencia:
                    productos_ids.append(s.producto.id)
                    s.lote.cantidad_actual += s.cantidad_remitida
                    s.lote.activo = True
                    s.lote.save()

                    s.delete()

            elif "A-" in transferencia.receptor_id and "A-" in transferencia.emisor_id:
                stock_transferencia = StockAlmacen.objects.filter(transferencia = transferencia)
                for s in stock_transferencia:
                    productos_ids.append(s.producto.id)
                    sa = StockAlmacen.objects.filter(almacen__id = transferencia.emisor_id.replace("A-",""),lote = s.lote,producto=s.producto).order_by("-alta")
                    
                    if sa.exists():
                        _sa = sa.first()
                        _sa.cantidad_actual += s.cantidad_factura
                        _sa.activo = True
                        _sa.save()

                    s.delete()

            #Realizando la nueva transferencia        
            if "PV-" in receptor:
                for index,id in enumerate(productos_ids,start=0):
                    if float(cantidades[index]) > 0.0:
                        lotes = StockAlmacen.objects.filter(almacen__id=almacen_id,cantidad_actual__gt=0,producto__id = id).order_by("lote")
                        cantidad_descontar = float(cantidades[index])
                        existencia = lotes.first().producto.existencia(almacen_id)
                        
                        for lote in lotes:
                            if cantidad_descontar == 0: break
                            elif cantidad_descontar <= lote.cantidad_actual:
                                lote.cantidad_actual -= cantidad_descontar
                                if lote.cantidad_actual == 0:
                                    lote.activo = False
                                lote.save()
                                cantidad_descontar = 0
                            else:
                                cantidad_descontar -= lote.cantidad_actual
                                lote.cantidad_actual = 0
                                lote.activo = False
                                lote.save()


                        punto_venta = PuntoVenta.objects.get(id = receptor.replace("PV-",""))
                        StockPuntoVenta.objects.create(
                            punto_venta =punto_venta,
                            producto = lote.producto,
                            lote = lote,
                            transferencia = transferencia,
                            existencia = existencia,
                            cantidad_remitida = cantidades[index],
                        )
                        success = True

            elif "C-" in receptor:
                for index,id in enumerate(productos_ids,start=0):
                    if float(cantidades[index]) > 0.0:
                        lotes = StockAlmacen.objects.filter(almacen__id=almacen_id,cantidad_actual__gt=0,producto__id = id).order_by("lote")
                        cantidad_descontar = float(cantidades[index])
                        existencia = lotes.first().producto.existencia(almacen_id)
                        
                        for lote in lotes:
                            if cantidad_descontar == 0: break
                            elif cantidad_descontar <= lote.cantidad_actual:
                                lote.cantidad_actual -= cantidad_descontar
                                if lote.cantidad_actual == 0:
                                    lote.activo = False
                                lote.save()
                                cantidad_descontar = 0
                            else:
                                cantidad_descontar -= lote.cantidad_actual
                                lote.cantidad_actual = 0
                                lote.activo = False
                                lote.save()


                        cocina = Cocina.objects.get(id = receptor.replace("C-",""))
                        StockCocina.objects.create(
                            cocina =cocina,
                            producto = lote.producto,
                            lote = lote,
                            transferencia = transferencia,
                            existencia = existencia,
                            cantidad_remitida = cantidades[index],
                        )
                        success = True
            
            elif "A-" in receptor:
                for index,id in enumerate(productos_ids,start=0):
                    if float(cantidades[index]) > 0.0:
                        #lote = StockAlmacen.objects.get(id=lotes_ids[index])
                        
                        lotes = StockAlmacen.objects.filter(almacen__id=almacen_id,cantidad_actual__gt=0,producto__id = id).order_by("lote")
                        cantidad_descontar = float(cantidades[index])
                        existencia = lotes.first().producto.existencia(almacen_id)
                        
                        for lote in lotes:
                            if cantidad_descontar == 0: break
                            elif cantidad_descontar <= lote.cantidad_actual:
                                lote.cantidad_actual -= cantidad_descontar
                                if lote.cantidad_actual == 0:
                                    lote.activo = False
                                lote.save()
                                cantidad_descontar = 0
                            else:
                                cantidad_descontar -= lote.cantidad_actual
                                lote.cantidad_actual = 0
                                lote.activo = False
                                lote.save()


                        StockAlmacen.objects.create(
                            almacen = almacen_receptor,
                            producto = lote.producto,
                            lote = lote.lote,#datetime.now().strftime('%Y%m%d%H%M%S%f'),
                            cantidad_factura = float(cantidades[index]),
                            #cantidad_inicial = float(cantidades[index]),
                            #cantidad_actual = float(cantidades[index]),
                            costo_cup = lote.costo_cup,
                            transferencia = transferencia,
                            activo = True
                        )
                        success = True


        return redirect(data["url"])

@method_decorator(login_required, name='dispatch')
class EntradasSalidasView(View):
    def get(self,request,*args,**kwargs):
        data = request.GET
        almacenes = Almacen.objects.filter(activo = True).order_by("nombre")
        productos = Producto.objects.filter(activo = True).order_by("nombre")
        
        if "inicio" in data.keys() and "fin" in data.keys():
            inicio = datetime.strptime(data["inicio"], '%d/%m/%Y')
            fin = datetime.strptime(data["fin"], '%d/%m/%Y')
        else:
            fin = datetime.now().date()
            inicio = datetime.now().date()

        if "producto" in  data.keys() and data["producto"] != "":
            producto_id = data["producto"]
            producto_select = Producto.objects.get(id = producto_id)
        else:
            producto_select = Producto.objects.all().order_by("nombre").first()

        if "almacen" in  data.keys():
            almacen_id=data["almacen"]
            almacen_select = Almacen.objects.get(id = almacen_id)
        else:
            almacen_id=almacenes[0].id
            almacen_select = almacenes[0]
        
        if "operacion" in  data.keys() and data["operacion"] != "":
            operacion = data["operacion"]
        else:
            operacion = "es"


        stock_almacen = StockAlmacen.objects.filter(
            (Q(almacen__id = almacen_id) | 
            Q(transferencia__emisor_id = f"A-{almacen_id}") | 
            Q(transferencia__receptor_id = f"A-{almacen_id}")) &
            #(Q(transferencia__alta__date__range=[inicio, fin]) | Q(alta__date__range=[inicio, fin])) &  
            (Q(transferencia__date_confirm__isnull = False) | Q(transferencia__isnull = True))
            ).exclude(cantidad_actual=None)
        
        stock_punto_venta = StockPuntoVenta.objects.filter(
            Q(transferencia__emisor_id = f"A-{almacen_id}") &            
            #(Q(transferencia__alta__date__range=[inicio, fin]) | Q(alta__date__range=[inicio, fin])) &  
            (Q(transferencia__date_confirm__isnull = False) | Q(transferencia__isnull = True))
        )

        stock_cocina = StockCocina.objects.filter(
            (Q(transferencia__emisor_id = f"A-{almacen_id}") | 
            Q(transferencia__receptor_id = f"A-{almacen_id}")) &
            #(Q(transferencia__alta__date__range=[inicio, fin]) | Q(alta__date__range=[inicio, fin])) &  
            (Q(transferencia__date_confirm__isnull = False) | Q(transferencia__isnull = True))
            )
        
        stock_estudio = StockEstudio.objects.filter(
            Q(transferencia__emisor_id = f"A-{almacen_id}") &            
            #(Q(transferencia__alta__date__range=[inicio, fin]) | Q(alta__date__range=[inicio, fin])) &  
            (Q(transferencia__date_confirm__isnull = False) | Q(transferencia__isnull = True))
        )

        stock_trabajadores = StockUsuario.objects.filter(
            Q(transferencia__emisor_id = f"A-{almacen_id}") &            
            #(Q(transferencia__alta__date__range=[inicio, fin]) | Q(alta__date__range=[inicio, fin])) &  
            (Q(transferencia__date_confirm__isnull = False) | Q(transferencia__isnull = True))
        )
            
        cambios = CambiosAlmacen.objects.filter(
            almacen__id=almacen_id,
            #fecha__date__range=[inicio, fin]
        )
        
        if producto_select:
            stock_almacen = stock_almacen.filter(Q(producto=producto_select) | Q(transformacion__producto_inicial=producto_select))
            stock_punto_venta = stock_punto_venta.filter(producto=producto_select)
            stock_cocina = stock_cocina.filter(producto=producto_select)
            stock_estudio = stock_estudio.filter(producto=producto_select)
            stock_trabajadores = stock_trabajadores.filter(producto=producto_select)
        
        if operacion == "se":
            stock_almacen = stock_almacen.filter(Q(transferencia__receptor_id = f"A-{almacen_id}") | Q(transferencia__isnull = True))
            stock_punto_venta = []
            stock_cocina = []
            stock_estudio = []
            stock_trabajadores = []
            cambios = cambios.filter(cantidad__gt = 0)
            
        elif operacion == "ss":
            stock_almacen = stock_almacen.filter((Q(transferencia__emisor_id = f"A-{almacen_id}") | 
                                  Q(transformacion__isnull = False)) & 
                                  Q(informe_recepcion__isnull = True))

            cambios = cambios.filter(cantidad__lt = 0)

        _entradasSalidas = list(stock_almacen) + list(stock_punto_venta) + list(stock_cocina) + list(cambios) + list(stock_estudio) + list(stock_trabajadores)
        entradasSalidas = sorted(_entradasSalidas, key=lambda x: x.date_confirm if hasattr(x, 'date_confirm') else x.fecha if hasattr(x, 'fecha') else  x.alta,reverse=True)
        
        context = {
                    "inicio":inicio.strftime('%d/%m/%Y'),
                    "fin":fin.strftime('%d/%m/%Y'),
                    "entradas_salidas":entradasSalidas,
                    "almacenes":almacenes,
                    "almacen_select":almacen_select,
                    "productos":productos,
                    "producto_select":producto_select,
                    "operacion":operacion
                   }
        

        if not request.user.almacen_permission: context["base"] = "base.html"
        else: context["base"] = "almacen/base.html"
        
        return render(request,'almacen/entradas_salidas.html',context)
 
@method_decorator(login_required, name='dispatch')
class CancelarTransferenciaView(View):
    def get(self,request,id,rool,*args,**kwargs):
        transferencia_cancelada = Transferencia.objects.get(id=id)
        if transferencia_cancelada.date_confirm == None:
            if "PV-" in transferencia_cancelada.receptor_id and "A-" in transferencia_cancelada.emisor_id:
                stock_transferencia = StockPuntoVenta.objects.filter(transferencia = transferencia_cancelada)
                for s in stock_transferencia:
                    s.lote.cantidad_actual += s.cantidad_remitida
                    s.lote.activo = True
                    s.lote.save()

            if "bolsa-estudio" in transferencia_cancelada.receptor_id and "A-" in transferencia_cancelada.emisor_id:
                stock_transferencia = StockEstudio.objects.filter(transferencia = transferencia_cancelada)
                for s in stock_transferencia:
                    s.lote.cantidad_actual += s.cantidad_remitida
                    s.lote.activo = True
                    s.lote.save()

            elif "U-" in transferencia_cancelada.receptor_id and "A-" in transferencia_cancelada.emisor_id:
                stock_transferencia = StockUsuario.objects.filter(transferencia = transferencia_cancelada)
                for s in stock_transferencia:
                    s.lote.cantidad_actual += s.cantidad_remitida
                    s.lote.activo = True
                    s.lote.save()

            elif "PV-" in transferencia_cancelada.receptor_id and "C-" in transferencia_cancelada.emisor_id:
                stock_transferencia = StockPuntoVenta.objects.filter(transferencia = transferencia_cancelada)
                for s in stock_transferencia:
                    # aqui hay que ver para cuando se cancele que lo agregue bien
                    spc = StockProductoCompuestoCocina.objects.filter(producto = s.producto,turno__cocina__id = transferencia_cancelada.emisor_id.replace("C-","")).order_by("-fecha_fabricacion")
                    cantidad_remitida = s.cantidad_remitida
                    for lote in spc:
                        if lote.cantidad_actual < lote.cantidad_resultante:
                            if lote.cantidad_resultante - lote.cantidad_actual >= cantidad_remitida:
                                lote.cantidad_actual += cantidad_remitida
                                lote.activo = True
                                lote.save()
                                break
                            else:
                                cantidad_remitida -= (lote.cantidad_resultante - lote.cantidad_actual)
                                lote.cantidad_actual = lote.cantidad_resultante

                                lote.activo = True
                                lote.save()

            elif "A-" in transferencia_cancelada.receptor_id and "A-" in transferencia_cancelada.emisor_id:
                stock_transferencia = StockAlmacen.objects.filter(transferencia = transferencia_cancelada)
                for s in stock_transferencia:
                    sa = StockAlmacen.objects.filter(almacen__id = transferencia_cancelada.emisor_id.replace("A-",""),lote = s.lote)
                    
                    cantidad_descontar = s.cantidad_factura
                    
                    for lote in sa:
                        if lote.cantidad_inicial - lote.cantidad_actual >= cantidad_descontar:
                            lote.cantidad_actual += cantidad_descontar
                            lote.activo = True
                            lote.save()
                            break
                        else:
                            cantidad_descontar -= (lote.cantidad_inicial - lote.cantidad_actual)
                            lote.cantidad_actual = lote.cantidad_inicial

                            lote.activo = True
                            lote.save()

                    """if sa.exists():
                        _sa = sa.first()
                        _sa.cantidad_actual += s.cantidad_factura
                        _sa.save()"""

            elif "A-" in transferencia_cancelada.receptor_id and "C-" in transferencia_cancelada.emisor_id:
                stock_transferencia = StockAlmacen.objects.filter(transferencia = transferencia_cancelada)

                for item in stock_transferencia:
                    cantidad_descontar = item.cantidad_factura

                    stock_cocina = StockCocina.objects.filter(producto=item.producto,cocina__id = transferencia_cancelada.emisor_id.replace("C-","")).order_by("-alta")

                    for sc in stock_cocina:
                        if cantidad_descontar == 0: break
                        elif sc.cantidad_actual + cantidad_descontar <= sc.cantidad_inicial:
                            sc.cantidad_actual += cantidad_descontar
                            sc.activo = True
                            sc.save()
                            cantidad_descontar = 0
                            break
                        else:
                            cantidad_descontar -= (sc.cantidad_inicial - sc.cantidad_actual)
                            sc.cantidad_actual = sc.cantidad_inicial
                            sc.activo = True
                            sc.save()
            
            if "C-" in transferencia_cancelada.receptor_id and "C-" in transferencia_cancelada.emisor_id:
                stock_transferencia = StockCocina.objects.filter(transferencia = transferencia_cancelada)
                for s in stock_transferencia:
                    # aqui hay que ver para cuando se cancele que lo agregue bien
                    stock_cocina = StockCocina.objects.filter(producto=s.producto,cocina__id = transferencia_cancelada.emisor_id.replace("C-","")).order_by("-alta")
                    cantidad_descontar = s.cantidad_remitida
                    for sc in stock_cocina:
                        if cantidad_descontar == 0: break
                        elif sc.cantidad_actual + cantidad_descontar <= sc.cantidad_inicial:
                            sc.cantidad_actual += cantidad_descontar
                            sc.activo = True
                            sc.save()
                            cantidad_descontar = 0
                            break
                        else:
                            cantidad_descontar -= (sc.cantidad_inicial - sc.cantidad_actual)
                            sc.cantidad_actual = sc.cantidad_inicial
                            sc.activo = True
                            sc.save()
            
            elif "C-" in transferencia_cancelada.receptor_id and "A-" in transferencia_cancelada.emisor_id:
                stock_transferencia = StockCocina.objects.filter(transferencia = transferencia_cancelada)
                for s in stock_transferencia:
                    s.lote.cantidad_actual += s.cantidad_remitida
                    s.lote.activo = True
                    s.lote.save()
            
            transferencia_cancelada.delete()
        else:
            messages.error(request, "Error al cancelar transferencia, puede que el destino haya confirmado la transferencia.")

        if rool == "pv":
            return redirect("http://" + str(request.get_host()) + "/transferencia-pv/?" + request.GET.urlencode())
        if rool == "user":
            return redirect("http://" + str(request.get_host()) + f"/historial-transferencias/?" + request.GET.urlencode())
        elif rool == "cocina-get":
            return redirect("http://" + str(request.get_host()) + f"/historial-transferencias/get")
        elif rool == "cocina-post":
            return redirect("http://" + str(request.get_host()) + f"/cocina/historial-transferencias/post")
        else:
            return redirect("http://" + str(request.get_host()) + f"/historial-transferencias/?" + request.GET.urlencode())
       
    def post(self,request,id,rool,*args,**kwargs):
        data = request.POST
        transferencia_cancelada = Transferencia.objects.get(id=id)
        transferencia_cancelada.mensaje_cancelacion = data["message"]
        transferencia_cancelada.save()

        if rool == "pv":
            return redirect("TransferenciaPv")
        if rool == "salon":
            return redirect("TransferenciaSalon")
        elif rool == "cocina":
            return redirect("TransferenciaCocina",action="get")
        elif rool == "cocina-get":
            return redirect("TransferenciaCocina",action="get")
        elif rool == "cocina-post":
            return redirect("TransferenciaCocina",action="post")
        elif rool == "bolsa-estudio":
            return redirect("TransferenciasEstudio")
        else:
            return redirect("HistorialTransferencias")

# -- Punto de Venta
@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class RecibirTurnoView(View):
    def get(self,request,pv_id,*args,**kwargs):

        punto_venta = PuntoVenta.objects.get(id=pv_id)
        productos = punto_venta.productos()

        turno = Turno.objects.filter(punto_venta=punto_venta).order_by('-fin').first()        
        context = {
            "turno_anterior":turno,
            "productos":productos
            }

        return render(request,'punto_venta/recibir_turno.html',context)
    
    def post(self,request,pv_id,*args,**kwargs):
        try:
            data = request.POST
            punto_venta = PuntoVenta.objects.get(id=pv_id)

            if Turno.objects.filter(punto_venta=punto_venta,fin=None).exists():
                logout(request)
                
                messages.error(request, "Punto de Venta en funcionamiento, si su intención es entrar como trabajador auxiliar pídale al trabajador principal que le agregue.")
                return redirect("http://" + str(request.get_host()) + f'/?for=PV-{punto_venta.id}')
            
            if Turno.objects.filter(punto_venta = punto_venta).exists():
        
                turno_saliente = Turno.objects.filter(punto_venta = punto_venta).latest("fin")

                if "ids" in data.keys():ids = list(dict(data)["ids"])
                else:ids =  []

                if "ajuste-stock" in data.keys():ajuste_stock = list(dict(data)["ajuste-stock"])
                else:ajuste_stock =  []
                
                if "motivos-ajuste" in data.keys() and "id-producto" in data.keys() and "cantidad-ajuste" in data.keys():
                    motivos_ajuste = list(dict(data)["motivos-ajuste"])
                    id_producto = list(dict(data)["id-producto"])
                    cantidad_ajuste = list(dict(data)["cantidad-ajuste"])
                

                    for index,motivo in enumerate(motivos_ajuste,start=0):
                        try:
                            cuadre = Cuadre.objects.get(producto__id=id_producto[index],turno = turno_saliente)
                            cantidad = float(cantidad_ajuste[index])
                            monto = cantidad * cuadre.producto.precio_venta
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
                            
                            Nota.objects.create(
                                cantidad = cantidad,
                                motivo = motivo,
                                cuadre = cuadre,
                                monto = monto,
                            )
                        except Exception as e:
                            messages.error(request, f"Error al guardar notas: {e}")
                            print(f"Error al guardar notas: {e}")

                        
                    alert = AlertaAdmin.objects.create(
                        tipo=False,
                        centro_costo = f"PV-{punto_venta.id}",
                        motivo = f"Cambio de turno de {turno_saliente.user} en {punto_venta.nombre} efectuado con {len(motivos_ajuste)} incidencias."
                    )
                    
                    message = f"<b>🚨 {punto_venta.nombre}</b>\n\n"
                    message += f"Cambio de turno de {turno_saliente.user} en {punto_venta.nombre} efectuado con {len(motivos_ajuste)} incidencias."
                    
                    t = threading.Thread(target=lambda:send_message(message,alert.id))
                    t.start()
                    
                else:
                    alert = AlertaAdmin.objects.create(
                        tipo=None,
                        centro_costo = f"PV-{punto_venta.id}",
                        motivo = f"Cambio de turno de {turno_saliente.user} en {punto_venta.nombre} efectuado sin incidencias."
                    )

                    message = f"<b>✅ {punto_venta.nombre}</b>\n\n"
                    message += f"Cambio de turno de {turno_saliente.user} en {punto_venta.nombre} efectuado sin incidencias."
                    
                    t = threading.Thread(target=lambda:send_message(message,alert.id))
                    t.start()
               
                for index,id in enumerate(ids,start=0):
                    if Cuadre.objects.filter(turno=turno_saliente,producto__id=id).exists():
                        producto = Cuadre.objects.get(turno=turno_saliente,producto__id=id)
                        if ajuste_stock[index] != "-":
                            producto.entregado = ajuste_stock[index]
                        else:
                            producto.entregado = producto.producto.existencia_pv(punto_venta.id)
                            
                        producto.save()


                    stock = StockPuntoVenta.objects.filter(producto__id=id,cantidad_actual__gt=0,punto_venta=punto_venta).order_by("alta")
                    if stock.exists():
                        s = stock.first()
                        existencia  = s.producto.existencia_pv(punto_venta.id)

                        if ajuste_stock[index] != "-":
                            cantidad_descontar = existencia - float(ajuste_stock[index])

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
                                    elif spv.cantidad_actual < spv.cantidad_inicial:
                                        d = (spv.cantidad_inicial - spv.cantidad_actual)
                                        if d < 0: d *= -1
                                        cantidad_descontar -= d
                                        spv.cantidad_actual = spv.cantidad_inicial
                                        spv.activo = True
                                        spv.save()
                                        
                                if cantidad_descontar != 0:
                                    s.cantidad_actual += cantidad_descontar
                                    s.save()
                    else:
                        stock = StockPuntoVenta.objects.filter(producto__id=id,punto_venta=punto_venta).order_by("-alta")
                        if stock.exists():
                            s = stock.first()
                            existencia  = s.producto.existencia_pv(punto_venta.id)
                            if ajuste_stock[index] != "-":
                                cantidad_descontar = existencia - float(ajuste_stock[index])

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

                    if Cuadre.objects.filter(turno=turno_saliente,producto__id=id).exists():
                        producto = Cuadre.objects.get(turno=turno_saliente,producto__id=id)
                        
                        ext = StockPuntoVenta.objects.filter(
                            punto_venta=punto_venta,activo = True,
                            cantidad_inicial__isnull = False,
                            lote__almacen__is_audit = True
                            ).aggregate(total = Sum("cantidad_actual"))["total"]
                        if ext:
                            producto.entregado_ext = ext
                            producto.save()

                if turno_saliente.user == request.user:
                    alert = AlertaAdmin.objects.create(
                        tipo=True,
                        centro_costo = f"PV-{punto_venta.id}",
                        motivo = f"El trabajador {request.user} ha cerrado y abierto un turno en {punto_venta.nombre}"
                    )
                    
                    message = f"<b>⚠️ {punto_venta.nombre}</b>\n\n"
                    message += f"El trabajador {request.user} ha cerrado y abierto un turno en {punto_venta.nombre}"
                    
                    t = threading.Thread(target=lambda:send_message(message,alert.id))
                    t.start()
            
            turno = Turno.objects.get_or_create(
                punto_venta=punto_venta,
                user=request.user,
                fin = None
            )
            
            if turno[1]:
                productos = punto_venta.productos()  
                for producto in productos:
                    if producto.cant_stock > 0:
                        ext = StockPuntoVenta.objects.filter(
                            punto_venta=punto_venta,activo = True,
                            cantidad_inicial__isnull = False,lote__almacen__is_audit = True
                            ).aggregate(total = Sum("cantidad_actual"))["total"]
                        if not ext:
                            ext = 0

                        Cuadre.objects.create(
                            turno = turno[0],
                            producto = producto,
                            recibido = producto.cant_stock,
                            recibido_ext = ext
                        )                
                
            return redirect("CuentasPuntoVenta")
        
        except Exception as e:
            messages.error(request, "Error en el cuadre: " + e)
            return redirect("RecibirTurno", pv_id=pv_id)

@method_decorator(login_required, name='dispatch')
@method_decorator(punto_venta_required, name='dispatch')
class EntregarTurnoView(View):
    def get(self,request,*args,**kwargs):
        turno = Turno.objects.get(user=request.user,punto_venta=request.user.punto_venta(),fin=None)
        productos = Cuadre.objects.filter(turno = turno)

        monto_caja = 0.0

        ventas = Venta.objects.filter(cuenta__turno = turno)
        for venta in ventas:
            monto_caja += venta.monto

        turno = Turno.objects.get(user=request.user,punto_venta=request.user.punto_venta(),fin=None)

        monto_vendido = 0.0
        cant_ventas = 0
        ventas = Venta.objects.filter(cuenta__turno = turno,cuenta__abierta = False)
        for venta in ventas:
            monto_vendido += venta.monto
            cant_ventas += venta.cantidad

        cant_clientes = len(Cuenta.objects.filter(punto_venta=request.user.punto_venta(),turno=turno))
        cuentas_abiertas = len(Cuenta.objects.filter(punto_venta=request.user.punto_venta(),turno=turno,abierta=True))

        if Cuenta.objects.filter(punto_venta=request.user.punto_venta(),abierta=True).exists():
            context = {
                "monto_caja":toMoney(monto_caja),
                "productos":productos,
                "message":"Antes de terminar el turno debe cerrar todas las cuentas abiertas",
                "monto_vendido":toMoney(monto_vendido),"cant_ventas":int(cant_ventas),
                "cant_clientes":cant_clientes,"cuentas_abiertas":cuentas_abiertas
                }
            return render(request,'punto_venta/entregar_turno.html',context)
        
        if Transferencia.objects.filter(receptor_id=f"PV-{request.user.punto_venta().id}",turno_id__isnull = True,mensaje_cancelacion=None).exists():
            
            context = {
                "monto_caja":toMoney(monto_caja),
                "productos":productos,
                "message":"Antes de terminar el turno debe aceptar o cancelar todas las transferencias pendientes",
                "monto_vendido":toMoney(monto_vendido),"cant_ventas":int(cant_ventas),
                "cant_clientes":cant_clientes,"cuentas_abiertas":cuentas_abiertas
                }
            return render(request,'punto_venta/entregar_turno.html',context)
        
        if SolicitudCocina.objects.filter(venta__cuenta__punto_venta = request.user.punto_venta(),activo=True,mensaje_cancelacion=None).exists():
            
            context = {
                "monto_caja":toMoney(monto_caja),
                "productos":productos,
                "message":"Antes de terminar el turno debe aceptar o cancelar todas las solicitudes a la cocina",
                "monto_vendido":toMoney(monto_vendido),"cant_ventas":int(cant_ventas),
                "cant_clientes":cant_clientes,"cuentas_abiertas":cuentas_abiertas
                }
            return render(request,'punto_venta/entregar_turno.html',context)

        context = {"monto_caja":toMoney(monto_caja),"productos":productos,"monto_vendido":toMoney(monto_vendido),
                   "cant_ventas":int(cant_ventas),"cant_clientes":cant_clientes,"cuentas_abiertas":cuentas_abiertas}

        return render(request,'punto_venta/entregar_turno.html',context)
    
    def post(self,request,*args,**kwargs):
        data = request.POST
        punto_venta=request.user.punto_venta()
        if Cuenta.objects.filter(punto_venta=punto_venta,abierta=True).exists():return  redirect("EntregarTurno")

        turno = Turno.objects.get(user=request.user,punto_venta=punto_venta,fin=None) 
        turno.fin = timezone.now()
        turno.recibido = data["recibido"]
        turno.monto_caja = data["monto-caja"]
        turno.monto_maquina = data["monto-maquina"]
        turno.monto_letra = data["monto-letras"]

        monto = float(data["monto-caja"])
        if data["monto-puerta"] != "":
            monto += float(data["monto-puerta"])
            turno.monto_puerta = data["monto-puerta"]

        recibo = ReciboEfectivo.objects.create(
            origen = f"PV-{turno.id}",
            recibido = data["recibido"],
            monto = monto,
            monto_letra = data["monto-letras"]
        )
        
        if "motivo-diferencia" in data and data["motivo-diferencia"] != "": 
            motivo = data["motivo-diferencia"]
            recibo.motivo_diferencia = motivo
            recibo.save()
            alert = AlertaAdmin.objects.create(
                tipo=True,
                centro_costo = f"PV-{punto_venta.id}",
                motivo = f"El punto de venta {punto_venta.nombre} ha emitido un recibo de efectivo con diferencias entre el monto en caja y el monto en máquina durante el turno de {turno.user.user} (MOTIVO: {motivo})"
            )

            message = f"<b>⚠️ {punto_venta.nombre}</b>\n\n"
            message +=  f"El punto de venta {punto_venta.nombre} ha emitido un recibo de efectivo con diferencias entre el monto en caja y el monto en máquina durante el turno de {turno.user.user}\n"
            message +=  f"<u>MOTIVO:</u> {motivo}"
            
            t = threading.Thread(target=lambda:send_message(message,alert.id))
            t.start()

            if float(turno.monto_caja) < float(turno.monto_maquina):
                faltante = float(turno.monto_maquina) - float(turno.monto_caja)
                Descuentos.objects.create(
                    monto_original = monto,
                    monto = faltante,
                    descripcion = f"Faltan ${toMoney(faltante)} en la caja de {turno.punto_venta.nombre} al cerrar el turno.",
                    motivo = motivo,
                    user_id = f"U-{turno.user.id}",
                    user_name = turno.user.user
                )
        
        monto_turno = 0.0
        costo_turno = 0.0
        monto_ext_turno = 0.0
        costo_ext_turno = 0.0

        monto_vendido = 0.0
        ganancia = 0.0
        cant_ventas = 0
        ventas = Venta.objects.filter(cuenta__turno = turno)
        for venta in ventas:
            monto_vendido += venta.monto
            cant_ventas += venta.cantidad
            ganancia += venta.ganancia

            if (venta.producto and not venta.producto.is_compuesto) or venta.formula_id:
                monto_turno += venta.monto
                costo_turno += (venta.monto - venta.ganancia)
                monto_ext_turno += venta.monto_ext
                costo_ext_turno += venta.costo_ext



        pago_ganancia = turno.pago_ganancia(ganancia)
        pago_venta = turno.pago_venta(monto_vendido)
        pago_minutos = turno.pago_minutos()
        pago_fijo = turno.pago_fijo()
        pago_conciliado = turno.pago_conciliado(monto_vendido)

        if pago_ganancia:
            pago = Pago.objects.create(
                monto_original = pago_ganancia,
                monto = pago_ganancia,
                descripcion = f"{punto_venta.pago_ganancia}% de la ganancia generada por el turno",
                user_id = f"U-{request.user.id}",
                user_name = request.user.user_str()
            )
            turno.pagos.add(pago)
            
        if pago_venta:
            pago = Pago.objects.create(
                monto_original = pago_venta,
                monto = pago_venta,
                descripcion = f"{punto_venta.pago_venta}% de la venta durante el turno",
                user_id = f"U-{request.user.id}",
                user_name = request.user.user_str()
            )
            turno.pagos.add(pago)

        if pago_minutos:
            pago = Pago.objects.create(
                monto_original = pago_minutos,
                monto = pago_minutos,
                descripcion = f"Pago efectuado en correspondencia al tiempo trabajado",
                user_id = f"U-{request.user.id}",
                user_name = request.user.user_str()
            )
            turno.pagos.add(pago)

        if pago_fijo:
            pago = Pago.objects.create(
                monto_original = pago_fijo,
                monto = pago_fijo,
                descripcion = f"Pago de salario fijo asignado al turno",
                user_id = f"U-{request.user.id}",
                user_name = request.user.user_str()
            )
            turno.pagos.add(pago)

        if pago_conciliado:
            conciliacion = punto_venta.pago_conciliado.split("|")
            pago = Pago.objects.create(
                monto_original = pago_conciliado,
                monto = pago_conciliado,
                descripcion = f"{conciliacion[1]}% de las ventas despues de ${conciliacion[0]}",
                user_id = f"U-{request.user.id}",
                user_name = request.user.user_str()
            )
            turno.pagos.add(pago)

        if punto_venta.pago_asociado:
            for user in turno.users_extra.all():
                pago = Pago.objects.create(
                    monto_original = punto_venta.pago_asociado,
                    monto = punto_venta.pago_asociado,
                    descripcion = f"Pago de salario fijo asignado a trabajadores asociados",
                    user_id = f"U-{user.id}",
                    user_name = user.user
                )
                turno.pagos.add(pago)

        turno.monto = monto_turno
        turno.costo = costo_turno
        turno.monto_ext = monto_ext_turno
        turno.costo_ext = costo_ext_turno
        turno.save()
        return  redirect("ResumenTurno",turno_id=turno.id)

@method_decorator(login_required, name='dispatch')
@method_decorator(punto_venta_required, name='dispatch')
class ResumenTurnoView(View):
    def get(self,request,turno_id,*args,**kwargs):
        turno = Turno.objects.get(id=turno_id)
        
        monto_vendido = 0.0
        ganancia = 0.0
        cant_ventas = 0
        ventas = Venta.objects.filter(cuenta__turno = turno)
        for venta in ventas:
            monto_vendido += venta.monto
            cant_ventas += venta.cantidad
            ganancia += venta.ganancia

        cant_clientes = len(Cuenta.objects.filter(punto_venta=request.user.punto_venta(),turno=turno))

        pago_ganancia = turno.pago_ganancia(ganancia)
        pago_venta = turno.pago_venta(monto_vendido)
        pago_minutos = turno.pago_minutos()
        pago_fijo = turno.pago_fijo()
        pago_conciliado = turno.pago_conciliado(monto_vendido)

        pago_total = toMoney(turno.pago_total(ganancia,monto_vendido))

        salario_ayudantes = []

        for a in turno.users_extra.all():
            salario_ayudantes.append(
                {
                    "n":a.user,
                    "v":turno.punto_venta.pago_asociado
                }
            )

        context = {
            "turno":turno,
            "monto_vendido":toMoney(monto_vendido),
            "cant_ventas":int(cant_ventas),
            "cant_clientes":cant_clientes,
            "pago_ganancia":pago_ganancia,
            "pago_venta":pago_venta,
            "pago_minutos":pago_minutos,
            "pago_fijo":pago_fijo,
            "pago_conciliado":pago_conciliado,
            "pago_total":pago_total,
            "salario_ayudantes":salario_ayudantes
            }

        return render(request,'punto_venta/resumen_turno.html',context)

@method_decorator(login_required, name='dispatch')
@method_decorator(punto_venta_required, name='dispatch')
class TransferenciaPvView(View):
    def get(self,request,*args,**kwargs):
        turno = Turno.objects.get(user=request.user,punto_venta=request.user.punto_venta(),fin=None)
        transferencias = Transferencia.objects.filter(Q(receptor_id=f"PV-{request.user.punto_venta().id}") & (Q(turno_id=f"PV-{turno.id}") | Q(turno_id=None)) & Q(mensaje_cancelacion__isnull = True)).order_by("alta").reverse()
        transferencias_return = []
        for transferencia in transferencias:
            try:
                emisor = transferencia.emisor()
                if isinstance(emisor, str):
                    transferencia.emisor_cosina = Cocina.objects.get(id=emisor.replace("C-",""))
                transferencias_return.append(transferencia)
            except:pass
        
        context = {"transferencias":transferencias_return}

        return render(request,'punto_venta/transferencias.html',context)
    
    def post(self,request,*args,**kwargs):
        data = request.POST

        pv_ids = list(dict(data)["producto-pv-id"])
        cantidades = list(dict(data)["cantidad"])
        try:
            punto_venta=request.user.punto_venta()
            turno = Turno.objects.get(user=request.user,punto_venta=punto_venta,fin=None)
            for index,id in enumerate(pv_ids,start=0):
                stock_punto_venta = StockPuntoVenta.objects.get(id=id)
                cant = cantidades[index]
                stock_punto_venta.cantidad_recibida = cant

                if stock_punto_venta.lote:
                    existencia = stock_punto_venta.lote.producto.existencia(stock_punto_venta.lote.almacen.id)

                    por_confirmar = StockPuntoVenta.objects.filter(producto=stock_punto_venta.producto,transferencia__turno_id = None, transferencia__emisor_id = f"A-{stock_punto_venta.lote.almacen.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
                    if por_confirmar is not None:
                        existencia = existencia + por_confirmar

                    por_confirmar = StockCocina.objects.filter(producto=stock_punto_venta.producto, transferencia__turno_id = None, transferencia__emisor_id = f"A-{stock_punto_venta.lote.almacen.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
                    if por_confirmar is not None:
                        existencia = existencia + por_confirmar

                    por_confirmar = StockAlmacen.objects.filter(producto=stock_punto_venta.producto, cantidad_inicial = None, transferencia__emisor_id = f"A-{stock_punto_venta.lote.almacen.id}").aggregate(total = Sum("cantidad_factura"))["total"]
                    if por_confirmar is not None:
                        existencia = existencia + por_confirmar

                    por_confirmar = StockUsuario.objects.filter(producto=stock_punto_venta.producto,transferencia__turno_id = None, transferencia__emisor_id = f"A-{stock_punto_venta.lote.almacen.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
                    if por_confirmar is not None:
                        existencia = existencia + por_confirmar
                        
                    por_confirmar = StockEstudio.objects.filter(producto=stock_punto_venta.producto,transferencia__turno_id = None, transferencia__emisor_id = f"A-{stock_punto_venta.lote.almacen.id}").aggregate(total = Sum("cantidad_remitida"))["total"]
                    if por_confirmar is not None:
                        existencia = existencia + por_confirmar
                        
                    existencia -= float(cant)

                else:existencia = None

                #stock_punto_venta.cantidad_inicial = cant
                stock_punto_venta.cantidad_actual += cant
                stock_punto_venta.existencia = existencia
                stock_punto_venta.activo = True
                stock_punto_venta.save()
                
                if not Cuadre.objects.filter(turno = turno,producto = stock_punto_venta.producto).exists():
                    Cuadre.objects.create(
                        turno = turno,
                        producto = stock_punto_venta.producto,
                        recibido = 0
                    )

                if stock_punto_venta.transferencia.turno_id is None and index + 1 == len(pv_ids):
                    stock_punto_venta.transferencia.date_confirm = timezone.now()
                    stock_punto_venta.transferencia.user_confirmacion = request.user.user_str()
                    stock_punto_venta.transferencia.turno_id = f"PV-{turno.id}"
                    stock_punto_venta.transferencia.save()
        except:
            messages.error(request, "Error al confirmar transferencia, puede que el remitente haya cancelado la transferencia.")

        return redirect("TransferenciaPv")
        
@method_decorator(login_required, name='dispatch')
@method_decorator(punto_venta_required, name='dispatch')
class CuentasView(View):
    def get(self,request,*args,**kwargs):
        punto_venta=request.user.punto_venta()
        if not punto_venta: return redirect("logout")

        turno = Turno.objects.get(punto_venta=punto_venta,fin=None)
        categorias = Categoria.objects.filter(activo=True)
        productos = request.user.punto_venta().productos(False,True,False)
        

        if request.user == turno.user:
            cuentas = Cuenta.objects.filter(punto_venta=punto_venta,turno=turno,nombre__isnull=False).order_by("creacion").reverse()
        else:
            cuentas = Cuenta.objects.filter(punto_venta=punto_venta,turno=turno,user=request.user,nombre__isnull=False).order_by("creacion").reverse()

        

        productos_ids = []
        formulas = Formula.objects.filter(
            activo=True
            ).exclude(producto__categoria__nombre = "SUBPRODUCTOS"
            ).exclude(producto__categoria__nombre = "MEDIOS BASICOS"
            ).exclude(producto__categoria__nombre="SUBPRODUCTOS SALON"
            ).exclude(producto__categoria__nombre="ACCESORIOS, PRENDAS Y OTROS")
        formulas_return = []
        for formula in formulas:
            formula.producto.disponibilidad = 999999999 # Para hacer una alta disponibilidad
            formula.producto.pre_id = "FC-"
            formulas_return.append(formula.producto)
            productos_ids.append(formula.producto.id)

        formulas = FormulaPv.objects.filter(activo=True)
        formulas_pv_return = []
        for formula in formulas:
            disponibilidad = formula.disponibilidad_pv(punto_venta.id)
            
            if disponibilidad and disponibilidad > 0:
                formula.disponibilidad = disponibilidad
                formula.pre_id = "FPV-"
                formulas_pv_return.append(formula)

        cant_clientes = len(Cuenta.objects.filter(punto_venta=request.user.punto_venta(),turno=turno)) + 1

        context = {}

        if "cuenta" in request.GET:
            cuenta_id = int(request.GET["cuenta"])
            cuenta = Cuenta.objects.get(id=cuenta_id)
            ventas,monto_total,monto_total_money = cuenta.ventas()
            status_cuenta = cuenta.abierta
            message = None

            if status_cuenta == True:
                ventas_pedidos = Venta.objects.filter(cuenta = cuenta)
                for venta in ventas_pedidos:
                    solicitudes = venta.producto_solicitado_cosina.filter(activo=True)
                    
                    if solicitudes.exists():
                        status_cuenta = False
                        message = "Existen pedidos a cosina pendientes a procesar"
                    if message != None: break

            context["cuenta_select"] = {
                "cuenta":cuenta,
                "ventas":ventas,
                "monto_total":monto_total,
                "monto_total_money":monto_total_money,
                "message":message,
                "status_cuenta":status_cuenta
            }

        context.update({"productos":productos,"cuentas":cuentas,"categorias":categorias,"cant_clientes":cant_clientes,"formulas_return":formulas_return,"formulas_pv_return":formulas_pv_return})

        return render(request,'punto_venta/cuentas.html',context)

    def post(self,request,*args,**kwargs):
        data = request.POST

        punto_venta = request.user.punto_venta()
        if not punto_venta: return redirect("logout")
        
        turno = Turno.objects.get(punto_venta=punto_venta,fin=None)
        if "id-entregar" in data:
            venta = Venta.objects.get(id=data["id-entregar"])
            venta.trab_primario = True
            venta.save()
            return redirect(str(request.build_absolute_uri()))


        Cuenta.objects.create(nombre = data["nueva-cuenta"],punto_venta=punto_venta,user=request.user,turno=turno)

        monto_vendido = 0.0
        cant_ventas = 0
        ventas = Venta.objects.filter(cuenta__turno = turno)
        for venta in ventas:
            monto_vendido += venta.monto
            cant_ventas += venta.cantidad

        return redirect("CuentasPuntoVenta")

@method_decorator(login_required, name='dispatch')
@method_decorator(punto_venta_required, name='dispatch')
class VentaRapidaView(View):
    def get(self,request,*args,**kwargs):
        punto_venta=request.user.punto_venta()        
        if not punto_venta: return redirect("logout")

        categorias = Categoria.objects.filter(activo=True)
        productos = punto_venta.productos(False,False,False)
        #print(productos)

        turno = Turno.objects.get(user=request.user,punto_venta=punto_venta,fin=None)
        cant_clientes = len(Cuenta.objects.filter(punto_venta=punto_venta,turno=turno)) + 1

        productos_ids = []
        formulas = Formula.objects.filter(activo=True).exclude(producto__categoria__nombre = "SUBPRODUCTOS").exclude(producto__categoria__nombre = "MEDIOS BASICOS").exclude(producto__categoria__nombre="SUBPRODUCTOS SALON").exclude(producto__categoria__nombre="ACCESORIOS, PRENDAS Y OTROS")
        
        formulas_return = []
        for formula in formulas:
            if formula.cocinas.filter(puntos_venta = punto_venta).exists():
                formula.producto.disponibilidad = 999999999 # Para hacer una alta disponibilidad
                formula.producto.pre_id = "FC-"
                formulas_return.append(formula.producto)
                productos_ids.append(formula.producto.id)
                
        formulas = FormulaPv.objects.filter(activo=True)
        formulas_pv_return = []
        for formula in formulas:
            #disponibilidad = formula.disponibilidad_pv(punto_venta.id)
            #if disponibilidad and disponibilidad > 0:
                #formula.disponibilidad = disponibilidad
                formula.disponibilidad = 999999999 # Para hacer una alta disponibilidad
                formula.pre_id = "FPV-"
                formulas_pv_return.append(formula)
        
        context = {"productos":productos,"categorias":categorias,"cant_clientes":cant_clientes,
                   "formulas_return":formulas_return,"formulas_pv_return":formulas_pv_return}

        return render(request,'punto_venta/venta_rapida.html',context)
    
    def post(self,request,*args,**kwargs):
        data = request.POST
        punto_venta=request.user.punto_venta()        
        if not punto_venta: return redirect("logout")
        
        turno = Turno.objects.get(punto_venta=punto_venta,fin=None)

        if "cuenta-name" in data:
            cuenta_name = data["cuenta-name"]
            if cuenta_name == "":
                cuenta = Cuenta.objects.create(punto_venta=punto_venta,turno=turno,user=request.user,abierta=False)
            else:
                cuenta = Cuenta.objects.create(nombre=cuenta_name,punto_venta=punto_venta,turno=turno,user=request.user,abierta=True)
        elif "cuenta-id" in data:
            cuenta_name = ""
            cuenta = Cuenta.objects.get(id = data["cuenta-id"])

        ids = list(dict(data)["ids"])
        cantidades = list(dict(data)["cantidad"])

        mensaje = []

        for index,id in enumerate(ids,start=0):
            cocinas_pv = punto_venta.puntos_venta_cocina.all()
            if "FC-" in id:
                
                producto = Producto.objects.get(id=id.replace("FC-",""))
                cantidad = int(cantidades[index])
                monto = producto.precio_venta * cantidad
                venta = Venta.objects.create(
                    cuenta = cuenta,
                    producto = producto,
                    cantidad = cantidad,
                    monto = monto,
                    ganancia =0.0
                )

                
                formula = Formula.objects.filter(activo=True,producto__id=id.replace("FC-","")).first()
                success = False
                if formula:
                    for cocina in cocinas_pv:# 
                        if cocina in list(formula.cocinas.all()) and TurnoCosina.objects.filter(cocina=cocina,fin=None).exists():
                            SolicitudCocina.objects.create(
                                venta=venta,
                                cantidad = cantidad,
                                cocina = cocina
                            )
                            success = True
                            break
                if success == False:
                    mensaje.append("No se puede eleaborar el producto debido a que no existe una cocina que elabore el producto.")
                    venta.delete()

            elif "FPV-" in id:
                formula_id = id.replace("FPV-","")
                formula = FormulaPv.objects.get(id=formula_id)
                cantidad = int(cantidades[index])
                venta = Venta.objects.create(
                    cuenta = cuenta,
                    formula_id = formula_id,
                    cantidad = cantidad,
                    monto = formula.precio_venta() * cantidad
                )
                for subproducto in formula.subproductos.all():
                    ganancia_dinero = 0.0
                    monto_ext = 0
                    costo_ext = 0
                    
                    stock = StockPuntoVenta.objects.filter(producto=subproducto.producto,cantidad_actual__gt=0,punto_venta=request.user.punto_venta()).order_by("alta")
                    cantidad_descontar = cantidad * subproducto.cantidad
                    for item in stock:
                        if cantidad_descontar == 0: break
                        elif item.cantidad_actual >= cantidad_descontar:
                            ganancia_dinero += item.ganancia_dinero() * cantidad_descontar
                            item.cantidad_actual -= cantidad_descontar
                            if item.lote_auditable:
                                monto_ext += (subproducto.producto.precio_venta * cantidad_descontar)
                                costo_ext += (item.costo_cup() * cantidad_descontar)
                            item.save()
                            cantidad_descontar = 0
                            break
                        else:
                            ganancia_dinero += item.ganancia_dinero() * item.cantidad_actual
                            #cantidad_descontar -= item.cantidad_actual
                            cantidad_descontar = 0
                            if item.lote_auditable:
                                monto_ext += (subproducto.producto.precio_venta * item.cantidad_actual)
                                costo_ext += (item.costo_cup() * item.cantidad_actual)
                            item.cantidad_actual = 0
                            item.save()

                    venta.monto_ext = monto_ext
                    venta.costo_ext = costo_ext
                    venta.ganancia = ganancia_dinero
                    venta.save()
        
            else:
                producto = Producto.objects.get(id=id)
                cantidad = int(cantidades[index])

                ganancia_dinero = 0.0
                monto_ext = 0
                costo_ext = 0

                stock = StockPuntoVenta.objects.filter(producto=producto,cantidad_actual__gt=0,punto_venta=request.user.punto_venta()).order_by("alta")
                cantidad_descontar = cantidad
                for item in stock:
                    if cantidad_descontar == 0: break
                    elif item.cantidad_actual >= cantidad_descontar:
                        g = item.ganancia_dinero() * cantidad_descontar
                        ganancia_dinero += g
                        item.cantidad_actual -= cantidad_descontar
                        item.save()
                        if item.lote_auditable:
                            monto_ext += (producto.precio_venta * cantidad_descontar)
                            costo_ext += (item.costo_cup() * cantidad_descontar)
                        cantidad_descontar = 0
                        break
                    else:
                        g = item.ganancia_dinero() * item.cantidad_actual
                        ganancia_dinero +=  g
                        cantidad_descontar -= item.cantidad_actual
                        if item.lote_auditable:
                            monto_ext += (producto.precio_venta * item.cantidad_actual)
                            costo_ext += (item.costo_cup() * item.cantidad_actual)
                        item.cantidad_actual = 0
                        item.activo = False
                        item.save()

                cantidad_vendida = cantidad - cantidad_descontar
                venta = Venta.objects.create(
                    cuenta = cuenta,
                    producto = producto,
                    cantidad = cantidad_vendida,
                    monto = float(producto.get_precios_diferenciados(punto_venta.id)) * cantidad_vendida
                )
                venta.monto_ext = monto_ext
                venta.costo_ext = costo_ext
                venta.ganancia = ganancia_dinero                
                if request.user != turno.user: venta.trab_primario = False
                venta.save()
                
                beneficio_venta = round((ganancia_dinero*100) / producto.precio_venta,2)
                ganancia_dinero_money = toMoney(ganancia_dinero/cantidad_vendida)

                if beneficio_venta <= 1:
                    alert = AlertaAdmin.objects.create(
                        tipo=True,
                        centro_costo = f"PV-{punto_venta.id}",
                        motivo = f"Venta de {producto.nombre} en perdida, con un margen de beneficio de ${ganancia_dinero_money}({beneficio_venta}%)"
                    )
                    
                    message = f"<b>🚨 {punto_venta.nombre}</b>\n\n"
                    message += f"Venta de {producto.nombre} en perdida, con un margen de beneficio de ${ganancia_dinero_money}({beneficio_venta}%)"
                    
                    t = threading.Thread(target=lambda:send_message(message,alert.id))
                    t.start()


                elif beneficio_venta < 5:
                    alert = AlertaAdmin.objects.create(
                        tipo=False,
                        centro_costo = f"PV-{punto_venta.id}",
                        motivo = f"Venta de {producto.nombre} con un margen de beneficio de ${ganancia_dinero_money}({beneficio_venta}%)"
                    )
                    
                    message = f"<b>⚠️ {punto_venta.nombre}</b>\n\n"
                    message += f"Venta de {producto.nombre} con un margen de beneficio de ${ganancia_dinero_money}({beneficio_venta}%)"
                    
                    t = threading.Thread(target=lambda:send_message(message,alert.id))
                    t.start()

                if cantidad_descontar > 0:
                    mensaje.append(f"Faltó por venderse <b>{cantidad_descontar} {producto.nombre}</b> debido a no haber disponibilidad en el punto de venta.")

        if len(mensaje) > 0:
            messages.error(request, "</br>".join(mensaje))

        if "cuenta-id" in data:
            cuanta_id = data["cuenta-id"]
            return redirect(f"/cuentas-punto-venta/?cuenta={cuanta_id}")
        else:
            return redirect("VentaRapida")

@method_decorator(login_required, name='dispatch')
@method_decorator(punto_venta_required, name='dispatch')
class RegistroVentasView(View):
    def get(self,request,*args,**kwargs):
        punto_venta=request.user.punto_venta()
        turno = Turno.objects.get(punto_venta=punto_venta,fin=None)
        if request.user == turno.user:
            ventas = Venta.objects.filter(cuenta__turno = turno).order_by("-instante")
            ventas_delete = True
        else:
            ventas = Venta.objects.filter(cuenta__user = request.user).order_by("-instante")
            ventas_delete = False

        context = {"ventas":ventas,"punto_venta":punto_venta,"ventas_delete":ventas_delete}

        return render(request,'punto_venta/ventas.html',context)
            
    def post(self,request,*args,**kwargs):
        try:
            data = request.POST
            id_venta = data["id-venta-delete"]
            punto_venta=request.user.punto_venta()
            turno = Turno.objects.get(user=request.user,punto_venta=punto_venta,fin=None)
            venta = Venta.objects.get(cuenta__turno = turno,id = id_venta)

            if venta.formula_id:
                formula = venta.formula()
                for subproducto in formula.subproductos.all():
                    stock = StockPuntoVenta.objects.filter(punto_venta=punto_venta,producto = subproducto.producto,cantidad_actual__isnull=False).order_by("-alta")

                    cantidad_descontar = subproducto.cantidad * venta.cantidad
                    for item in stock:
                        if cantidad_descontar == 0: break
                        elif item.cantidad_actual + cantidad_descontar > item.cantidad_inicial:
                            cantidad_descontar = cantidad_descontar - (item.cantidad_inicial - item.cantidad_actual)
                            item.cantidad_actual = item.cantidad_inicial
                            item.activo = True
                            item.save()
                        else:
                            item.cantidad_actual += cantidad_descontar
                            item.activo = True
                            item.save()
                            cantidad_descontar = 0
                            break
                
            elif data["id-solicitud"] == "":
                stock = StockPuntoVenta.objects.filter(punto_venta=punto_venta,producto = venta.producto,cantidad_actual__isnull=False).order_by("-alta")

                cantidad_descontar = venta.cantidad
                for item in stock:
                    if item.cantidad_actual < item.cantidad_inicial:
                        if cantidad_descontar == 0: break
                        elif item.cantidad_actual + cantidad_descontar > item.cantidad_inicial:
                            cantidad_descontar = cantidad_descontar - (item.cantidad_inicial - item.cantidad_actual)
                            item.cantidad_actual = item.cantidad_inicial
                            item.activo = True
                            item.save()
                        else:
                            item.cantidad_actual += cantidad_descontar
                            item.activo = True
                            item.save()
                            cantidad_descontar = 0
                            break
                
            venta.delete()

        except Exception as e:
            print(e)
            pass

        return redirect("RegistroVentas")

@method_decorator(login_required, name='dispatch')
@method_decorator(punto_venta_required, name='dispatch')
class SolicitudesView(View):
    def get(self,request,*args,**kwargs):
        punto_venta=request.user.punto_venta()
        
        if not punto_venta: return redirect("logout")

        solicitudes = SolicitudCocina.objects.filter(venta__cuenta__punto_venta = punto_venta,venta__cuenta__user = request.user,activo=True,mensaje_cancelacion=None)
        context = {"solicitudes":solicitudes}

        return render(request,'punto_venta/solicitudes.html',context)
    
    def post(self,request,*args,**kwargs):
        data = request.POST
        punto_venta=request.user.punto_venta()        
        if not punto_venta: return redirect("logout")

        if "id-solicitud-cancelada" in data.keys() and data["id-solicitud-cancelada"] != "":
            solicitud = SolicitudCocina.objects.get(id=data["id-solicitud-cancelada"])
            if solicitud.estado == None:
                if solicitud.venta.cantidad == solicitud.cantidad:
                    solicitud.venta.delete()
                else:
                    solicitud.venta.monto = solicitud.venta.monto - ((solicitud.venta.cantidad - solicitud.cantidad) * solicitud.venta.producto.precio_venta)
                    solicitud.venta.cantidad -= solicitud.cantidad
                    solicitud.venta.save()
                    solicitud.delete()

                return redirect("SolicitudesPv")

            else:
                punto_venta=request.user.punto_venta()
                solicitudes = SolicitudCocina.objects.filter(venta__cuenta__punto_venta = punto_venta)
                context = {"solicitudes":solicitudes}
                if solicitud.estado == False:
                    messages.error(request, 'Error al cancelar pedido. El pedido no puede ser cancelado debido a que está elaborandose.')
                else:
                    messages.error(request, 'Error al cancelar pedido. El pedido no puede ser cancelado debido a que ya se encuentra elaborado.')
                    
                return redirect("SolicitudesPv")
            
        if "id-solicitud-transferida-cancelada" in data.keys() and data["id-solicitud-transferida-cancelada"] != "":
            solicitud = SolicitudCocina.objects.get(id=data["id-solicitud-transferida-cancelada"])
            solicitud.mensaje_cancelacion = data["message"]
            solicitud.transferido = False
            solicitud.save()

        if "id-solicitud-transferida" in data.keys() and data["id-solicitud-transferida"] != "":
            
            solicitud = SolicitudCocina.objects.get(id=data["id-solicitud-transferida"])
            stock = StockProductoCompuestoCocina.objects.filter(turno__cocina=solicitud.cocina,producto=solicitud.venta.producto,cantidad_actual__gt=0).order_by("fecha_fabricacion")

            monto_ext = 0
            costo_ext = 0
            costos = []
            cantidad_descontar = solicitud.cantidad
            for item in stock:
                if cantidad_descontar == 0: break
                elif item.cantidad_actual >= cantidad_descontar:
                    item.cantidad_actual -= cantidad_descontar
                    item.save()

                    if item.lote_auditable:
                        monto_ext += (item.producto.precio_venta * cantidad_descontar)
                        costo_ext += (item.costo_cup * cantidad_descontar)

                    costos.append(item.costo_cup)
                    cantidad_descontar = 0
                    if item.cantidad_actual == 0:
                        item.activo = False
                    break
                else:
                    cantidad_descontar -= item.cantidad_actual

                    if item.lote_auditable:
                        monto_ext += (item.producto.precio_venta * item.cantidad_actual)
                        costo_ext += (item.costo_cup * item.cantidad_actual)

                    item.cantidad_actual = 0
                    item.activo = False
                    costos.append(item.costo_cup)
                    item.save()

            if len(costos) >0:costo = sum(costos)/len(costos)
            else:costo = 0.0

            if solicitud.venta.ganancia == None: solicitud.venta.ganancia = 0
            solicitud.venta.ganancia += (solicitud.venta.monto - (costo * solicitud.cantidad))            
            solicitud.venta.monto_ext = monto_ext
            solicitud.venta.costo_ext = costo_ext
            solicitud.venta.save()
            solicitud.activo = False
            solicitud.save()

        return redirect("SolicitudesPv")
    
@method_decorator(login_required, name='dispatch')
@method_decorator(punto_venta_required, name='dispatch')
class CerrarCuenta(View):
    def post(self,request,cuenta_id,*args,**kwargs):
        try:
            cuenta = Cuenta.objects.get(id = cuenta_id)
            ventas = Venta.objects.filter(cuenta=cuenta)

            if len(ventas) == 0:
                cuenta.delete()
            else:
                cuenta.abierta = False
                cuenta.save()

        except Exception as e:
            print("Error en Cerrar cuenta",e)

        return redirect("CuentasPuntoVenta")

@method_decorator(login_required, name='dispatch')
class AddTrabajador(View):
    def get(self,request,*args,**kwargs):
        punto_venta=request.user.punto_venta()
        users = UserAccount.objects.filter( Q(puntos_venta__id=punto_venta.id) ).exclude( Q(id=request.user.id) )

        users_extra = Turno.objects.get(user=request.user,punto_venta=punto_venta,fin=None).users_extra.all()

        context = {"users":users,"users_extra":users_extra}

        return render(request,'punto_venta/add_trabajador.html',context)
    
    def post(self,request,*args,**kwargs):
        data = request.POST
        turno = Turno.objects.get(id=data["turno-id"])

        if data["user-id-add"] != "":
            turno.users_extra.add(UserAccount.objects.get(id=data["user-id-add"]))
            turno.save()

        elif data["user-id-delete"] != "":
            turno.users_extra.remove(UserAccount.objects.get(id=data["user-id-delete"]))
            turno.save()

        return redirect(data["redirect"])

def update_cuenta(request):
    if not request.user.is_authenticated:
        logout(request)
        return redirect('login')
    if request.method == 'POST':
        nombre = request.POST["nombre"]
        cuenta_id = request.POST["cuenta_id"]

        cuenta = Cuenta.objects.get(id=cuenta_id)
        cuenta.nombre = nombre
        cuenta.save()
        return redirect(str(request.build_absolute_uri()).replace("/update-cuenta/","/cuentas-punto-venta/"))
    else:
        return redirect("CuentasPuntoVenta")

@method_decorator(login_required, name='dispatch')
class NotasPvView(View):
    def get(self,request,*args,**kwargs):

        punto_venta=request.user.punto_venta()
        cocinas = punto_venta.puntos_venta_cocina.all()
        notas = []
        for cocina in cocinas:
            notas += list(NotaCocina.objects.filter(cocina_id = f"C-{cocina.id}"))
            
        return render(request,'punto_venta/notas.html',{"notas":notas})
 
def getNotificacionPv(request):
    if request.method == 'GET':
        
        messages_list = []
        pv_id = int(request.GET["pv_id"])
        turno = Turno.objects.get(punto_venta__id=pv_id,fin=None)
        if turno.user == request.user:        
            stock = StockPuntoVenta.objects.filter(transferencia__receptor_id = f"PV-{pv_id}",cantidad_recibida__isnull=True,
                                                transferencia__mensaje_cancelacion__isnull=True)

            if stock.exists():
                messages_list.append(f"{len(stock)} transferencias pendientes por confirmación")

        
        solicitudes = SolicitudCocina.objects.filter(venta__cuenta__punto_venta__id = pv_id, venta__cuenta__user = request.user, transferido = True, activo = True)
        if solicitudes.exists():
            messages_list.append(f"{len(solicitudes)} solicitudes  a cocina listas")

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

class ErrorView(View):
    def get(self,request,*args,**kwargs):
        return redirect("logout")

class PreciosView(View):
    def get(self,request,*args,**kwargs):

        productos = Producto.objects.filter(is_compuesto=False).order_by("nombre")
        
        context = {"productos":productos}

        return render(request,'precios.html',context)
