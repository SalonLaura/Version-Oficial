import json
from django.db import models
from django.utils import timezone

from bussiness.models import ConfigVar, Descuentos, Pago, Producto, StockAlmacen, Transferencia, UserAccount


class Estado(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.TextField(blank = False, null = False)
    duracion = models.FloatField(blank = False, null = False,default=0.0) #Dias

class GrupoEstado(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.TextField(blank = False, null = False)
    estados = models.ManyToManyField(Estado)
    activo = models.BooleanField(default=True)

    def estados_str(self):
        try:
            estados_list = []
            for estado in self.estados.all():
                if estado.duracion > 1:estados_list.append(f"{estado.nombre} {estado.duracion} días")
                else:estados_list.append(f"{estado.nombre} {estado.duracion} día")

            return ", ".join(estados_list)
        except:
            return ""

class Servicio(models.Model):
    MONEDAS_CHOICES = [
        ('USD', 'Dólar estadounidense'),
        ('EUR', 'Euro'),
        ('CUP', 'Peso cubano'),
        ('MLC', 'Moneda libremente convertible'),
    ]
    
    id = models.AutoField(primary_key=True)
    nombre = models.TextField(blank = False, null = False)
    descripcion = models.TextField(blank = False, null = False)
    activo = models.BooleanField(default=True)
    contrato = models.BooleanField(default=True)
    estado = models.ForeignKey(GrupoEstado,on_delete=models.CASCADE,null=True,blank=True)
    
    costo = models.FloatField(default=0,blank = False, null = False)
    precio = models.FloatField(default=0,blank = False, null = False)
    moneda_precio = models.CharField(max_length=3, choices=MONEDAS_CHOICES)
    
    pago_fotografo = models.FloatField(default=0,blank = False, null = False)
    pago_responsable = models.FloatField(default=0,blank = False, null = False)

    def precio_cup(self):
        razon_cambio_usd = float(ConfigVar.objects.get(key="precio_usd").value)
        if self.moneda_precio == "CUP": return self.precio
        if self.moneda_precio == "USD": return (self.precio * razon_cambio_usd)
        #if self.moneda_precio == "MLC": return (self.precio * razon_cambio_mlc)
        #if self.moneda_precio == "EUR": return (self.precio * razon_cambio_eur)
        
    def precio_usd(self):
        razon_cambio_usd = float(ConfigVar.objects.get(key="precio_usd").value)
        if self.moneda_precio == "CUP": return (self.precio / razon_cambio_usd)
        if self.moneda_precio == "USD": return self.precio

    def estados_str(self):
        try:
            estados_list = []
            for estado in self.estado.estados.all():
                if estado.duracion > 1:estados_list.append(f"{estado.nombre} {estado.duracion} días")
                else:estados_list.append(f"{estado.nombre} {estado.duracion} día")

            return ", ".join(estados_list)
        except:
            return "Sin estados asignados"



class Fotografo(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.TextField(blank = False, null = False)
    activo = models.BooleanField(default=True)
    
    def user_str(self):
        return self.nombre

    def tag_id(self):
        return f"F-{self.id}"

    def __str__(self):
        return self.nombre
    
    def pago_acumulado(self, fin=None):
        monto = 0.0
        
        pagos = Pago.objects.filter(user_id=f"F-{self.id}",fecha_liquidacion__isnull = True)
        if fin != None: pagos = pagos.filter(fecha__lte = fin)
        for pago in pagos:
            if pago.monto == pago.liquidado:
                pago.fecha_liquidacion = timezone.now()
                pago.save()

            else:monto += (pago.monto - pago.liquidado)

        return monto
    
    def pagos(self, fin=None):
        pagos = Pago.objects.filter(user_id=f"F-{self.id}",fecha_liquidacion__isnull = True)
        if fin != None: pagos = pagos.filter(fecha__lte = fin)
        return pagos

    def monto_descontar(self, fin=None):
        monto = 0.0
        descuentos = Descuentos.objects.filter(user_id=f"F-{self.id}",fecha_liquidacion__isnull = True)
        if fin != None: descuentos = descuentos.filter(fecha__lte = fin)

        for descuento in descuentos:
            if descuento.monto == descuento.liquidado:
                descuento.fecha_liquidacion = timezone.now()
                descuento.save()

            else:monto += (descuento.monto - descuento.liquidado)

        return monto
    
    def descuentos(self, fin=None):
        descuentos = Descuentos.objects.filter(user_id=f"F-{self.id}",fecha_liquidacion__isnull = True)
        if descuentos != None: descuentos = descuentos.filter(fecha__lte = fin)
        return descuentos

    def monto_pagar(self, fin=None):
        pago_acumulado = self.pago_acumulado(fin)
        monto_descontar = self.monto_descontar(fin)

        monto = pago_acumulado - monto_descontar
        if monto < 0:
            monto = 0
        return monto

class Editor(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.TextField(blank = False, null = False)
    pago = models.FloatField(default=0,blank = False, null = False)
    activo = models.BooleanField(default=True)

    def user_str(self):
        return self.nombre
    
    def __str__(self):
        return self.nombre
    
    def tag_id(self):
        return f"E-{self.id}"
    
class CasaImpresion(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.TextField(blank = False, null = False)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nombre
    

class TipoContrato(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.TextField(blank = False, null = False)
    activo = models.BooleanField(default=True)

class ServicioContrato(models.Model):
    id = models.AutoField(primary_key=True)
    servicio = models.ForeignKey(Servicio,on_delete=models.CASCADE,null=False,blank=False)
    cantidad = models.IntegerField(blank = False, null = False,default=0.0)
    
    def servicio_str(self):
        if float(int(self.cantidad)) == self.cantidad:
            return f"{self.servicio.nombre} - {int(self.cantidad)}"
        return f"{self.servicio.nombre} - {self.cantidad}"
    
    
class ServicioContratoCliente(models.Model):
    id = models.AutoField(primary_key=True)
    servicio = models.ForeignKey(Servicio,on_delete=models.CASCADE,null=False,blank=False)
    cantidad = models.IntegerField(blank = False, null = False,default=1)
    seleccion = models.TextField(blank = True, null = True)
    estado = models.ForeignKey(Estado,on_delete=models.SET_NULL,null=True,blank=True)
    fecha_acordada = models.DateTimeField(null=True)
    terminado = models.BooleanField(default=False,blank = False, null = False)
        
    def servicio_str(self):
        if float(int(self.cantidad)) == self.cantidad:
            return f"{self.servicio.nombre} - {int(self.cantidad)}"
        return f"{self.servicio.nombre} - {self.cantidad}"
    
    def ficha(self):
        return FichaCliente.objects.filter(servicios_contrato=self).first()

class Contrato(models.Model):
    MONEDAS_CHOICES = [
        ('USD', 'Dólar estadounidense'),
        ('EUR', 'Euro'),
        ('CUP', 'Peso cubano'),
        ('MLC', 'Moneda libremente convertible'),
    ]


    id = models.AutoField(primary_key=True)
    nombre = models.TextField(blank = False, null = False)
    tipo = models.ForeignKey(TipoContrato,on_delete=models.CASCADE,null=False,blank=False)
    servicios = models.ManyToManyField(ServicioContrato)

    #costo = models.FloatField(default=0,blank = False, null = False)
    precio = models.FloatField(default=0,blank = False, null = False)
    moneda_precio = models.CharField(max_length=3, choices=MONEDAS_CHOICES)

    anticipo = models.FloatField(default=0,blank = False, null = False)
    moneda_anticipo = models.CharField(max_length=3, choices=MONEDAS_CHOICES)

    pago_fotografo = models.FloatField(default=0,blank = False, null = False)
    pago_responsable = models.FloatField(default=0,blank = False, null = False)
    pago_gestor = models.FloatField(default=0,blank = False, null = False)
    monto_bolsa = models.FloatField(default=0,blank = False, null = False)

    activo = models.BooleanField(default=True)

    def precio_cup(self):    
        razon_cambio_usd = float(ConfigVar.objects.get(key="precio_usd").value)
        if self.moneda_precio == "CUP": return self.precio
        if self.moneda_precio == "USD": return (self.precio * razon_cambio_usd)
        #if self.moneda_precio == "MLC": return (self.precio * razon_cambio_mlc)
        #if self.moneda_precio == "EUR": return (self.precio * razon_cambio_eur)

    def precio_usd(self):
        razon_cambio_usd = float(ConfigVar.objects.get(key="precio_usd").value)
        if self.moneda_precio == "CUP": return (self.precio / razon_cambio_usd)
        if self.moneda_precio == "USD": return self.precio

    def anticipo_cup(self):  
        razon_cambio_usd = float(ConfigVar.objects.get(key="precio_usd").value)  
        if self.moneda_anticipo == "CUP": return self.anticipo
        if self.moneda_anticipo == "USD": return (self.anticipo * razon_cambio_usd)
        #if self.moneda_anticipo == "MLC": return (self.anticipo * razon_cambio_mlc)
        #if self.moneda_anticipoo == "EUR": return (self.anticipo * razon_cambio_eur)

    def anticipo_usd(self):
        razon_cambio_usd = float(ConfigVar.objects.get(key="precio_usd").value)
        if self.moneda_anticipo == "CUP": return (self.anticipo / razon_cambio_usd)
        if self.moneda_anticipo == "USD": return self.anticipo

    def servicios_str(self):
        servicios_list = []
        for servicio in self.servicios.all():
            servicios_list.append(f"{servicio.servicio.nombre} - {servicio.cantidad}")

        if len(servicios_list) > 0:return ", ".join(servicios_list)
        return "-"

class FichaCliente(models.Model):
    id = models.AutoField(primary_key=True)

    responsable_contrato = models.ForeignKey(UserAccount,on_delete=models.CASCADE,null=False,blank=False, related_name="responsable_contrato_ficha")
    responsable_revicion = models.ForeignKey(UserAccount,on_delete=models.CASCADE,null=False,blank=False, related_name="responsable_revicion_ficha")
    fotografo = models.ForeignKey(Fotografo,on_delete=models.CASCADE,null=False,blank=False, related_name="fotografo_ficha")
    editor = models.ForeignKey(Editor,on_delete=models.CASCADE,null=False,blank=False, related_name="editor_ficha")

    contrato = models.ForeignKey(Contrato,on_delete=models.CASCADE,null=False,blank=False, related_name="contrato_ficha")
    servicios_contrato = models.ManyToManyField(ServicioContratoCliente, related_name="servicios_contrato_ficha")

    
    nombre = models.CharField(blank = False, null = False,max_length=200)
    edad = models.CharField(blank = False, null = False,max_length=200)
    ci = models.CharField(blank = False, null = False,max_length=200)

    calle = models.CharField(blank = True, null = True,max_length=100)
    entre = models.CharField(blank = True, null = True,max_length=100)
    numero = models.CharField(blank = True, null = True,max_length=100)
    consejo_popular  = models.CharField(blank = True, null = True,max_length=100)
    muncp = models.CharField(blank = True, null = True,max_length=100)
    prov = models.CharField(blank = True, null = True,max_length=100)
    pais = models.CharField(blank = True, null = True,max_length=100)
    
    telefono = models.CharField(blank = True, null = True,max_length=200)
    correo = models.CharField(blank = True, null = True,max_length=200)
    facebook = models.CharField(blank = True, null = True,max_length=200)
    instagram = models.CharField(blank = True, null = True,max_length=200)
    twitter = models.CharField(blank = True, null = True,max_length=200)
    telegram = models.CharField(blank = True, null = True,max_length=200)


    nombre_contrata = models.CharField(blank = True, null = True,max_length=200)
    ci_contrata = models.CharField(blank = True, null = True,max_length=200)
    parentesco_contrata = models.CharField(blank = True, null = True,max_length=200)
    
    nombre_contrata_2 = models.CharField(blank = True, null = True,max_length=200)
    ci_contrata_2 = models.CharField(blank = True, null = True,max_length=200)
    parentesco_contrata_2 = models.CharField(blank = True, null = True,max_length=200)

    servicios_adicionales = models.ManyToManyField(ServicioContratoCliente, related_name="servicios_adicionales_ficha")

    
    autorizo_redes_sociales = models.BooleanField(blank = False, null = False,default=True)
    condiciones_publicacion = models.TextField(blank = True, null = True)

    
    fecha_solicitud = models.DateTimeField(null=True,auto_now_add=True)
    fecha_acordada = models.DateField(null=True)
    fecha_seleccion = models.DateField(null=True)
    fecha_realizacion = models.DateTimeField(null=True)
    fecha_fin = models.DateField(null=True)

    activo = models.BooleanField(default=True)

    anotaciones = models.TextField(blank = False, null = False,default="")
    
    historial_cambios = models.JSONField(blank = True, null = True)
    
    precio_contrato_cup = models.FloatField(blank = False, null = False,default=0.0)
    precio_contrato_usd = models.FloatField(blank = False, null = False,default=0.0)
    costo_cup = models.FloatField(blank = False, null = False,default=0.0)
    costo_usd = models.FloatField(blank = False, null = False,default=0.0)
    tasa_cambio_usd = models.FloatField(blank = False, null = False,default=0.0)

    audit = models.BooleanField(default=True)

    def cumplimiento(self):
        
        porcientos = []

        servicios_contratos = self.servicios_contrato.all()

        for servicio in servicios_contratos:
            total = 1  
            estado_actual = 0
            if servicio.servicio.estado:
                for estado in servicio.servicio.estado.estados.all():
                    total += 1
                    if servicio.estado == estado:
                        estado_actual = total - 1

            if servicio.terminado:
                estado_actual = total

            porcientos.append((estado_actual*100)/total)
        
        servicios_contratos = self.servicios_adicionales.all()

        for servicio in servicios_contratos:
            total = 1  
            estado_actual = 0
            if servicio.servicio.estado:
                for estado in servicio.servicio.estado.estados.all():
                    total += 1
                    if servicio.estado == estado:
                        estado_actual = total - 1

            if servicio.terminado:
                estado_actual = total

            porcientos.append((estado_actual*100)/total)


        return round(sum(porcientos)/len(porcientos),2)
    
    
    def cambios(self):
        try:
            datos_json = json.loads(self.historial_cambios)
        except:
            datos_json = {"cambios":[]}
        cambios = list(datos_json["cambios"])
        datos_json_list = []
        
        for d in cambios:
            datos_json_list.insert(0,d)
        return datos_json_list

    def add_cambios(self,new_cambios):
        try:
            datos_json = json.loads(self.historial_cambios)
        except:
            datos_json = {"cambios":[]}
        cambios = list(datos_json["cambios"])

        
        historial_cambios_data =json.dumps({
            "cambios": cambios + new_cambios
        })

        self.historial_cambios = historial_cambios_data
        self.save()
        

    def costo_servicios(self):
        costo = 0
        for servicio in self.servicios_adicionales.all():
            costo += servicio.servicio.precio_cup()
        return costo

    def costo_total(self):        
        razon_cambio_usd = float(ConfigVar.objects.get(key="precio_usd").value)
        if self.contrato.moneda_precio == "CUP": self.contrato.costo + self.costo_servicios()
        if self.contrato.moneda_precio == "USD": return (self.contrato.costo * razon_cambio_usd) + self.costo_servicios()
        #if self.contrato.moneda_precio == "MLC": return (self.contrato.costo * razon_cambio_mlc) + self.costo_servicios()
        #if self.contrato.moneda_precio == "EUR": return (self.contrato.costo * razon_cambio_eur) + self.costo_servicios()

    def precio_cup(self):
        precio = 0
        for servicio in self.servicios_adicionales.all():
            precio += servicio.servicio.precio_cup()
        precio += self.contrato.precio_cup()
        precio -= self.contrato.anticipo_cup()
        return precio

    def precio_usd(self):
        precio = 0
        for servicio in self.servicios_adicionales.all():
            precio += servicio.servicio.precio_usd()

        precio += self.contrato.precio_usd()
        precio -= self.contrato.anticipo_usd()

        return precio
    
    def contrato_precio_cup(self):
        precio = 0
        precio += self.contrato.precio_cup()
        return precio

    def contrato_precio_usd(self):
        precio = 0
        precio += self.contrato.precio_usd()

        return precio
        
    def adicionales_precio_cup(self):
        precio = 0
        for servicio in self.servicios_adicionales.all():
            precio += servicio.servicio.precio_cup()
        return precio

    def adicionales_precio_usd(self):
        precio = 0
        for servicio in self.servicios_adicionales.all():
            precio += servicio.servicio.precio_usd()

        return precio


    
    def servicios_adicionales_agrupados(self):
        servicios_list = []
        servicios_ids = []
        servicios = self.servicios_adicionales.all()
        for s in servicios:
            if s.servicio.id in servicios_ids:
                servicios_list[servicios_ids.index(s.servicio.id)].cantidad += s.cantidad
            else:
                servicios_list.append(s)
                servicios_ids.append(s.servicio.id)
        return servicios_list
        
    def numeroCliente(self):
        registros = FichaCliente.objects.filter(fecha_solicitud__month=self.fecha_solicitud.month, fecha_solicitud__year=self.fecha_solicitud.year)
        return list(registros).index(self)+1
        
    def identificador(self):
        return str(self.numeroCliente()) + self.fecha_solicitud.strftime("%b%d%Y")
    
    
class EnviosEdicion(models.Model):
    id = models.AutoField(primary_key=True)
    lote = models.IntegerField(blank = False, null = False)
    editor = models.ForeignKey(Editor,on_delete=models.CASCADE,null=False,blank=False, related_name="editor_envio")
    servicio = models.ForeignKey(ServicioContratoCliente,on_delete=models.CASCADE,null=False,blank=False, related_name="foto_envia_editar")
    fecha_envio = models.DateTimeField(auto_now_add=True)
    fecha_retorno = models.DateTimeField(null=True)


    def color(self):
        colors = ["red","lime","cyan","rose","orange","green","sky","pink","amber",
                  "emerald","indigo","fuchsia","yellow","teal","violet","purple"]
        
        indice_color = self.lote
        if self.lote > len(colors):
            indice_color = self.lote % len(colors)

        return colors[indice_color]
    
class EnviosImpresion(models.Model):
    id = models.AutoField(primary_key=True)
    lote = models.IntegerField(blank = False, null = False)
    casa = models.ForeignKey(CasaImpresion,on_delete=models.CASCADE,null=True,blank=True, related_name="casa_envio")
    servicio = models.ForeignKey(ServicioContratoCliente,on_delete=models.CASCADE,null=False,blank=False, related_name="foto_envia_imprimir")
    fecha_envio = models.DateTimeField(null=True)
    fecha_retorno = models.DateTimeField(null=True)


    def color(self):
        colors = ["red","lime","cyan","rose","orange","green","sky","pink","amber",
                  "emerald","indigo","fuchsia","yellow","teal","violet","purple"]
        
        indice_color = self.lote
        if self.lote > len(colors):
            indice_color = self.lote % len(colors)

        return colors[indice_color]
    
    
class StockEstudio(models.Model):
    id = models.AutoField(primary_key=True)
    producto = models.ForeignKey(Producto,on_delete=models.CASCADE,null=False,blank=False,related_name="ProductoStockEstudio")
    transferencia = models.ForeignKey(Transferencia,on_delete=models.CASCADE,null=True,blank=True,related_name="TransferenciaEstudio")
    lote = models.ForeignKey(StockAlmacen,on_delete=models.CASCADE,null=True,blank=True,related_name="LoteStockSalon")
    
    costo = models.FloatField(blank = True, null = True)
    deuda = models.FloatField(blank = True, null = True)
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
        return {"nombre":"Estudio(Bolsa)"}

    def type_(self) -> str:
        return "BolsaEstudio"
    

class Turno(models.Model):
    id = models.AutoField(primary_key=True)
    cuadre = models.JSONField()
    user = models.ForeignKey(UserAccount,on_delete=models.SET_NULL,null=True,blank=True,related_name="UserTurnoEstudio")
    
    inicio = models.DateTimeField(auto_now_add=True)
    fin = models.DateTimeField(blank = True, null = True)

    def datos_cuadre(self):
        datos_json = json.loads(self.cuadre)
        if not datos_json:
            return {"notas":[],"cuadre":[]}
        return datos_json

    def add_entrada_cuadre(self,producto_id,entrada):
        producto_id = str(producto_id)
        entrada = float(entrada)

        datos_json = json.loads(self.cuadre)
        add_ok = False
        try:
            cuadre = datos_json["cuadre"]
            for producto in cuadre:
                if producto["producto_id"] == producto_id:
                    producto["entradas"] += entrada
                    add_ok = True
                    break

            if not add_ok:
                cuadre.append(
                            {
                                "producto_id":producto_id,
                                "inicial":0,
                                "entradas":entrada
                            }
                        )
        except:
            print("Error add_entrada_cuadre")
                
        cuadre_data =json.dumps({
            "notas":datos_json["notas"],
            "cuadre":cuadre
        })

        self.cuadre = cuadre_data
        self.save()
        