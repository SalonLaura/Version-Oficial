import json
from django.db import models

from bussiness.models import ConfigVar, Pago, Producto, Transferencia, UserAccount
from estudio.models import FichaCliente

# Create your models here.


class CantidadSubproducto(models.Model):
    id = models.AutoField(primary_key=True)
    producto = models.ForeignKey(Producto,on_delete=models.CASCADE,null=False,blank=False,related_name="CantidadSubproductoSalon")
    cantidad = models.FloatField(default=0.0,blank = False, null = False)
    subgrupo = models.CharField(max_length=5, blank = True, null = True)

class Servicio(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(blank = False, null = False, max_length=200)
    precio_usd = models.FloatField(blank = False, null = False, default = 0.0)
    descuento = models.FloatField(blank = False, null = False, default = 0.0)
    caracteristicas = models.TextField(blank = True, null = True)
    
    subproductos = models.ManyToManyField(CantidadSubproducto)
    
    pago_monto = models.FloatField(default=1.0,blank = False, null = False)
    pago_relacion = models.CharField(blank = False, null = False,max_length=1)
    activo = models.BooleanField(default=True)

    def porc_descuento(self):
        return (100 - self.descuento) / 100

    def subproductos_list(self):
        subproductos_dict = {}
        subproductos = self.subproductos.all()
        
        for s in subproductos:
            if s.subgrupo in subproductos_dict.keys():
                subproductos_dict[s.subgrupo].append({"id":s.id,"n":f"{s.producto.nombre}","c":s.cantidad,"a":s.producto.medida.abreviatura})
            else:
                subproductos_dict[s.subgrupo] = [{"id":s.id,"n":f"{s.producto.nombre}","c":s.cantidad,"a":s.producto.medida.abreviatura},]

        subproductos_requeridos = []
        subproductos_list = []
        for k in subproductos_dict.keys():
            if k == None:
                subproductos_requeridos = subproductos_dict[k]
            else:
                subproductos_list.append(
                    subproductos_dict[k]
                )
            
        l = {
            "requeridos":subproductos_requeridos,
            "opcionales":subproductos_list
        }
        return l
    
    def subproductos_str(self):
        subproductos_list = []
        subproductos = self.subproductos.all()
        
        for s in subproductos:
            subproductos_list.append(f"{s.producto.nombre} - {s.cantidad}{s.producto.medida.abreviatura}")
        return ", ".join(subproductos_list)

    def precio_cup(self):
        razon_cambio_usd = float(ConfigVar.objects.get(key="precio_usd").value)
        return self.precio_usd * razon_cambio_usd

    def monto_descuento(self):
        razon_cambio_usd = float(ConfigVar.objects.get(key="precio_usd").value)
        return self.precio_usd * razon_cambio_usd * (self.descuento/100)

class Turno(models.Model):
    id = models.AutoField(primary_key=True)
    cuadre = models.JSONField()
    user = models.ForeignKey(UserAccount,on_delete=models.SET_NULL,null=True,blank=True,related_name="UserTurnoSalon")
    
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
        

    def cerrar_cuadre(self):
        
        datos_json = json.loads(self.cuadre)
        
        try:
            cuadre = datos_json["cuadre"]
            for producto in cuadre:
                consumo = Consumo.objects.filter(producto__id=producto["producto_id"])
                if consumo.exists():
                    usado = consumo.aggregate(total=models.Sum('cantidad'))["total"]
                else:
                    usado = 0
                
                producto["usado"] = usado

                entregado = producto["inicial"] - usado
                if entregado < 0: entregado = 0
                producto["entregado"] = entregado
                    
        except:
            print("Error add_entrada_cuadre")
                
        cuadre_data =json.dumps({
            "notas":datos_json["notas"],
            "cuadre":cuadre
        })

        self.cuadre = cuadre_data
        self.save()
        


class Cliente(models.Model):
    
    MONEDAS_CHOICES = [
        ('USD', 'Dólar estadounidense'),
        ('EUR', 'Euro'),
        ('CUP', 'Peso cubano'),
        ('MLC', 'Moneda libremente convertible'),
    ]
    
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(blank = False, null = False,max_length=200)
    ci = models.CharField(blank = True, null = True,max_length=11)
    telefono = models.CharField(blank = True, null = True,max_length=200)

    servicios = models.ManyToManyField(Servicio, related_name="servicios_cliente_salon")
    activo = models.BooleanField(default=True)    
    
    turno = models.ForeignKey(Turno,on_delete=models.CASCADE,null=True,blank=True,related_name="turnoClienteSalon")
    user_id = models.CharField(blank = False, null = False,max_length=999)
    user_name = models.CharField(blank = False, null = False,max_length=999)

    fecha_solicitud = models.DateTimeField(null=True,auto_now_add=True)
    fecha_acordada = models.DateTimeField(null=True)
    fecha_realizacion = models.DateTimeField(null=True)

    costo = models.FloatField(default=0.0,blank = False, null = False)
    razon_cambio = models.FloatField(default=0.0,blank = False, null = False)

    monto_base = models.FloatField(default=0.0,blank = False, null = False)
    monto_cobrado = models.FloatField(default=0.0,blank = False, null = False)
    moneda = models.CharField(max_length=3, choices=MONEDAS_CHOICES,default="CUP")    
    contrato_id = models.IntegerField(blank = True, null = True)

    
    pagos = models.ManyToManyField(Pago,blank = True, null = True)

    audit = models.BooleanField(default=True)

    def monto(self):
        if self.moneda == "CUP":    return self.monto_cobrado
        else: return self.monto_cobrado * self.razon_cambio

    
    def contrato(self):
        if not  self.contrato_id: return "-"
        return FichaCliente.objects.get(id=self.contrato_id).identificador()
    
    def servicios_str(self):
        servicios_list = []
        servicios = self.servicios.all()
        for servicio in servicios:
            servicios_list.append(servicio.nombre)
        return ", ".join(servicios_list)
    
    
    def precio_base_usd(self):
        precio = 0.0
        servicios = self.servicios.all()
        for servicio in servicios:
            precio += servicio.precio_usd

        return precio
    
    def precio_base_cup(self):
        razon_cambio_usd = float(ConfigVar.objects.get(key="precio_usd").value)
        return self.precio_base_usd() * razon_cambio_usd
    
    def consumo_cup(self):
        Consumo.objects.filter(cliente=self)

class Consumo(models.Model):
    id = models.AutoField(primary_key=True)
    cliente_name = models.CharField(blank = False, null = False,max_length=999)
    cliente = models.ForeignKey(Cliente,on_delete=models.SET_NULL,null=True,blank=True,related_name="ClienteConsumo")
    servicio = models.CharField(blank = False, null = False,max_length=999)
    producto = models.ForeignKey(Producto,on_delete=models.CASCADE,null=False,blank=False,related_name="productoConsumidoSalon")
    cantidad = models.FloatField(default=1.0,blank = False, null = False)
    turno = models.ForeignKey(Turno,on_delete=models.CASCADE,null=False,blank=False,related_name="turnoConsumidoSalon")


