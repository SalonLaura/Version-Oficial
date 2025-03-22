from django.db import models
from django.utils import timezone
from .choices import categoria_choices
from bussiness.models import FormulaTransformacion, Medida, Pago, Producto, PuntoVenta, StockAlmacen, StockPuntoVenta, Transferencia, UserAccount, Venta


class Cocina(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.TextField(blank = False, null = False)
    direccion = models.TextField(blank = False, null = False)
    codigo = models.TextField(blank = False, null = False)
    users_access = models.ManyToManyField(UserAccount,related_name="users_access_cocina")
    puntos_venta = models.ManyToManyField(PuntoVenta,related_name="puntos_venta_cocina")
    categoria = models.CharField(max_length=12, choices=categoria_choices, default='si', verbose_name='Categoria_cocina')
    activo = models.BooleanField(default=True)
    porciento_cocinero = models.FloatField(blank = False, null = False, default= 0.0)
    pago_fijo_cocinero = models.FloatField(blank = False, null = False, default= 0.0)
    pago_fijo_ayudante = models.FloatField(blank = False, null = False, default= 0.0)

    def __str__(self) -> str:
        return self.nombre
        
    def is_delete(self) -> bool:
        if (not Turno.objects.filter(cocina=self,fin=None).exists() and 
            not StockProductoCompuestoCocina.objects.filter(turno__cocina=self,activo=True).exists() and 
            not StockCocina.objects.filter(cocina=self,activo=True).exists() and 
            not SolicitudCocina.objects.filter(cocina=self,activo=True).exists()):
            return True
        return False
    
    def puntos_venta_str(self):
        puntos_venta_list = self.puntos_venta.all() 
        nombres_puntos_venta = [pv.nombre for pv in puntos_venta_list]
        return ', '.join(nombres_puntos_venta)
    
    def productos_start_turno(self,turno=None):
        productos_return = []
        ids_puestos = []

        #stock_cocina = StockCocina.objects.filter(cocina=self,activo = True,cantidad_actual__gt=0)        
        # Obtén los IDs de los productos del Cuadre del turno dado
        ids_productos_cuadre = Cuadre.objects.filter(turno=turno).values_list('producto__id', flat=True)

        # Filtra los StockCocina cuyos productos estén en los IDs obtenidos
        stock_cocina = StockCocina.objects.filter(cocina=self, activo=True, producto__in=ids_productos_cuadre)


        for stock in stock_cocina:
            if stock.producto.id not in ids_puestos:
                ids_puestos.append(stock.producto.id)

                existencia = StockCocina.objects.filter(cocina=self,cantidad_actual__gt=0,producto=stock.producto).aggregate(total=models.Sum('cantidad_actual'))["total"]
                if not existencia: existencia = 0
                # Comentado para descontar al final del turno
                """if turno != None:
                    consumo = Consumo.objects.filter(turno=turno,producto=stock.producto).aggregate(total=models.Sum('cantidad'))["total"]
                    if consumo:existencia -= consumo
                    if existencia < 0:existencia = 0"""

                producto = stock.producto
                producto.id_filter = f"FC-{producto.id}"
                producto.cant_stock = existencia
                producto.importe = existencia * stock.costo_cup()
                producto.precio_venta = stock.precio_venta()
                productos_return.append(producto)

        stock_cocina = StockProductoCompuestoCocina.objects.filter(turno__cocina=self,activo = True,cantidad_actual__gt=0)
        for stock in stock_cocina:
            if stock.producto.id not in ids_puestos:
                ids_puestos.append(stock.producto.id)

                existencia = StockProductoCompuestoCocina.objects.filter(turno__cocina=self,activo = True,cantidad_actual__gt=0,producto=stock.producto).aggregate(total=models.Sum('cantidad_actual'))["total"]
                if turno != None:
                    consumo = Consumo.objects.filter(turno=turno,producto=stock.producto).aggregate(total=models.Sum('cantidad'))["total"]
                    if consumo:existencia -= consumo
                    if existencia < 0:existencia = 0
                
                producto = stock.producto
                producto.id_filter = f"SC-{producto.id}"
                producto.cant_stock = existencia
                producto.importe = existencia * stock.costo_cup
                producto.precio_venta = stock.precio_venta()
                productos_return.append(producto)

        return productos_return

    def kit_productos_start_turno(self,turno=None):        
        productos_return = []
        ids_puestos = []

        #stock_cocina = StockCocina.objects.filter(cocina=self,activo = True,cantidad_actual__gt=0)        
        # Obtén los IDs de los productos del Cuadre del turno dado
        ids_productos_cuadre = Cuadre.objects.filter(turno=turno).values_list('producto__id', flat=True)

        # Filtra los StockCocina cuyos productos estén en los IDs obtenidos
        stock_cocina = StockCocina.objects.filter(cocina=self, activo=True, producto__in=ids_productos_cuadre)

        for stock in stock_cocina:
            if stock.producto.id not in ids_puestos:
                ids_puestos.append(stock.producto.id)
                if(stock.objetivo ):                    
                    #prod_cantidad = CantidadSubproducto.objects.get(id = stock.objetivo.id)                    

                    existencia = StockCocina.objects.filter(cocina=self,cantidad_actual__gt=0,producto=stock.producto).aggregate(total=models.Sum('cantidad_actual'))["total"]
                    if not existencia: existencia = 0
                    # Comentado para descontar al final del turno
                    """if turno != None:
                        consumo = Consumo.objects.filter(turno=turno,producto=stock.producto).aggregate(total=models.Sum('cantidad'))["total"]
                        if consumo:existencia -= consumo
                        if existencia < 0:existencia = 0"""

                    producto = stock.producto
                    producto.id_filter = f"FC-{producto.id}"
                    producto.cant_stock = existencia
                    producto.importe = existencia * stock.costo_cup()
                    producto.precio_venta = stock.precio_venta()
                    producto.consumo = False
                    productos_return.append(producto)

                if(stock.consumo):   
                    existencia = StockCocina.objects.filter(cocina=self,cantidad_actual__gt=0,producto=stock.producto).aggregate(total=models.Sum('cantidad_actual'))["total"]
                    if not existencia: existencia = 0
                    # Comentado para descontar al final del turno
                    """if turno != None:
                        consumo = Consumo.objects.filter(turno=turno,producto=stock.producto).aggregate(total=models.Sum('cantidad'))["total"]
                        if consumo:existencia -= consumo
                        if existencia < 0:existencia = 0"""

                    producto = stock.producto
                    producto.id_filter = f"FC-{producto.id}"
                    producto.cant_stock = existencia
                    producto.importe = existencia * stock.costo_cup()
                    producto.precio_venta = stock.precio_venta()
                    producto.consumo = True
                    productos_return.append(producto)

        return productos_return

    def inventario_start_turno(self,turno=None):        
        
        inventario_return = []
        ids_puestos = []

        #stock_cocina = StockCocina.objects.filter(cocina=self, activo=True, cantidad_actual__gt=0, producto__categoria__nombre = "MEDIOS BASICOS")
        
        # Obtén los IDs de los productos del Cuadre del turno dado
        ids_inventario_cuadre = Cuadre.objects.filter(turno=turno).values_list('producto__id', flat=True)

        # Filtra los StockCocina cuyos productos estén en los IDs obtenidos
        stock_cocina = StockCocina.objects.filter(cocina=self, activo=True, producto__in=ids_inventario_cuadre, producto__categoria__nombre = "MEDIOS BASICOS")

        for stock in stock_cocina:
            if stock.producto.id not in ids_puestos:
                ids_puestos.append(stock.producto.id)

                existencia = StockCocina.objects.filter(cocina=self,cantidad_actual__gt=0,producto=stock.producto).aggregate(total=models.Sum('cantidad_actual'))["total"]
                if not existencia: existencia = 0
                # Comentado para descontar al final del turno
                """if turno != None:
                    consumo = Consumo.objects.filter(turno=turno,producto=stock.producto).aggregate(total=models.Sum('cantidad'))["total"]
                    if consumo:existencia -= consumo
                    if existencia < 0:existencia = 0"""

                producto = stock.producto
                producto.id_filter = f"FC-{producto.id}"
                producto.cant_stock = existencia
                producto.importe = existencia * stock.costo_cup()
                producto.precio_venta = stock.precio_venta()
                inventario_return.append(producto)        

        return inventario_return
            
    def productos(self,turno=None):
        productos_return = []
        ids_puestos = []

        stock_cocina = StockCocina.objects.filter(cocina=self,activo = True,cantidad_actual__gt=0)

        for stock in stock_cocina:
            if stock.producto.id not in ids_puestos:
                ids_puestos.append(stock.producto.id)

                existencia = StockCocina.objects.filter(cocina=self,cantidad_actual__gt=0,producto=stock.producto).aggregate(total=models.Sum('cantidad_actual'))["total"]
                # Comentado para descontar al final del turno
                """if turno != None:
                    consumo = Consumo.objects.filter(turno=turno,producto=stock.producto).aggregate(total=models.Sum('cantidad'))["total"]
                    if consumo:existencia -= consumo
                    if existencia < 0:existencia = 0"""

                producto = stock.producto
                producto.id_filter = f"FC-{producto.id}"
                producto.cant_stock = existencia
                producto.importe = existencia * stock.costo_cup()
                producto.precio_venta = stock.precio_venta()
                productos_return.append(producto)

        stock_cocina = StockProductoCompuestoCocina.objects.filter(turno__cocina=self,activo = True,cantidad_actual__gt=0)
        for stock in stock_cocina:
            if stock.producto.id not in ids_puestos:
                ids_puestos.append(stock.producto.id)

                existencia = StockProductoCompuestoCocina.objects.filter(turno__cocina=self,activo = True,cantidad_actual__gt=0,producto=stock.producto).aggregate(total=models.Sum('cantidad_actual'))["total"]
                if turno != None:
                    consumo = Consumo.objects.filter(turno=turno,producto=stock.producto).aggregate(total=models.Sum('cantidad'))["total"]
                    if consumo:existencia -= consumo
                    if existencia < 0:existencia = 0
                
                producto = stock.producto
                producto.id_filter = f"SC-{producto.id}"
                producto.cant_stock = existencia
                producto.importe = existencia * stock.costo_cup
                producto.precio_venta = stock.precio_venta()
                productos_return.append(producto)

        return productos_return

    def last_turno(self):
        return Turno.objects.all().last()

class Turno(models.Model):
    id = models.AutoField(primary_key=True)
    cocina = models.ForeignKey(Cocina,on_delete=models.CASCADE,null=False,blank=False,related_name="TurnoCocina")
    user = models.ForeignKey(UserAccount,on_delete=models.CASCADE,null=False,blank=False,related_name="UserTurnoCocina")
    ayudantes = models.ManyToManyField(UserAccount,blank = True, null = True,related_name="UserAyudanteCocina")
    inicio = models.DateTimeField(auto_now_add=True)
    fin = models.DateTimeField(blank = True, null = True)
    pagos = models.ManyToManyField(Pago,related_name="PagosTurnoCocina")
    

    # Para sacer por turno de cocina la contabilidad
    monto = models.FloatField(default=0.0,blank = False, null = False)
    costo = models.FloatField(default=0.0,blank = False, null = False)

    costo_ext = models.FloatField(default=0.0,blank = False, null = False)


    
    def total_pagado(self,):
        try:
            return self.pagos.all().aggregate(total = models.Sum("monto_original"))["total"]
        except:
            return 0


    
    def monto_ext(self,):
        try:
            p = ((self.costo_ext*100)/self.costo)/100
            return self.monto * p
        except:
            return 0

    
    def monto_total(self,):
        if self.monto_puerta: return self.monto_puerta + self.monto_caja
        return self.monto_caja

    def coste_productos(self,all=True):
        if all:
            return self.costo
        return self.costo_ext

    def impuestos_ventas(self,all=False):
        monto = 0

        if all:
            monto += (self.monto *  0.1 + self.monto * 0.01)
        else:
            monto += (self.monto_ext() *  0.1 + self.monto_ext() * 0.01)

        return monto

    def impuestos_ventas_list(self,all=False):

        if all:
            imp_01 = self.monto *  0.1
            imp_001 = self.monto * 0.01
            imp_035 = (self.monto - self.costo)*0.35
        else:
            imp_01 = self.monto_ext() *  0.1
            imp_001 = self.monto_ext() * 0.01
            imp_035 = (self.monto_ext() - self.costo_ext)*0.35
        return [imp_01,imp_001,imp_035]


    def duracion_turno(self):
        time_diff = self.fin - self.inicio
        days = time_diff.days
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if days > 0 :f"{days} dias, {hours} horas y {minutes} minutos."
        return f"{hours} horas y {minutes} minutos."
    

    def pago_fijo(self):
        if self.cocina.pago_fijo_cocinero:return round(self.cocina.pago_fijo_cocinero,2)
        return None
    
    def pago_fijo_ayudante(self):
        if self.cocina.pago_fijo_ayudante:return round(self.cocina.pago_fijo_ayudante,2)
        return 0.0
    
    def pago_total(self):
        total = 0.0 
        pago_fijo = self.pago_fijo()
        if pago_fijo: total += pago_fijo

        return round(total,2)
 
class Cuadre(models.Model):
    id = models.AutoField(primary_key=True)
    turno = models.ForeignKey(Turno,on_delete=models.CASCADE,null=False,blank=False,related_name="CuadreCocina")
    producto = models.ForeignKey(Producto,on_delete=models.CASCADE,null=False,blank=False,related_name="CuadreProducto")
    recibido = models.FloatField(default=0.0,blank = False, null = False)
    entregado = models.FloatField(blank = True, null = True, default=0.0)
    usado = models.FloatField(blank = True, null = True, default=0.0)
    bajas = models.FloatField(blank = True, null = True, default=0.0)
    
    def cantidad_insertada_producto(self) -> float:
        cant = 0.0
        transferencias = Transferencia.objects.filter(turno_id=f"C-{self.turno.id}",receptor_id=f"C-{self.turno.cocina.id}")
        for transferencia in transferencias:
            stock = StockCocina.objects.filter(transferencia=transferencia,producto = self.producto)
            for s in stock:
                cant += s.cantidad_inicial
        
        elaborado = StockProductoCompuestoCocina.objects.filter(turno=self.turno,producto=self.producto).order_by("-fecha_fabricacion").aggregate(total=models.Sum('cantidad_resultante'))["total"]
        if elaborado != None: cant += elaborado

        if self.turno.fin:
            elaborado = StockCocina.objects.filter(consumo__isnull=False,alta__range=[self.turno.inicio,self.turno.fin],producto=self.producto).order_by("-alta").aggregate(total=models.Sum('cantidad_inicial'))["total"]
        else:
            elaborado = StockCocina.objects.filter(consumo__isnull=False,alta__gte=self.turno.inicio,producto=self.producto).order_by("-alta").aggregate(total=models.Sum('cantidad_inicial'))["total"]
     
        if elaborado != None: cant += elaborado
        
        return cant


    def cantidad_retirada(self) -> float:
        cant = 0.0
        transferencias = Transferencia.objects.filter(turno_id=f"C-{self.turno.id}",emisor_id=f"C-{self.turno.cocina.id}")
        for transferencia in transferencias:
            stock = StockCocina.objects.filter(transferencia=transferencia,producto = self.producto)
            for s in stock:
                cant += s.cantidad_inicial
                
            stock = StockPuntoVenta.objects.filter(transferencia=transferencia,producto = self.producto)
            for s in stock:
                cant += s.cantidad_inicial
                
            stock = StockAlmacen.objects.filter(transferencia=transferencia,producto = self.producto)
            for s in stock:
                cant += s.cantidad_inicial

        return cant

    def existencia(self) -> float:
        total = 0
        sub_total = StockCocina.objects.filter(activo=True,cantidad_actual__gt=0, producto=self.producto,cocina=self.turno.cocina).aggregate(total=models.Sum('cantidad_actual'))["total"]
        if sub_total != None: total += sub_total
        sub_total = StockProductoCompuestoCocina.objects.filter(activo=True,cantidad_actual__gt=0, producto=self.producto,turno__cocina=self.turno.cocina).aggregate(total=models.Sum('cantidad_actual'))["total"]
        if sub_total != None: total += sub_total
        return total
    
    def cant_usado(self) -> float:
        cant = 0.0
        consumo = Consumo.objects.filter(turno=self.turno,producto=self.producto)
        for c in consumo:
            cant += c.cantidad
        return cant

class CantidadSubproducto(models.Model):
    id = models.AutoField(primary_key=True)
    producto = models.ForeignKey(Producto,on_delete=models.CASCADE,null=False,blank=False,related_name="CantidadSubproducto")
    cantidad = models.FloatField(default=0.0,blank = False, null = False)
    subgrupo = models.CharField(max_length=5, blank = True, null = True)
    medida = models.ForeignKey(Medida,on_delete=models.CASCADE,null=False,blank=False,related_name="MedidaSubproducto")

    def optional(self):
        if self.subgrupo == None: return False
        return True

    def __str__(self) -> str:
        return f"ID: {self.id}, Prod: {self.producto}, Cant: {self.cantidad}"

class GastosElaboracion(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.TextField(blank = True, null = True)
    monto = models.FloatField(default=0,blank = False, null = False)

class Formula(models.Model):
    id = models.AutoField(primary_key=True)
    producto = models.ForeignKey(Producto,on_delete=models.CASCADE,null=False,blank=False,related_name="productoCocinaFormula")
    subproducto = models.ManyToManyField(CantidadSubproducto)
    descripcion = models.TextField(blank = True, null = True)
    cantidad = models.FloatField(default=1.0,blank = False, null = False)
    
    pago_elaboracion_monto = models.FloatField(default=1.0,blank = False, null = False)
    pago_elaboracion_relacion = models.CharField(blank = False, null = False,max_length=1)

    gastos = models.ManyToManyField(GastosElaboracion, blank = True, null = True)

    cocinas = models.ManyToManyField(Cocina,related_name="cocinas_formula", blank = True, null = True)
    
    activo = models.BooleanField(blank = True, null = True,default = True)

    def subproducto_order(self):
        return list(self.subproducto.filter(subgrupo=None).order_by('subgrupo')) + list(self.subproducto.all().exclude(subgrupo=None).order_by('subgrupo'))
    
    def is_delete(self) -> bool:
        if (not StockCocina.objects.filter(producto=self.producto,activo=True).exists()):
            return True
        return False
    
    def __str__(self) -> str:
        return str(self.producto)

    def disponibilidad_almacen(self,almacen_id):
        subproductos = self.subproducto.filter(subgrupo=None)
        cant = None
        for subproducto in subproductos:
            d = subproducto.producto.existencia(almacen_id) / subproducto.cantidad
            
            if cant == None:
                cant = d
            elif d < cant and d >= 0:
                cant = d
        if cant != None: return cant
        return 0.0
    
    def disponibilidad_cocina(self,cocina_id,descuento = True, objetivo = False):
        subproductos = self.subproducto.filter(subgrupo=None)
        cant = None
        try:
            for subproducto in subproductos:
                cantidad = 0.0
                stock = StockCocina.objects.filter(producto=subproducto.producto,cocina__id=cocina_id,activo=True,cantidad_inicial__isnull = False,cantidad_actual__isnull = False)
                
                if objetivo:stock = stock.filter(objetivo = self)
                
                for s in stock:
                    if s.cantidad_inicial > 0 and s.cantidad_actual > 0:
                        cantidad += s.cantidad_actual

                d = cantidad / subproducto.cantidad
                if cant == None:
                    cant = d
                elif d < cant and d >= 0:
                    cant = d

            if cant != None: cant = cant * self.cantidad
            if cant != None and cant > 0 and descuento:
                cantidad = SolicitudCocina.objects.filter(  models.Q(cocina__id=cocina_id) &
                                                            models.Q(venta__producto=self.producto,activo=True) &
                                                            (models.Q(estado=None) | models.Q(estado=False))
                                                        ).aggregate(total=models.Sum('cantidad'))["total"]
                
                if cantidad != None:
                    cant -= cantidad
        except Exception as e: 
            print(e)
        
        if cant != None:return cant
        return 0

class Consumo(models.Model):
    id = models.AutoField(primary_key=True)
    turno = models.ForeignKey(Turno,on_delete=models.CASCADE,null=False,blank=False,related_name="turnoConsumo")
    formula = models.ForeignKey(Formula,on_delete=models.CASCADE,null=False,blank=False,related_name="formulaElaborada")
    producto = models.ForeignKey(Producto,on_delete=models.CASCADE,null=False,blank=False,related_name="productoConsumido")

    cantidad = models.FloatField(default=1.0,blank = False, null = False)

    medida = models.ForeignKey(Medida,on_delete=models.CASCADE,null=False,blank=False,related_name="medidaProductoConsumido")

    def to_str(self):
        return f"{self.producto.nombre}:{self.cantidad}{self.medida.abreviatura}"

class StockCocina(models.Model):
    id = models.AutoField(primary_key=True)
    cocina = models.ForeignKey(Cocina,on_delete=models.CASCADE,null=False,blank=False,related_name="CocinaStock")
    producto = models.ForeignKey(Producto,on_delete=models.CASCADE,null=False,blank=False,related_name="ProductoCocinaStock")
    lote = models.ForeignKey(StockAlmacen,on_delete=models.CASCADE,null=True,blank=True,related_name="CocinaAlmacen")
    transferencia = models.ForeignKey(Transferencia,on_delete=models.CASCADE,null=True,blank=True,related_name="cocinaTransferencia")
    transformacion = models.ForeignKey(FormulaTransformacion,on_delete=models.CASCADE,null=True,blank=True,related_name="cocinaProductoTransformado")

    costo_produccion = models.FloatField(blank = True, null = True)
    existencia = models.FloatField(blank = True, null = True)
    cantidad_remitida = models.FloatField(blank = True, null = True)
    cantidad_recibida = models.FloatField(blank = True, null = True)

    cantidad_inicial = models.FloatField(blank = True, null = True)
    cantidad_actual = models.FloatField(blank = True, null = True)

    objetivo = models.ForeignKey(Formula,on_delete=models.SET_NULL,null=True,blank=True,related_name="FormulaObjetivoCocinaStock")

    alta = models.DateTimeField(auto_now_add=True)

    activo = models.BooleanField(blank = True, null = True,default=True)
    consumo = models.TextField(blank = True, null = True)

    def fecha_fabricacion(self):
        return self.alta

    def operacion(self):
        return "Transferencia"

    def destino(self):
        return self.cocina

    def type_(self) -> str:
        return "StockCocina"

    def costo_cup(self) -> float:
        try:
            if self.costo_produccion: return self.costo_produccion
            return self.lote.costo_real()
        except: return 0.0
    
    def importe_remitido(self) -> float:
        try:
            if self.lote:return self.cantidad_remitida * self.lote.costo_cup
        except: return 0.0
    
    def importe_recibido(self) -> float:
        if self.cantidad_recibida:
            if self.lote:return self.cantidad_recibida * self.lote.costo_cup
            if not self.lote and self.costo_produccion:return self.cantidad_recibida * self.costo_produccion
        return None
    
    def existencia_cocina(self) -> float:
        total = 0
        sub_total = StockCocina.objects.filter(activo=True,cantidad_actual__gt=0, producto=self.producto,cocina=self.cocina).aggregate(total=models.Sum('cantidad_actual'))["total"]
        if sub_total: total += sub_total
        return total
    
    def disponibilidad(self) -> float:
        return self.objetivo.cantidad * self.cantidad_actual
    
    def precio_venta(self) -> float:
        return self.costo_cup()

class StockProductoCompuestoCocina(models.Model):
    id = models.AutoField(primary_key=True)
    #cocina = models.ForeignKey(Cocina,on_delete=models.CASCADE,null=False,blank=False,related_name="cocina_producto_compuesto_stock")
    producto = models.ForeignKey(Producto,on_delete=models.CASCADE,null=True,blank=True,related_name="producto_compuesto_stock")
    turno = models.ForeignKey(Turno,on_delete=models.CASCADE,null=False,blank=False,related_name="turno_elaboracion_producto")
    consumo = models.TextField(blank = True, null = True)

    costo_cup = models.FloatField(default=0.0,blank = False, null = False)
    cantidad_elaborada = models.FloatField(default=0.0,blank = False, null = False)
    cantidad_resultante = models.FloatField(default=0.0,blank = False, null = False)
    cantidad_actual = models.FloatField(default=0.0,blank = False, null = False)

    lote_auditable = models.BooleanField(blank = True, null = True, default=True)

    fecha_fabricacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(blank = False, null = False, default = True)
    monto_total = models.FloatField(default=0.0,blank = False, null = False)

    def existencia_cocina(self) -> float:
        total = 0
        sub_total = StockProductoCompuestoCocina.objects.filter(activo=True,cantidad_actual__gt=0, producto=self.producto,turno__cocina=self.turno.cocina).aggregate(total=models.Sum('cantidad_actual'))["total"]
        if sub_total: total += sub_total
        return total
    
    def precio_venta(self) -> float:
        if self.producto.precio_venta: return self.producto.precio_venta
        return self.costo_cup

class SolicitudCocina(models.Model):
    id = models.AutoField(primary_key=True)
    venta = models.ForeignKey(Venta,on_delete=models.CASCADE,null=False,blank=False,related_name="producto_solicitado_cosina")
    cocina = models.ForeignKey(Cocina,on_delete=models.CASCADE,null=False,blank=False,related_name="cocina_solicitada")
    cantidad = models.FloatField(default=0.0,blank = False, null = False)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    estado = models.BooleanField(blank = True, null = True,default=None)    # None=No procesado False=Procesandose True=Procesado
    transferido = models.BooleanField(blank = False, null = False,default=False)
    mensaje_cancelacion = models.TextField(blank = True, null = True)
    activo = models.BooleanField(blank = False, null = False, default = True)
    
    costo = models.FloatField(default=0.0,blank = False, null = False)


    def formula(self):
        return self.venta.producto.productoCocinaFormula.all().first()

    def accion(self):
        if self.estado == True:
            return "T"
        return "E"

    def tiempo_transcurrido(self):
        tiempo_actual = timezone.now()
        tiempo_transcurrido = tiempo_actual - self.fecha_solicitud

        # Obtener los días, horas y minutos
        dias, segundos_total = divmod(tiempo_transcurrido.total_seconds(), 86400)
        horas, segundos_total = divmod(segundos_total, 3600)
        minutos, segundos = divmod(segundos_total, 60)

        # Formatear la duración transcurrida
        duracion_formateada = []
        if minutos > 0: duracion_formateada.append(f"{int(minutos)} minutos")
        if horas > 0: duracion_formateada.insert(0,f"{int(horas)} horas")
        if dias > 0: duracion_formateada.insert(0,f"{int(dias)} días")
         
        return ", ".join(duracion_formateada)

class Nota(models.Model):
    id = models.AutoField(primary_key=True)
    cantidad = models.IntegerField(default=0,blank = False, null = False)
    monto = models.FloatField(default=0,blank = False, null = False)
    motivo = models.TextField(blank = True, null = True)
    cuadre = models.ForeignKey(Cuadre,on_delete=models.SET_NULL,null=True,blank=True,related_name="NotaCuadreCocina")
    fecha = models.DateTimeField(auto_now_add=True)
    
    def __str__(self) -> str:
        return str(self.motivo)
    
class NotaCocina(models.Model):
    id = models.AutoField(primary_key=True)
    cocina_id = models.TextField(blank = True, null = True)
    cocina_nombre = models.TextField(blank = True, null = True)
    cocinero_nombre = models.TextField(blank = True, null = True)
    nota = models.TextField(blank = True, null = True)
    fecha = models.DateTimeField(auto_now_add=True)
    
    def __str__(self) -> str:
        return str(self.nota)
