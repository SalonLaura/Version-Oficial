import json
from django.db import models
from bussiness.models import Descuentos, Pago, PuntoVenta, Turno
from datetime import datetime

from kitchen.models import Cocina

class Caja(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField(blank = False, null = False)
    monto = models.FloatField(default=0.0,blank = False, null = False)

    MONEDAS_CHOICES = [
        ('USD', 'Dólar estadounidense'),
        ('EUR', 'Euro'),
        ('CUP', 'Peso cubano'),
        ('MLC', 'Moneda libremente convertible'),
    ]

    moneda = models.CharField(max_length=3, choices=MONEDAS_CHOICES,default="CUP")


    
class ReciboEfectivo(models.Model):
    id = models.AutoField(primary_key=True)
    origen = models.TextField(blank = True, null = True)
    recibido = models.TextField(blank = True, null = True) # Nombre del administrador que recoje el dinero en el punto de venta
    monto = models.FloatField(default=0.0,blank = False, null = False)
    monto_letra = models.TextField(blank = True, null = True)
    motivo_diferencia = models.TextField(blank = True, null = True)
    fecha = models.DateTimeField(auto_now_add=True)
    fecha_confirmacion = models.DateTimeField(blank = True, null = True)


    def turno(self):
        turno = Turno.objects.get(id = self.origen.replace("PV-",""))
        if turno.fin == None: return None
        else: return turno

    def centro_costo_origen(self):
        turno = Turno.objects.get(id = self.origen.replace("PV-",""))
        print(turno)
        if turno.fin == None: return None
        else: return turno.punto_venta.nombre

class Operaciones(models.Model):
    id = models.AutoField(primary_key=True)
    monto = models.FloatField(default=0.0,blank = False, null = False)
    motivo = models.TextField(blank = False, null = False)
    caja = models.ForeignKey(Caja, on_delete=models.CASCADE,blank = False, null = False)
    existencia = models.FloatField(blank = True, null = True)
    fecha = models.DateTimeField(auto_now_add=True)


class Nomina(models.Model):
    id = models.AutoField(primary_key=True)
    nomina = models.JSONField()

    pagos = models.ManyToManyField(Pago,blank = True, null = True)
    descuentos = models.ManyToManyField(Descuentos,blank = True, null = True)

    fecha = models.DateTimeField(auto_now_add=True)

    user_confirm = models.CharField(blank = True, null = True,max_length=200)


    def nombre(self):
        fecha_formateada = self.fecha.strftime('%m%d%Y-%H%M%S')  # Formatea la fecha según tus especificaciones
        return fecha_formateada
    
    def datos_nomina(self):
        try:
            datos_json = json.loads(self.nomina)
            return datos_json
        except:
            return {"total": 0.0, "pagos": []}


class Capital(models.Model):
    id = models.AutoField(primary_key=True)
    centro_costo = models.CharField(blank = False, null = False,max_length=50)
    monto = models.FloatField(default=0.0,blank = False, null = False)
    fecha = models.DateField(auto_now_add=True)

    
class CapitalLiquides(models.Model):
    id = models.AutoField(primary_key=True)
    capital = models.FloatField(default=0.0,blank = False, null = False)
    liquides = models.FloatField(default=0.0,blank = False, null = False)
    fecha = models.DateField(auto_now_add=True)


    
class GastoMensual(models.Model):
    id = models.AutoField(primary_key=True)
    centro_costo = models.CharField(blank = False, null = False,max_length=50)
    motivo = models.CharField(blank = False, null = False,max_length=500)
    monto = models.FloatField(default=0.0,blank = False, null = False)
    fecha = models.DateField(auto_now_add=True)


    def origen(self):
        if self.centro_costo == "all": return "General"

        if "PV-" in self.centro_costo: 
            return PuntoVenta.objects.get(id = self.centro_costo.replace("PV-","")).nombre
        
        if "C-" in self.centro_costo: 
            return Cocina.objects.get(id = self.centro_costo.replace("C-","")).nombre
        
        if "estudio" in self.centro_costo: 
            return "Estuio"
        
        if "salon" in self.centro_costo: 
            return "Salón"