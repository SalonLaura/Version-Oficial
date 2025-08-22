from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db.models import Sum

class PagoServicio(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.TextField(blank = False, null = False)
    monto = models.FloatField(default=0.0,blank = True, null = True)
    activo = models.BooleanField(default=True)

class Servicios(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.TextField(blank = False, null = False)
    descripcion = models.TextField(blank = True, null = True)
    pagos = models.ManyToManyField(PagoServicio)
    activo = models.BooleanField(default=True)
    
    def actividades(self):
        r =  []
        for pago in self.pagos.all():r.append(pago.nombre)
        return ', '.join(r)
    
    def is_delete(self):
        if UserAccount.objects.filter(pago_servicios = self).exists(): return False
        return True

"""class TrabajadorServicio(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.TextField(blank = False, null = False, unique=True)    
    imagen = models.ImageField(upload_to = 'usuario',null=True,blank=True)
    pago_909 = models.BooleanField(blank = False, null = False, default=False)
    activo = models.BooleanField(default=True)
    pago_servicios = models.ManyToManyField(Servicios)
    
    def rool(self) -> str:
        r =  []
        for pago in self.pago_servicios.all():r.append(pago.nombre)
        return "Trabajador de servicio (" + ', '.join(r) + ")"
    
    def is_delete(self) -> bool:
        return True
    
    def img(self):
        if not self.imagen:return "/static/images/men.jpg"

        if "/media/static/" in self.imagen.url: return self.imagen.name
        else:return self.imagen.url
"""

class Medida(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.TextField(blank = False, null = False, unique=True)
    abreviatura = models.TextField(blank = False, null = False)
    activo = models.BooleanField(default=True)


    """
    Peso
    1 libra (lb) = 16 onzas (oz) = 0,454 kilogramos (kg)
    1 kilogramo = 2,2 libras
    1 oz = 28,35 gramos (g)
    1 gramo = 0,035 oz
    Volumen
    1 galón (gal) = 4 cuartos (qt) = 3,785 litros (L)
    1 litro = 1,057 cuartos
    1 cuarto = 2 pintas (pt) = 0,946 litros
    1 pinta = 16 onzas líquidas (oz líquidas) = 0,473 litros
    1 taza = 8 oz = 16 cucharadas
    1 fl oz = 29,573 mililitros (mL)
    1 cucharada =1/2 oz = 3 cucharaditas
    """ 

    def is_edit(self) -> bool:
        if self.abreviatura in ["KG","LB","GR","OZ","U","GAL","L","ML"] : return False
        return True
        
    
    def is_delete(self) -> bool:
        if self.abreviatura in ["KG","LB","GR","OZ","U","GAL","L","ML"] : return False
        from kitchen.models import StockCocina
        
        if (not StockAlmacen.objects.filter(producto__medida=self,activo=True).exists() and 
            not StockPuntoVenta.objects.filter(producto__medida=self,activo=True).exists() and 
            not StockCocina.objects.filter(producto__medida=self,activo=True).exists()):
            return True
        return False
    
    def __str__(self) -> str:
        return str(self.nombre)

class Categoria(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.TextField(blank = False, null = False, unique=True)
    activo = models.BooleanField(default=True)
    
    def __str__(self) -> str:
        return str(self.nombre)
    
    def is_delete(self) -> bool:
        if (self.nombre != "SUBPRODUCTOS" and self.nombre != "MEDIOS BASICOS" and self.nombre != "SUBPRODUCTOS SALON" and
           self.nombre != "ACCESORIOS, PRENDAS Y OTROS" and not Producto.objects.filter(categoria=self,activo=True).exists()):
            return True
        return False

class Sub_Categoria(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.TextField(blank = False, null = False, unique=True)
    categoria = models.ForeignKey(Categoria,on_delete=models.SET_NULL,null=True,blank=True)
    activo = models.BooleanField(default=True)
    
    def __str__(self) -> str:
        return str(self.nombre)
    
    def is_delete(self) -> bool:
        if (self.nombre != "SUBPRODUCTOS" and self.nombre != "MEDIOS BASICOS" and self.nombre != "SUBPRODUCTOS SALON" and
           self.nombre != "ACCESORIOS, PRENDAS Y OTROS" and not Producto.objects.filter(categoria=self,activo=True).exists()):
            return True
        return False

class Producto(models.Model):
    id = models.AutoField(primary_key=True)
    imagen = models.ImageField(upload_to = 'producto', blank = True, null = True)
    codigo = models.TextField(blank = True, null = True)
    nombre = models.TextField(blank = False, null = False)
    descripcion = models.TextField(blank = True, null = True)
    
    precio_venta = models.FloatField(blank = True, null = True)
    precios_diferenciados = models.TextField(blank = True, null = True,default="")
    cantidades_ideales_pedidos = models.TextField(blank = True, null = True,default="")
    
    medida = models.ForeignKey(Medida,on_delete=models.SET_NULL,null=True,blank=True)
    categoria = models.ForeignKey(Categoria,on_delete=models.SET_NULL,null=True,blank=True)

    activo = models.BooleanField(default=True)
    is_compuesto = models.BooleanField(default=False)

    def precios(self):
        precios_list = []
        stocks = StockAlmacen.objects.filter(producto = self)

        for s in stocks:
            precios_list.append(
                {
                    "fecha":s.alta,
                    "cant":s.cantidad_inicial,
                    "costo":s.costo_cup,
                }
            )
        return precios_list


    def get_precios_diferenciados(self,pv_id=None):
        precios_diferenciados_return = []
        precios_diferenciados = self.precios_diferenciados.split("|")
        for pd in precios_diferenciados:
            precio_list = pd.split(":")
            if str(pv_id) == precio_list[0]:
                return precio_list[1]
            precios_diferenciados_return.append(precio_list)

        if pv_id==None: return precios_diferenciados_return
        return float(self.precio_venta)
    
    def get_cantidades_ideales_pedidos(self,pv_id=None):
        cantidades_ideales_pedidos_return = []
        cantidades_ideales_pedidos = self.cantidades_ideales_pedidos.split("|")
        for pd in cantidades_ideales_pedidos:
            precio_list = pd.split(":")
            if str(pv_id) == precio_list[0]:
                return precio_list[1]
            cantidades_ideales_pedidos_return.append(precio_list)

        if pv_id==None: return cantidades_ideales_pedidos_return
        return 0
        
    def get_cantidad_solicitud(self,id=None):
        cant_ideales = self.get_cantidades_ideales_pedidos(pv_id=id)
        if "C-" in str(id):
            existencia_pv = self.existencia_cocina(id.replace("C-",""))
        else:
            existencia_pv = self.existencia_pv(id)

        cantidad_solicitud = float(cant_ideales) - float(existencia_pv)
        if cantidad_solicitud < 0: return [0,existencia_pv]
        return [cantidad_solicitud,existencia_pv]

    """def is_compuesto(self) -> bool:
        if not self.productoCocinaFormula.filter(activo=True).exists():
            return False
        return True"""

    def is_delete(self) -> bool:
        from kitchen.models import StockCocina
        if (not StockAlmacen.objects.filter(producto=self,activo=True).exists() and 
            not StockPuntoVenta.objects.filter(producto=self,activo=True).exists() and 
            not StockCocina.objects.filter(producto=self,activo=True).exists()):
            return True
        return False

    def __str__(self) -> str:
        return str(self.nombre)
    
    def img(self):
        try:
            if "no_image.jpg" in self.imagen.url: return None
            if "/media/static/" in self.imagen.url: return self.imagen.name
            else:return self.imagen.url
        except:return ""

    def img_name(self):
        try:
            if "/media/static/" in self.imagen.url:
                return self.imagen.url.split("/")[-1].replace(".jpg","")
            else:return self.imagen.url
        except:return ""
    
    def existencia(self,almacen_id=None,lote=None) -> float:
        cantidad = 0.0
        if almacen_id != None:
            stock = StockAlmacen.objects.filter(producto=self,almacen__id=almacen_id,activo=True)
        else:
            stock = StockAlmacen.objects.filter(producto=self,activo=True)

        for s in stock:
            if s.cantidad_inicial != None and s.cantidad_inicial > 0 and s.cantidad_actual != None and s.cantidad_actual > 0 and (lote == None or lote == s.lote):
                cantidad += s.cantidad_actual
        
        return cantidad
    
    def existencia_pv(self,pv) -> float:
        cantidad = 0.0
        stock = StockPuntoVenta.objects.filter(producto=self,punto_venta__id=pv,activo=True,cantidad_actual__gt=0)

        for s in stock:
            if s.cantidad_inicial != None and s.cantidad_inicial > 0 and s.cantidad_actual != None and s.cantidad_actual > 0:
                cantidad += s.cantidad_actual
        ventas = Venta.objects.filter(cuenta__punto_venta__id = pv,ganancia = None,producto = self)
        cantidad -= float(sum(venta.cantidad for venta in ventas))

        return cantidad    
    
    def existencia_cocina(self,cocina) -> float:
        from kitchen.models import StockCocina
        total = 0
        sub_total = StockCocina.objects.filter(activo=True,cantidad_actual__gt=0, producto=self,cocina__id=cocina).aggregate(total=models.Sum('cantidad_actual'))["total"]
        if sub_total: total += sub_total
        return total
    
    def lote_asignar(self,almacen_id=None):
        if almacen_id != None : return StockAlmacen.objects.filter(producto = self,almacen__id=almacen_id,cantidad_actual__gt=0).first()
        return StockAlmacen.objects.filter(producto = self,cantidad_actual__gt=0).first()
    
    def existe_stock(self,almacen_id):
        formulas = self.productoCocinaFormula.all()
        
        for formula in formulas:
            for subproducto in formula.subproducto.all():
                suma_cantidad_actual = StockAlmacen.objects.filter(almacen__id=almacen_id, producto=subproducto.producto).aggregate(cantidad=Sum('cantidad_actual'))
                
                if not suma_cantidad_actual["cantidad"] or suma_cantidad_actual["cantidad"] < subproducto.cantidad:
                    return False

        return True
    
class Almacen(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.TextField(blank = False, null = False)
    direccion = models.TextField(blank = False, null = False)
    codigo = models.TextField(blank = False, null = False)
    activo = models.BooleanField(default=True) 
    is_audit = models.BooleanField(default=True) 

    def __str__(self) -> str:
        return self.nombre
    
    def is_delete(self) -> bool:
        from kitchen.models import StockCocina
        if (not StockAlmacen.objects.filter(almacen=self,activo=True).exists() and 
            not StockPuntoVenta.objects.filter(lote__almacen=self,activo=True).exists() and 
            not StockCocina.objects.filter(lote__almacen=self,activo=True).exists()):
            return True
        return False
    
    def productos(self):
        productos_return = []
        ids_agregados = []
        stock_almacen = StockAlmacen.objects.filter(almacen=self,baja = None).exclude(cantidad_actual=None)
        #print("Productos", stock_almacen)
        for prod in stock_almacen:
            existencia = prod.producto.existencia(prod.almacen.id,prod.lote)
            if existencia > 0:
                if prod.producto.id not in ids_agregados:
                    ids_agregados.append(prod.producto.id)
                    if prod.producto.precio_venta: 
                        importe = existencia * prod.producto.precio_venta
                        precio_venta = prod.producto.precio_venta
                    else: 
                        importe = existencia * prod.costo_cup
                        precio_venta = prod.costo_cup

                    productos_return.append({
                        "id":prod.producto.id,
                        "img":prod.producto.img(),
                        "codigo":prod.producto.codigo,
                        "categoria":prod.producto.categoria.nombre,
                        "nombre":prod.producto.nombre,
                        "medida":prod.producto.medida.abreviatura,
                        "lote_asignar":prod.id,
                        "precio_venta":precio_venta,
                        "existencia":existencia,
                        "importe":importe,
                    })
                else:
                    
                    if prod.producto.precio_venta: 
                        importe = existencia * prod.producto.precio_venta
                    else: 
                        importe = existencia * prod.costo_cup

                    index = ids_agregados.index(prod.producto.id)
                    productos_return[index]["existencia"] += existencia
                    productos_return[index]["importe"] += importe
        return productos_return

class GastosRecepcion(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.TextField(blank = True, null = True)
    monto = models.FloatField(default=0,blank = False, null = False)

    def __str__(self) -> str:
        return str(self.id) + "- " + self.nombre + " " + str(self.monto)
    
class InformeRecepcion(models.Model):
    id = models.AutoField(primary_key=True)
    fecha = models.DateTimeField(null=False,auto_now_add=True)
    #almacen = models.TextField(blank = True, null = True)
    almacen = models.ForeignKey(Almacen,on_delete=models.SET_NULL,null=True,blank=True,verbose_name="almacen")
    proveedor = models.TextField(blank = True, null = True)
    codigo = models.TextField(blank = True, null = True)
    factura = models.TextField(blank = True, null = True)
    conduce = models.TextField(blank = True, null = True)
    contrato = models.TextField(blank = True, null = True)
    manifiesto = models.TextField(blank = True, null = True)
    partida = models.TextField(blank = True, null = True)
    conoc_embarque = models.TextField(blank = True, null = True)
    orden_expedicion = models.TextField(blank = True, null = True)
    transportador = models.TextField(blank = True, null = True)
    carne_identidad = models.TextField(blank = True, null = True)
    chapa = models.TextField(blank = True, null = True)
    numero = models.TextField(blank = True, null = True)
    activo = models.BooleanField(blank = True, null = True)
    gastos = models.ManyToManyField(GastosRecepcion)
    date_confirm = models.DateTimeField(blank = True, null = True)
    
    user_recepcion = models.TextField(blank = True, null = True)
    user_confirmacion = models.TextField(blank = True, null = True)

    def monto_gastos(self):
        monto = 0
        for gasto in self.gastos.all():
            monto += gasto.monto
        return monto
    
    def monto(self):
        monto = 0
        for m in self.InformeRecepcion.all():
            monto += (m.costo_real() * m.cantidad_inicial)
        return monto

    def productos(self):
        return StockAlmacen.objects.filter(informe_recepcion = self)    
    
    def entradas_salidas(self):
        productos_list = []
        stokAlmacen = StockAlmacen.objects.filter(informe_recepcion = self,cantidad_actual__isnull = False)
        for s in stokAlmacen:
            productos_list.append({
                "producto":s.producto,
                "lote":s.lote,
                "cantidad_inicial":s.cantidad_inicial,
                "existencia":s.existencia,
                })          
        return productos_list

class PuntoVenta(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.TextField(blank = False, null = False)
    direccion = models.TextField(blank = False, null = False)
    codigo = models.TextField(blank = False, null = False)
    activo = models.BooleanField(default=True)
    edit_venta = models.BooleanField(default=True)

    
    pago_ganancia = models.FloatField(blank = True, null = True)
    pago_venta = models.FloatField(blank = True, null = True)
    pago_minutos = models.FloatField(blank = True, null = True)
    pago_fijo = models.FloatField(blank = True, null = True)
    pago_conciliado = models.TextField(blank = True, null = True)
        
    pago_asociado = models.FloatField(blank = True, null = True)
    

    def pago_conciliado1(self):
        if not self.pago_conciliado: return None
        pc = self.pago_conciliado.split("|")
        if len(pc) > 0:
            return pc[0]
        return None

    def pago_conciliado2(self):
        if not self.pago_conciliado: return None
        pc = self.pago_conciliado.split("|")
        if len(pc) > 0:
            return pc[1]
        return None

    def __str__(self) -> str:
        return str(self.nombre)
    
    def productos(self,sub = True,mb = True, form = True):
        productos_return = []
        ids_puestos = []

        stock_pv = StockPuntoVenta.objects.filter(
            punto_venta=self,
            activo = True,
            cantidad_inicial__isnull = False, 
            cantidad_actual__gt=0, 
            producto__precio_venta__isnull = False
            ).exclude(producto__categoria__nombre="SUBPRODUCTOS SALON"
            ).exclude(producto__categoria__nombre="ACCESORIOS, PRENDAS Y OTROS")
        if sub == False:
            stock_pv = stock_pv.exclude(producto__categoria__nombre = "SUBPRODUCTOS")
        if mb == False:
            stock_pv = stock_pv.exclude(producto__categoria__nombre = "MEDIOS BASICOS")
            
        if form == False:
            productos_subproductos = Formula.objects.values_list('subproductos__producto', flat=True).exclude(subproductos__producto=None)
            stock_pv = stock_pv.exclude(producto__in=productos_subproductos)


        for stock in stock_pv:
            if stock.producto.id not in ids_puestos:
                ids_puestos.append(stock.producto.id)

                existencia = stock.producto.existencia_pv(self.id)

                producto = stock.producto
                producto.cant_stock = existencia
                producto.get_precio = producto.get_precios_diferenciados(self.id)
                producto.importe = existencia * stock.producto.precio_venta
                productos_return.append(producto)

        return productos_return
    
    
    def is_delete(self) -> bool:
        if (not StockPuntoVenta.objects.filter(punto_venta=self,activo=True).exists()):
            return True
        return False
    
    def faltantes(self):
        faltante = []
        return faltante
        
    def abierto(self):
        if Turno.objects.filter(punto_venta=self,fin=None).exists():return True
        return False
 
    def last_turno(self):
        return Turno.objects.filter(punto_venta=self).last()

class UserAccountManager(BaseUserManager):
    def create_user(self, user, password=None, **extra_fields):
        if not user:
            raise ValueError('Users must have an email address')
        
        user_new = self.model(user=user, **extra_fields)

        user_new.set_password(password)
        user_new.save()
        return user_new

    def create_superuser(self, user, password, **extra_fields):
        superuser = self.create_user(user, password, **extra_fields)

        superuser.is_superuser = True
        superuser.is_staff = True
        superuser.super_permission = True
        superuser.save()
        return superuser

class UserAccount(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    user = models.TextField(blank = False, null = False, unique=True)
    imagen = models.ImageField(upload_to = 'usuario',null=True,blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    super_permission = models.BooleanField(default=False)
    balanc_permission = models.BooleanField(default=False)
    almacen_permission = models.BooleanField(default=False)    
    admin_permission = models.BooleanField(default=False)
    
    estudio_permission = models.BooleanField(default=False)
    responsable_estudio_permission = models.BooleanField(default=False)
    salon_permission = models.BooleanField(default=False)

    telefono = models.CharField(blank = True, null = True,max_length=200)
    ci = models.CharField(blank = True, null = True,max_length=11)

    puntos_venta = models.ManyToManyField(PuntoVenta)
    #almacenes = models.ManyToManyField(Almacen)
    #cocina = models.IntegerField(blank = True, null = True)

    pago_909 = models.BooleanField(blank = False, null = False, default=False)

    pago_servicios = models.ManyToManyField(Servicios)


    objects = UserAccountManager()

    USERNAME_FIELD = 'user'
    REQUIRED_FIELDS = []
    
    def punto_venta(self):
        turno = Turno.objects.filter(user = self,fin__isnull = True)
        if turno.exists():
            return turno.first().punto_venta
        
        turno = Turno.objects.filter(users_extra = self,fin__isnull = True)
        if turno.exists():
            return turno.first().punto_venta
        return None

    def cocina(self):
        from kitchen.models import Turno as TurnoCocina
        turno = TurnoCocina.objects.filter(user = self, fin = None)
        if turno.exists(): return turno.first().cocina
        return None
    
    def pago_acumulado(self, fin=None):
        monto = 0.0
        
        pagos = Pago.objects.filter(user_id=f"U-{self.id}",fecha_liquidacion__isnull = True)
        if fin != None: pagos = pagos.filter(fecha__lte = fin)
        for pago in pagos:
            if pago.monto == pago.liquidado:
                pago.fecha_liquidacion = timezone.now()
                pago.save()

            else:monto += (pago.monto - pago.liquidado)

        return monto
    
    def pagos(self, fin=None):
        pagos = Pago.objects.filter(user_id=f"U-{self.id}",fecha_liquidacion__isnull = True)
        if fin != None: pagos = pagos.filter(fecha__lte = fin)
        return pagos

    def monto_descontar(self, fin=None):
        monto = 0.0
        descuentos = Descuentos.objects.filter(user_id=f"U-{self.id}",fecha_liquidacion__isnull = True)
        if fin != None: descuentos = descuentos.filter(fecha__lte = fin)

        for descuento in descuentos:
            if descuento.monto == descuento.liquidado:
                descuento.fecha_liquidacion = timezone.now()
                descuento.save()

            else:monto += (descuento.monto - descuento.liquidado)

        return monto
    
    def descuentos(self, fin=None):
        descuentos = Descuentos.objects.filter(user_id=f"U-{self.id}",fecha_liquidacion__isnull = True)
        if descuentos != None: descuentos = descuentos.filter(fecha__lte = fin)
        return descuentos

    def monto_pagar(self, fin=None):
        pago_acumulado = self.pago_acumulado(fin)
        monto_descontar = self.monto_descontar(fin)

        monto = pago_acumulado - monto_descontar
        if monto < 0:
            monto = 0
        return monto
    

    
    def tag_id(self):
        return f"U-{self.id}"

    def __str__(self):
        return self.user.split(" (Borrado:")[0]
    
    def user_str(self):
        return self.user.split(" (Borrado:")[0]

    def has_perm(self,perm,obj = None):
        return True

    def has_mmodule_perms(self,app_label):
        return True
    
    def rool(self):
        if self.super_permission: return "Superusuario"
        if self.balanc_permission: return "Balancista"
        if self.almacen_permission: return "Almacenero"
        if self.admin_permission: return "Administrador"
        if self.salon_permission: return "Trabajador del salón"
        if self.estudio_permission: return "Gestor del estudio"
        if self.responsable_estudio_permission: return "Responsable de contratos del estudio"
        if self.pago_servicios.all().exists(): return self.pago_servicios.first().nombre
        
        if len(self.puntos_venta.all()) > 0:
            r =  []
            for a in self.puntos_venta.all():r.append(a.nombre)
            return ', '.join(r)
        
        elif self.users_access_cocina.all():
            cocinas = []
            for c in self.users_access_cocina.all():
                cocinas.append(c.nombre)
            return ",".join(cocinas)
            return "-cocina-"

    def img(self):
        if not self.imagen:return "/static/images/men.jpg"

        if "/media/static/" in self.imagen.url: return self.imagen.name
        else:return self.imagen.url


    def gestion_turnos(self):
        if self.super_permission or self.balanc_permission or self.admin_permission:
            puntos_venta =  PuntoVenta.objects.all()
            if len(puntos_venta) > 0:return True

        return False
    
    def is_delete(self) -> bool:
        from almacen.models import Turno as TurnoAlmacen
        from kitchen.models import Turno as TurnoCocina
        if (Turno.objects.filter(user=self,fin=None).exists() or
        TurnoAlmacen.objects.filter(user=self,fin=None).exists() or
        TurnoCocina.objects.filter(user=self,fin=None).exists()):
            return False
        return True

class Pago(models.Model):
    id = models.AutoField(primary_key=True)
    monto_original = models.FloatField(default=0,blank = False, null = False)
    monto = models.FloatField(default=0,blank = False, null = False)
    liquidado = models.FloatField(default=0,blank = False, null = False)
    descripcion = models.TextField(blank = True, null = True)
    user_id = models.CharField(blank = False, null = False,max_length=999)
    user_name = models.CharField(blank = False, null = False,max_length=999)
    fecha = models.DateTimeField(auto_now_add=True)
    fecha_liquidacion = models.DateTimeField(blank=True,null=True)
    
    def __str__(self) -> str:
        return str(self.user_id) + "  " + str(self.user_name) + "  " + str(self.monto)

class Descuentos(models.Model):
    id = models.AutoField(primary_key=True)
    monto_original = models.FloatField(default=0,blank = False, null = False)
    monto = models.FloatField(default=0,blank = False, null = False)
    liquidado = models.FloatField(default=0,blank = False, null = False)
    descripcion = models.TextField(blank = True, null = True)
    motivo = models.TextField(blank = True, null = True)
    user_id = models.CharField(blank = False, null = False,max_length=999)
    user_name = models.CharField(blank = False, null = False,max_length=999)
    fecha = models.DateTimeField(auto_now_add=True)
    fecha_liquidacion = models.DateTimeField(blank=True,null=True)
    
    def __str__(self) -> str:
        return str(self.user_id) + "  " + str(self.user_name) + "  " + str(self.monto)

class Turno(models.Model):
    id = models.AutoField(primary_key=True)
    punto_venta = models.ForeignKey(PuntoVenta,on_delete=models.CASCADE,null=False,blank=False,related_name="TurnoPuntoVenta")
    user = models.ForeignKey(UserAccount,on_delete=models.CASCADE,null=False,blank=False,related_name="User")
    inicio = models.DateTimeField(auto_now_add=True)
    fin = models.DateTimeField(blank = True, null = True)
    pagos = models.ManyToManyField(Pago,blank = True, null = True)
    users_extra = models.ManyToManyField(UserAccount,blank = True, null = True)
    
    recibido = models.TextField(blank = True, null = True)    
    monto_caja = models.FloatField(blank = True, null = True)
    monto_maquina = models.FloatField(blank = True, null = True)
    monto_puerta = models.FloatField(blank = True, null = True)
    monto_letra = models.TextField(blank = True, null = True)

    # Para sacer por turno de cocina la contabilidad
    monto = models.FloatField(default=0.0,blank = False, null = False)
    costo = models.FloatField(default=0.0,blank = False, null = False)
    
    monto_ext = models.FloatField(default=0.0,blank = False, null = False)
    costo_ext = models.FloatField(default=0.0,blank = False, null = False)

    
    
    def total_pagado(self,):
        try:
            return self.pagos.all().aggregate(total = models.Sum("monto_original"))["total"]
        except:
            return 0



    def recibo_efectivo(self):
        from caja.models import ReciboEfectivo
        re = ReciboEfectivo.objects.filter(origen=f"PV-{self.id}").first()
        return re
    
    def is_reopen(self):
        if Turno.objects.filter(punto_venta=self.punto_venta,fin__isnull=False).order_by("-fin").first() == self:
            return True
        return False
    
    def monto_total(self,):
        if self.monto_puerta: return self.monto_puerta + self.monto_caja
        return self.monto_caja
    
    def monto_total_venta_export(self):
        return self.monto_ext
    
        ventas = Venta.objects.filter(cuenta__turno = self,)
        monto = 0
        for venta in ventas:
            monto += venta.monto_ext        
        return monto
    
    # Para los informes de Estado de capital
    def coste_productos(self,all=True):
        if all:
            return self.costo
        return self.costo_ext
        
        costo = 0.0
        if all == True:
            ventas = Venta.objects.filter(cuenta__turno = self)
            for venta in ventas:
                costo += venta.coste_producto()
        else:
            ventas = Venta.objects.filter(cuenta__turno = self)
            for venta in ventas:
                costo += venta.costo_ext

        return costo
    
    def impuestos_ventas(self,all=False):
        monto = 0

        if all:
            monto += (self.monto *  0.1 + self.monto * 0.01)
        else:
            monto += (self.monto_ext *  0.1 + self.monto_ext * 0.01)

        return monto
        ventas = Venta.objects.filter(cuenta__turno = self,)
        for venta in ventas:
            if all == False:
                monto += (venta.monto_ext * 0.1 + venta.monto_ext * 0.01) #+ (venta.monto_ext - venta.costo_ext)*0.35)
            else:
                monto += (venta.monto * 0.1 + venta.monto * 0.01) #+ (venta.monto - (venta.monto - venta.ganancia))*0.35)
    
    def impuestos_ventas_list(self,all=False):

        if all:
            imp_01 = self.monto *  0.1
            imp_001 = self.monto * 0.01
            imp_035 = (self.monto - self.costo)*0.35
        else:
            imp_01 = self.monto_ext *  0.1
            imp_001 = self.monto_ext * 0.01
            imp_035 = (self.monto_ext - self.costo_ext)*0.35
        return [imp_01,imp_001,imp_035]

        '''ventas = Venta.objects.filter(cuenta__turno = self,)
        imp_01 = 0
        imp_001 = 0
        imp_035 = 0
        for venta in ventas:
            imp_01 += venta.monto_ext * 0.1
            imp_001 += venta.monto_ext * 0.01
            imp_035 += (venta.monto_ext - venta.costo_ext)*0.35'''
        


    
    def duracion_turno(self):
        time_diff = self.fin - self.inicio
        days = time_diff.days
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if days > 0 :f"{days} dias, {hours} horas y {minutes} minutos."
        return f"{hours} horas y {minutes} minutos."
    
    def pago_ganancia(self,ganancia):
        if self.punto_venta.pago_ganancia: return round(self.punto_venta.pago_ganancia * ganancia * 0.01,2)
        return None
    
    def pago_venta(self,monto_total):
        if self.punto_venta.pago_venta: return round(self.punto_venta.pago_venta * monto_total * 0.01,2)
        return None
    
    def pago_minutos(self):
        if self.punto_venta.pago_minutos:
            time_diff = self.fin - self.inicio
            duration_minutes = int(time_diff.total_seconds() / 60)
            return round(self.punto_venta.pago_minutos * duration_minutes,2)
        return None

    def pago_fijo(self):
        if self.punto_venta.pago_fijo:return round(self.punto_venta.pago_fijo,2)
        return None
    
    def pago_conciliado(self,monto_total):
        if self.punto_venta.pago_conciliado:
            conciliacion = self.punto_venta.pago_conciliado.split("|")
            if float(conciliacion[0]) < monto_total:            
                return round((monto_total - float(conciliacion[0])) * float(conciliacion[1]) * 0.01,2)
            else: return 0.0
        return None
    
    def pago_total(self,ganancia,monto):
        total = 0.0 
        pago_ganancia = self.pago_ganancia(ganancia)
        pago_venta = self.pago_venta(monto)
        pago_minutos = self.pago_minutos()
        pago_fijo = self.pago_fijo()
        pago_conciliado = self.pago_conciliado(monto)
        
        if pago_ganancia: total += pago_ganancia
        if pago_venta: total += pago_venta
        if pago_minutos: total += pago_minutos
        if pago_fijo: total += pago_fijo
        if pago_conciliado: total += pago_conciliado

        return round(total,2)

class Cuadre(models.Model):
    id = models.AutoField(primary_key=True)
    turno = models.ForeignKey(Turno,on_delete=models.CASCADE,null=False,blank=False,related_name="Turno")
    producto = models.ForeignKey(Producto,on_delete=models.CASCADE,null=False,blank=False,related_name="Cuadre_Producto")
    recibido = models.FloatField(default=0.0,blank = False, null = False)
    entregado = models.FloatField(blank = True, null = True, default=0.0)
    bajas = models.FloatField(blank = True, null = True, default=0.0)

    recibido_ext = models.FloatField(blank = False, null = False, default=0.0)
    entregado_ext = models.FloatField(blank = True, null = True, default=0.0)


    def cantidad_retirada(self) -> float:
        cant = 0.0
        transformaciones = StockPuntoVenta.objects.filter(transformacion__turno_id=f"PV-{self.turno.id}",
                                                          transformacion__formula__producto_inicial = self.producto)
        for s in transformaciones:
            formula = s.transformacion.formula
            c = (s.cantidad_inicial * formula.cantidad_inicial)/formula.cantidad_final
            cant += c
        return cant
    
    def cantidad_retirada_ext(self) -> float:
        cant = 0.0
        transformaciones = StockPuntoVenta.objects.filter(transformacion__turno_id=f"PV-{self.turno.id}",
                                                          transformacion__formula__producto_inicial = self.producto, lote_auditable = True)
        for s in transformaciones:
            formula = s.transformacion.formula
            c = (s.cantidad_inicial * formula.cantidad_inicial)/formula.cantidad_final
            cant += c
        return cant


    def cantidad_insertada_producto(self) -> float:
        cant = 0.0
        transferencias = Transferencia.objects.filter(turno_id=f"PV-{self.turno.id}",)
        for transferencia in transferencias:
            stock = StockPuntoVenta.objects.filter(transferencia=transferencia,producto = self.producto)
            for s in stock:
                cant += s.cantidad_inicial
        
        transformaciones = StockPuntoVenta.objects.filter(transformacion__turno_id=f"PV-{self.turno.id}",producto = self.producto)
        for s in transformaciones:
            cant += s.cantidad_inicial
         
        
        from kitchen.models import SolicitudCocina
        solicitudes = SolicitudCocina.objects.filter(venta__cuenta__turno=self.turno,venta__producto = self.producto, activo=False)
        for s in solicitudes:
            cant += s.cantidad

        return cant
    
    def cantidad_insertada_producto_ext(self) -> float:
        cant = 0.0
        transferencias = Transferencia.objects.filter(turno_id=f"PV-{self.turno.id}",)        
        for transferencia in transferencias:
            stock = StockPuntoVenta.objects.filter(models.Q(transferencia=transferencia) & models.Q(producto = self.producto) & (models.Q(lote__almacen__is_audit = True) | models.Q(lote_auditable = True)))
            for s in stock:
                cant += s.cantidad_inicial
        
        transformaciones = StockPuntoVenta.objects.filter(transformacion__turno_id=f"PV-{self.turno.id}",lote__almacen__is_audit = True,producto = self.producto)
        for s in transformaciones:
            cant += s.cantidad_inicial
        
        from kitchen.models import SolicitudCocina
        solicitudes = SolicitudCocina.objects.filter(venta__cuenta__turno=self.turno, activo=False)
        for s in solicitudes:
            cant += s.venta.cantidad_ext()

        return cant

    def cantidad_vendida(self) -> float:
        cant = 0.0
        ventas = Venta.objects.filter(cuenta__turno = self.turno,producto=self.producto)
        if not ventas.exists():  return 0.0
        for venta in ventas:
            cant += venta.cantidad
        return cant
    
    def cantidad_vendida_ext(self) -> float:
        cant = 0.0
        ventas = Venta.objects.filter(cuenta__turno = self.turno,producto=self.producto)
        if not ventas.exists():  return 0.0
        for venta in ventas:
            cant += venta.cantidad_ext()
        return cant
    
    def costo_vendido(self) -> float:
        monto = 0.0
        ventas = Venta.objects.filter(cuenta__turno = self.turno,producto=self.producto)
        if not ventas.exists():  return 0.0
        for venta in ventas:
            monto += venta.costo()
        return monto
    
    def costo_vendido_ext(self) -> float:
        monto = 0.0
        ventas = Venta.objects.filter(cuenta__turno = self.turno,producto=self.producto)
        if not ventas.exists():  return 0.0
        for venta in ventas:
            monto += venta.costo_ext
        return monto
    
    def monto_vendido(self) -> float:
        monto = 0.0
        ventas = Venta.objects.filter(cuenta__turno = self.turno,producto=self.producto)
        if not ventas.exists():  return 0.0
        for venta in ventas:
            monto += venta.monto
        return monto
    
    def monto_vendido_ext(self) -> float:
        monto = 0.0
        ventas = Venta.objects.filter(cuenta__turno = self.turno,producto=self.producto)
        if not ventas.exists():  return 0.0
        for venta in ventas:
            monto += venta.monto_ext
        return monto



    def existencia(self) -> float:
        return self.producto.existencia_pv(self.turno.punto_venta.id)

class Nota(models.Model):
    id = models.AutoField(primary_key=True)
    cantidad = models.IntegerField(default=0,blank = False, null = False)
    monto = models.FloatField(default=0,blank = False, null = False)
    motivo = models.TextField(blank = True, null = True)
    cuadre = models.ForeignKey(Cuadre,on_delete=models.SET_NULL,null=True,blank=True,related_name="NotaCuadre")
    fecha = models.DateTimeField(auto_now_add=True)
    
    def __str__(self) -> str:
        return str(self.motivo)
    
class Transferencia(models.Model):
    id = models.AutoField(primary_key=True)
    emisor_id = models.TextField(blank = True, null = True)
    receptor_id = models.TextField(blank = True, null = True)

    entrega = models.TextField(blank = True, null = True)
    recibe = models.TextField(blank = True, null = True)
    autoriza = models.TextField(blank = True, null = True)

    turno_id = models.TextField(blank = True, null = True)

    alta = models.DateTimeField(auto_now_add=True)
    date_confirm = models.DateTimeField(blank = True, null = True)
    
    cant_elaborar = models.FloatField(blank = True, null = True)

    activo = models.BooleanField(default=True, blank = True, null = True)
    mensaje_cancelacion = models.TextField(blank = True, null = True)
    
    user_transfiere = models.TextField(blank = True, null = True)
    user_confirmacion = models.TextField(blank = True, null = True)

    def __str__(self) -> str:
        return str(self.id) + " - " + str(self.emisor_id) + " - " + str(self.receptor_id)
        
    def emisor(self):
        try:
            if "A-" in self.emisor_id:return Almacen.objects.get(id = self.emisor_id.replace("A-",""))
            if "PV-" in self.emisor_id:return PuntoVenta.objects.get(id = self.emisor_id.replace("PV-",""))
            if "C-" in self.emisor_id:return self.emisor_id
        except: return None

    def receptor(self):
        try:
            if "A-" in self.receptor_id:return Almacen.objects.get(id = self.receptor_id.replace("A-",""))
            if "PV-" in self.receptor_id:return PuntoVenta.objects.get(id = self.receptor_id.replace("PV-",""))
            if "C-" in self.receptor_id:return self.cocinaTransferencia.all()[0].cocina
            if "bolsa-estudio" in self.receptor_id:
                return {
                    "nombre":"Estudio",
                    "direccion":"-",
                    "codigo":"-",
                }
            if "U-" in self.receptor_id:
                receptor = UserAccount.objects.get(id = self.receptor_id.replace("U-",""))
                if receptor.salon_permission:
                    receptor.nombre = f"{receptor.user} (Salón)"
                else:
                    receptor.nombre = receptor.user
                receptor.direccion = "-"
                receptor.codigo = "-"
                return receptor
        except:
            return
        
    def stock(self) :
        if "PV-" in self.receptor_id:return StockPuntoVenta.objects.filter(transferencia = self)
        elif "C-" in self.receptor_id:return self.cocinaTransferencia.all()
        elif "A-" in self.receptor_id:return StockAlmacen.objects.filter(transferencia = self)
        elif "U-" in self.receptor_id:return StockUsuario.objects.filter(transferencia = self)
        elif "bolsa-estudio" in self.receptor_id:
            from estudio.models import StockEstudio
            return StockEstudio.objects.filter(transferencia = self)
    
    def stock_transferido(self):
        stock = []
        if "PV-" in self.receptor_id:stock = StockPuntoVenta.objects.filter(transferencia = self,cantidad_recibida = None)
        elif "C-" in self.receptor_id:stock = self.cocinaTransferencia.filter(cantidad_recibida = None)
        elif "U-" in self.receptor_id:stock = StockUsuario.objects.filter(transferencia = self,cantidad_recibida = None)
        
        elif "bolsa-estudio" in self.receptor_id:
            from estudio.models import StockEstudio
            return StockEstudio.objects.filter(transferencia = self,cantidad_recibida = None)
        
        elif "C-" in self.emisor_id:stock = []
        return stock
    
    def cant_transferido(self):
        stock = []
        if "PV-" in self.receptor_id:stock = StockPuntoVenta.objects.filter(transferencia = self)
        elif "C-" in self.receptor_id:stock = self.cocinaTransferencia.all()
        elif "bolsa-estudio" in self.receptor_id:
            from estudio.models import StockEstudio
            return StockEstudio.objects.filter(transferencia = self)
        
        elif "C-" in self.emisor_id:stock = []
        return len(stock)

    def stock_pendiente(self):
        if "PV-" in self.receptor_id: x = StockPuntoVenta.objects.filter(transferencia = self,activo = None)
        elif "C-" in self.receptor_id: x = self.cocinaTransferencia.all()
        elif "bolsa-estudio" in self.receptor_id:
            from estudio.models import StockEstudio
            return StockEstudio.objects.filter(transferencia = self,activo = None)
        return x
    
    def entradas_salidas(self):
        productos_list = []
        stokAlmacen = StockAlmacen.objects.filter(transferencia = self,cantidad_actual__isnull = False)
        for s in stokAlmacen:
            productos_list.append({
                "producto":s.producto,
                "lote":s.lote,
                "cantidad_inicial":s.cantidad_inicial,
                "existencia":s.existencia,
                "destino":"",
                "existencia_receptor":s.existencia_receptor,
                })
        stockPuntoVenta = StockPuntoVenta.objects.filter(transferencia = self,cantidad_actual__isnull = False)
        for s in stockPuntoVenta:
            productos_list.append({
                "producto":s.producto,
                "lote":s.lote.lote,
                "cantidad_inicial":s.cantidad_inicial,
                "existencia":s.existencia,
                "destino":s.punto_venta.nombre,
                })
            
        stockCocina = self.cocinaTransferencia.filter(cantidad_actual__isnull = False)
        for s in stockCocina:
            productos_list.append({
                "producto":s.producto,
                "lote":s.lote.lote,
                "cantidad_inicial":s.cantidad_inicial,
                "existencia":s.existencia,
                "destino":s.cocina.nombre,
                })
            
        return productos_list
   
class FormulaTransformacion(models.Model):
    id = models.AutoField(primary_key=True)
    producto_inicial = models.ForeignKey(Producto,on_delete=models.CASCADE,null=False,blank=False,related_name="producto_transformado_inicial")
    cantidad_inicial = models.FloatField(default=0.0,blank = False, null = False)
    producto_final = models.ForeignKey(Producto,on_delete=models.CASCADE,null=False,blank=False,related_name="producto_transformado_final")
    cantidad_final = models.FloatField(blank = True, null = True)
    activo = models.BooleanField(blank = False, null = False, default = True)

    def is_delete(self) -> bool:
        return True
    
class StockAlmacen(models.Model):
    id = models.AutoField(primary_key=True)
    almacen = models.ForeignKey(Almacen,on_delete=models.CASCADE,null=True,blank=True,verbose_name="almacen")
    producto = models.ForeignKey(Producto,on_delete=models.CASCADE,null=True,blank=True,verbose_name="producto_almacen")

    lote = models.TextField(blank = False, null = False)
    costo_cup = models.FloatField(default=0.0,blank = False, null = False)
    gasto = models.FloatField(default=0.0,blank = True, null = True)

    existencia = models.FloatField(blank = True, null = True)# Para el emior
    existencia_receptor = models.FloatField(blank = True, null = True)# Para el receptor

    cantidad_factura = models.FloatField(default=0.0,blank = False, null = False)
    cantidad_inicial = models.FloatField(blank = True, null = True)
    cantidad_actual = models.FloatField(blank = True, null = True)
    
    vencimiento = models.DateField(blank = True, null=True)

    alta = models.DateTimeField(auto_now_add=True)  
    baja = models.DateTimeField(blank = True, null=True)

    informe_recepcion = models.ForeignKey(InformeRecepcion,on_delete=models.SET_NULL,null=True,blank=True,related_name="InformeRecepcion")
    transferencia = models.ForeignKey(Transferencia,on_delete=models.CASCADE,null=True,blank=True,related_name="TransferenciaAlmacen")
    transformacion = models.ForeignKey(FormulaTransformacion,on_delete=models.SET_NULL,null=True,blank=True,related_name="TransformacionAlmacen")

    activo = models.BooleanField(blank = True, null = True)

    def destino(self):
        return self.almacen

    def operacion(self):
        if self.informe_recepcion: return "Informe de recepción"
        if self.transformacion: return "Transformación"
        if self.transferencia: return "Transferencia"

    def type_(self) -> str:
        return "StockAlmacen"

    def __str__(self) -> str:
        return str(self.producto) + " (Lote:" + self.lote + ") " + " - " + str(self.costo_cup) + " CUP"
    
    def existencia_almacen(self) -> float:
        existenca =  self.producto.existencia(self.almacen.id,None)
        return existenca
        
    def existencia_almacen_emisor(self) -> float:
        total = StockAlmacen.objects.filter(producto = self.producto,
                                           almacen__id = self.transferencia.emisor_id.replace("A-",""),
                                           cantidad_actual__gt=0,
                                           activo = True
                                        ).aggregate(total=Sum('cantidad_actual'))['total']
        if total == None: return 0.0
        return total
    
    def costo_real(self):
        costo = self.costo_cup 
        if self.gasto: costo += self.gasto
        return costo
    
    def importe_inicial(self) -> str:
        """if self.producto.precio_venta:
            return self.producto.precio_venta * self.cantidad_inicial
        else:"""
        return self.costo_cup * self.cantidad_inicial
    
    def importe_actual(self) -> str:
        return self.producto.precio_venta * self.cantidad_actual
    
    def ganancia_dinero(self):
        if self.producto.precio_venta:
            return self.producto.precio_venta - self.costo_real()
        else:
            return 0.0
    
    def ganancia_porciento(self) -> str:
        if self.producto.precio_venta == 0.0: return 0.0
        
        if self.producto.precio_venta:
            return round(((self.producto.precio_venta - self.costo_real()) * 100 ) / self.producto.precio_venta,2)
        else:
            return 0.0
        
    def importe_remitido(self) -> float:
        return self.cantidad_factura * self.costo_cup
    
    def importe_recibido(self) -> float:
        if self.cantidad_inicial:
            return self.cantidad_inicial * self.costo_cup
        return None
    
    def cantidad_remitida(self) -> float:
        return self.cantidad_factura
    
    def cantidad_recibida(self) -> float:
        return self.cantidad_inicial

class Transformacion(models.Model):
    id = models.AutoField(primary_key=True)
    turno_id = models.TextField(blank = True, null = True)
    fecha = models.DateTimeField(auto_now_add=True)
    formula = models.ForeignKey(FormulaTransformacion,on_delete=models.CASCADE)

class StockPuntoVenta(models.Model):
    id = models.AutoField(primary_key=True)
    punto_venta = models.ForeignKey(PuntoVenta,on_delete=models.CASCADE,null=False,blank=False,related_name="PuntoVentaStock")
    producto = models.ForeignKey(Producto,on_delete=models.CASCADE,null=False,blank=False,related_name="ProductoStock")
    lote = models.ForeignKey(StockAlmacen,on_delete=models.CASCADE,null=True,blank=True,related_name="Almacen")
    lote_auditable = models.BooleanField(blank = True, null = True, default=True)
    transferencia = models.ForeignKey(Transferencia,on_delete=models.CASCADE,null=True,blank=True,related_name="Transferencia")
    transformacion = models.ForeignKey(Transformacion,on_delete=models.CASCADE,null=True,blank=True,related_name="ProductoTransformado")

    costo_produccion = models.FloatField(blank = True, null = True)
    existencia = models.FloatField(blank = True, null = True)
    cantidad_remitida = models.FloatField(blank = True, null = True)
    cantidad_recibida = models.FloatField(blank = True, null = True)

    cantidad_inicial = models.FloatField(blank = True, null = True)
    cantidad_actual = models.FloatField(blank = True, null = True)

    alta = models.DateTimeField(auto_now_add=True)

    activo = models.BooleanField(blank = True, null = True, default=True)

    def operacion(self):
        return "Transferencia"

    def destino(self):
        return self.punto_venta

    def type_(self) -> str:
        return "StockPuntoVenta"
    
    def __str__(self) -> str:
        return str(self.id) + " - " + str(self.producto)
    
    def existencia_almacen_emisor(self) -> float:
        return StockAlmacen.objects.filter(producto = self.producto,
                                           almacen__id = self.transferencia.emisor_id.replace("A-",""),
                                           cantidad_actual__gt=0,
                                           activo = True
                                        ).aggregate(total=Sum('cantidad_actual'))['total']
    
    def costo_cup(self) -> float:
        if self.costo_produccion: return self.costo_produccion
        return self.lote.costo_cup
    
    def existencia_almacen(self) -> float:
        if not self.lote: return 0.0
        return self.producto.existencia(almacen_id=self.lote.almacen.id)

    def importe_remitido(self) -> float:
        return self.cantidad_remitida * self.costo_cup()
    
    def importe_recibido(self) -> float:
        try:
            if self.cantidad_recibida: return self.cantidad_recibida * self.producto.precio_venta
            return None
        except: 
            return None

    def ganancia_dinero(self):
        try:
            if self.lote and self.lote.producto.precio_venta:
                return self.lote.ganancia_dinero()
            elif self.costo_produccion:
                return self.producto.precio_venta - (self.costo_produccion/self.cantidad_inicial)
            return 0.0
        except: 
            return 0.0

    def ganancia_porciento(self) -> str:
        try:
            if self.lote and self.lote.producto.precio_venta:
                return self.lote.ganancia_porciento()
            elif self.costo_produccion:
                return round(((self.producto.precio_venta - self.costo_produccion) * 100 ) / self.producto.precio_venta,2)
            return 0.0
        except: 
            return 0.0

class StockBar(models.Model):
    id = models.AutoField(primary_key=True)
    punto_venta = models.ForeignKey(PuntoVenta,on_delete=models.CASCADE,null=False,blank=False,related_name="BarStock")
    producto = models.ForeignKey(Producto,on_delete=models.CASCADE,null=False,blank=False,related_name="ProductoBarStock")
    lote = models.ForeignKey(StockAlmacen,on_delete=models.CASCADE,null=True,blank=True,related_name="AlmacenBar")
    lote_auditable = models.BooleanField(blank = True, null = True, default=True)
    transferencia = models.ForeignKey(Transferencia,on_delete=models.CASCADE,null=True,blank=True,related_name="TransferenciaBar")
    transformacion = models.ForeignKey(Transformacion,on_delete=models.CASCADE,null=True,blank=True,related_name="ProductoTransformadoBar")

    costo_produccion = models.FloatField(blank = True, null = True)
    existencia = models.FloatField(blank = True, null = True)
    cantidad_remitida = models.FloatField(blank = True, null = True)
    cantidad_recibida = models.FloatField(blank = True, null = True)

    cantidad_inicial = models.FloatField(blank = True, null = True)
    cantidad_actual = models.FloatField(blank = True, null = True)

    alta = models.DateTimeField(auto_now_add=True)

    activo = models.BooleanField(blank = True, null = True, default=True)

    def operacion(self):
        return "TransferenciaBar"

    def destino(self):
        return self.punto_venta

    def type_(self) -> str:
        return "StockBar"
    
    def __str__(self) -> str:
        return str(self.id) + " - " + str(self.producto)
    
    def existencia_almacen_emisor(self) -> float:
        return StockAlmacen.objects.filter(producto = self.producto,
                                           almacen__id = self.transferencia.emisor_id.replace("A-",""),
                                           cantidad_actual__gt=0,
                                           activo = True
                                        ).aggregate(total=Sum('cantidad_actual'))['total']
    
    def costo_cup(self) -> float:
        if self.costo_produccion: return self.costo_produccion
        return self.lote.costo_cup
    
    def existencia_almacen(self) -> float:
        if not self.lote: return 0.0
        return self.producto.existencia(almacen_id=self.lote.almacen.id)

    def importe_remitido(self) -> float:
        return self.cantidad_remitida * self.costo_cup()
    
    def importe_recibido(self) -> float:
        try:
            if self.cantidad_recibida: return self.cantidad_recibida * self.producto.precio_venta
            return None
        except: 
            return None

    def ganancia_dinero(self):
        try:
            if self.lote and self.lote.producto.precio_venta:
                return self.lote.ganancia_dinero()
            elif self.costo_produccion:
                return self.producto.precio_venta - (self.costo_produccion/self.cantidad_inicial)
            return 0.0
        except: 
            return 0.0

    def ganancia_porciento(self) -> str:
        try:
            if self.lote and self.lote.producto.precio_venta:
                return self.lote.ganancia_porciento()
            elif self.costo_produccion:
                return round(((self.producto.precio_venta - self.costo_produccion) * 100 ) / self.producto.precio_venta,2)
            return 0.0
        except: 
            return 0.0


class Cuenta(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.TextField(blank = True, null = True)
    creacion = models.DateTimeField(auto_now_add=True)
    punto_venta = models.ForeignKey(PuntoVenta,on_delete=models.CASCADE,null=False,blank=False,related_name="Cuenta_PuntoVenta")   
    
    user = models.ForeignKey(UserAccount,on_delete=models.SET_NULL,null=True,blank=True,related_name="UserCuenta")
    turno = models.ForeignKey(Turno,on_delete=models.CASCADE,null=False,blank=False,related_name="Cuenta_Turno")
    abierta = models.BooleanField(default=True)

    def ventas(self,id=None):
        ventas_list = []
        monto_total = 0.0
        from kitchen.models import SolicitudCocina

        venta = self.Venta_Cuenta.all()
        for v in venta:
            monto_total += v.monto
            list_monto = str(v.monto).split(".")
            if len(list_monto[1]) == 1: 
                monto = f"{list_monto[0]}.{list_monto[1]}0"
            else:
                monto = f"{list_monto[0]}.{list_monto[1]}"

            if v.producto:
                if id == None or str(id) == str(v.producto.id):
                    formulas = v.producto.productoCocinaFormula.filter(activo=True)
                    if formulas.exists():
                        producto_id=f"FC-{v.producto.id}"
                        stock = 0
                        for formula in formulas:
                            cocinas_pv = self.punto_venta.puntos_venta_cocina.all()
                            for cocina in cocinas_pv:  
                                stock += formula.disponibilidad_cocina(cocina.id)
                    else:
                        producto_id = v.producto.id
                        stock = v.producto.existencia_pv(self.punto_venta.id)
                    ventas_list.append({
                        "img":v.producto.img(),
                        "cantidad":v.cantidad,
                        "trab_primario":v.trab_primario,
                        "venta_id":v.id,
                        "producto_id":producto_id,
                        "stock":stock,
                        "monto":monto,
                        "precio":v.producto.precio_venta,
                        "nombre":v.producto.nombre,
                        "codigo":v.producto.codigo,
                        "desc":v.producto.descripcion,
                        "hora":v.instante
                    })
            else:
                if id == None or id == f"FPV-{v.formula_id}":
                    formula = Formula.objects.get(id=v.formula_id)
                    disponibilidad = formula.disponibilidad_pv(self.punto_venta.id)
                    
                    img = f'<div id="images-id-FPV-{v.formula_id}" class="flex my-1 -space-x-3 rtl:space-x-reverse">'
                    for index,p in enumerate(formula.subproductos.all(),start=0):
                        if index + 1 <= 2:
                            img += f"<img class='w-6 h-6 border-2 border-white rounded-full dark:border-gray-800' src='{p.producto.img()}'>"

                    if len(formula.subproductos.all()) > 2:
                        img += f"<span class='flex items-center justify-center w-6 h-6 text-lg font-medium text-white bg-gray-400 border-2 border-white rounded-full hover:bg-gray-500 dark:border-gray-800'>+{len(formula.subproductos.all())-2}</span>"
                    img += "</div>"
                    
                    desc = ""
                    for p in formula.subproductos.all():
                        desc += f"</br>{p.producto.nombre} - {p.cantidad}{p.producto.medida.abreviatura}"
                    if formula.descripcion: desc += f"</br></br>{formula.descripcion}"

                    ventas_list.append({
                        "img":img,
                        "cantidad":v.cantidad,
                        "trab_primario":v.trab_primario,
                        "venta_id":v.id,
                        "producto_id":f"FPV-{v.formula_id}",
                        "stock":disponibilidad,
                        "monto":monto,
                        "precio":formula.precio_venta(),
                        "nombre":formula.nombre,
                        "desc":desc,
                        "hora":v.instante
                    })


        list_monto = str(monto_total).split(".")
        if len(list_monto[1]) == 1: 
            monto_total_money = f"{list_monto[0]}.{list_monto[1]}0"
        else:
            monto_total_money = f"{list_monto[0]}.{list_monto[1]}"
            
        return [ventas_list,monto_total,monto_total_money]

class Venta(models.Model):
    id = models.AutoField(primary_key=True)
    cuenta = models.ForeignKey(Cuenta,on_delete=models.CASCADE,null=False,blank=False,related_name="Venta_Cuenta")
    producto = models.ForeignKey(Producto,on_delete=models.CASCADE,null=True,blank=True,related_name="Venta_ProductoPuntoVenta")
    formula_id = models.TextField(blank = True, null = True)
    cantidad = models.FloatField(default=0.0,blank = False, null = False)
    monto = models.FloatField(default=0.0,blank = False, null = False)
    ganancia = models.FloatField(blank = True, null = True)
    
    monto_ext = models.FloatField(default=0.0,blank = False, null = False)
    costo_ext = models.FloatField(default=0.0,blank = False, null = False)

    instante = models.DateTimeField(auto_now_add=True, null = True)
    trab_primario = models.BooleanField(default=True)
    
    def cancelable(self):
        if not self.cuenta.punto_venta.edit_venta: return False
        if not self.producto_solicitado_cosina.all().exists(): return True
        elif self.producto_solicitado_cosina.filter(estado=None).exists():return True
        else:
            return False
    
    def formula(self):
        return Formula.objects.get(id=self.formula_id)

    def costo(self):
        if self.ganancia:return self.monto - self.ganancia
        return self.monto
    
    def cantidad_ext(self):
        if self.monto_ext > 0:
            return (self.monto_ext * self.cantidad) / self.monto
        return self.cantidad
        
    # Para los informes de Estado de capital
    def coste_producto(self):
        if self.producto_solicitado_cosina.all().exists():
            costo = 0
            for e in self.producto_solicitado_cosina.all():
                costo += e.costo
            return costo

        if self.ganancia:return self.monto - self.ganancia
        return self.monto
    

    def __str__(self) -> str:
        return str(self.producto) + "  " + str(self.monto) + "  " + str(self.cantidad)

class CantidadSubproducto(models.Model):
    id = models.AutoField(primary_key=True)
    producto = models.ForeignKey(Producto,on_delete=models.CASCADE,null=False,blank=False,related_name="CantidadSubproductoFormula")
    cantidad = models.FloatField(default=0.0,blank = False, null = False)

# Formula de venta, permite vender varios productos simultaneamente
class Formula(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.TextField(blank = False, null = False)
    descripcion = models.TextField(blank = True, null = True)
    #tipo = models.TextField(blank = True, null = True)
    #medida = models.ForeignKey(Medida,on_delete=models.SET_NULL,null=True,blank=True)
    pago = models.FloatField(default=0.0,blank = False, null = False)
    precio = models.FloatField(blank = True, null = True)

    subproductos = models.ManyToManyField(CantidadSubproducto)
    activo = models.BooleanField(blank = True, null = True,default = True)
    
    def __str__(self) -> str:
        return self.nombre
    
    def is_delete(self) -> bool:
        if (not Venta.objects.filter(formula_id=self.id,ganancia=None).exists()):
            return True
        return False
            
    def precio_venta(self) -> float:
        if self.precio: return self.precio
        return self.subproductos.all().aggregate(total=Sum('producto__precio_venta'))['total']
        
    def disponibilidad_pv(self,pv_id):
        subproductos = self.subproductos.all()
        cant = None
        for subproducto in subproductos:
            cantidad = 0.0
            stock = StockPuntoVenta.objects.filter(producto=subproducto.producto,punto_venta__id=pv_id,activo=True,cantidad_inicial__isnull = False,cantidad_actual__isnull = False)
            
            for s in stock:
                if s.cantidad_inicial > 0 and s.cantidad_actual > 0:
                    cantidad += s.cantidad_actual
            d = cantidad / subproducto.cantidad
            if cant == None:
                cant = d
            elif d < cant and d >= 0:
                cant = d
                
        cant_vendida = Venta.objects.filter(formula_id=self.id,ganancia = None).aggregate(total=Sum("cantidad"))["total"]
        if cant_vendida: cant -= cant_vendida
        return cant

    def medida(self):
        return "UNIDAD"

class AlertaAdmin(models.Model):
    id = models.AutoField(primary_key=True)
    tipo = models.BooleanField(blank = True, null = True) #None=Green , False=Orange, True=Red
    centro_costo = models.CharField(blank = True, null = True, max_length=80)
    motivo = models.TextField(blank = True, null = True)
    activo = models.BooleanField(blank = True, null = True,default = True)
    fecha = models.DateTimeField(auto_now_add=True)
    
    def __str__(self) -> str:
        return str(self.motivo)
    
    
    def origen(self) -> str:
        if "C-" in self.centro_costo:
            from kitchen.models import Cocina
            return "Cocina " +  Cocina.objects.get(id = self.centro_costo.replace("C-","")).nombre
        
        if "PV-" in self.centro_costo:
            return "Punto de venta " +  PuntoVenta.objects.get(id = self.centro_costo.replace("PV-","")).nombre
        
        if "A-all" == self.centro_costo:
            return "Almacenes"
        
        if "A-" in self.centro_costo:
            return "Almacen " +  Almacen.objects.get(id = self.centro_costo.replace("A-","")).nombre
        
        if "S-" in self.centro_costo:
            return "Salón"
        
        else:
            return self.centro_costo
            
class StockUsuario(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(UserAccount,on_delete=models.SET_NULL,null=True,blank=True,related_name="UserStock")
    producto = models.ForeignKey(Producto,on_delete=models.CASCADE,null=False,blank=False,related_name="ProductoStockUsuario")
    lote = models.ForeignKey(StockAlmacen,on_delete=models.CASCADE,null=True,blank=True,related_name="LoteStockUsuario")
    transferencia = models.ForeignKey(Transferencia,on_delete=models.CASCADE,null=True,blank=True,related_name="TransferenciaStockUsuario")
    
    lote_auditable = models.BooleanField(blank = True, null = True, default=True)
    existencia = models.FloatField(blank = True, null = True)
    cantidad_remitida = models.FloatField(blank = True, null = True)
    cantidad_recibida = models.FloatField(blank = True, null = True)

    cantidad_inicial = models.FloatField(blank = True, null = True)
    cantidad_actual = models.FloatField(blank = True, null = True)

    alta = models.DateTimeField(auto_now_add=True)  
    baja = models.DateTimeField(blank = True, null=True)
    
    activo = models.BooleanField(blank = True, null = True)

    
    def operacion(self):
        return "Transferencia"

    def destino(self):
        return {"nombre":f"Trabajador {self.user.user}"}

    def type_(self) -> str:
        return "Trabajador"
    
    def importe_recibido(self) -> float:
        if self.cantidad_inicial:return self.cantidad_inicial * self.lote.costo_cup
        return None

class ErrorReport(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.IntegerField(blank = False, null = False)
    error = models.TextField(blank = False, null = False)
    activo = models.BooleanField(blank = True, null = True,default = True)
    fecha = models.DateTimeField(auto_now_add=True)
    
class ConfigVar(models.Model):
    id = models.AutoField(primary_key=True)
    key = models.TextField(blank = False, null = False)
    value = models.TextField(blank = False, null = False)
