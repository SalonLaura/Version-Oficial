from django.db import models

from bussiness.models import Almacen, Producto, UserAccount, FormulaTransformacion


class Turno(models.Model):
    id = models.AutoField(primary_key=True)
    almacen = models.ForeignKey(Almacen,on_delete=models.CASCADE,null=False,blank=False,related_name="TurnoAlmacen")
    user = models.ForeignKey(UserAccount,on_delete=models.CASCADE,null=False,blank=False,related_name="UserTurnoAlmacen")
    inicio = models.DateTimeField(auto_now_add=True)
    fin = models.DateTimeField(blank = True, null = True)



class Pedidos(models.Model):
    id = models.AutoField(primary_key=True)
    producto = models.ForeignKey(Producto,on_delete=models.CASCADE,null=False,blank=False,related_name="productoPedido")
    ideal = models.FloatField(blank = False, null = False, default=0.0)
    alerta = models.FloatField(blank = False, null = False, default=0.0)



class CambiosAlmacen(models.Model):
    id = models.AutoField(primary_key=True)
    producto = models.ForeignKey(Producto,on_delete=models.CASCADE,null=False,blank=False,related_name="productoCambiado")
    almacen = models.ForeignKey(Almacen,on_delete=models.CASCADE,null=True,blank=True,verbose_name="almacenCambiado")
    existencia = models.FloatField(blank = True, null = True)    
    cantidad = models.FloatField(default=0.0,blank = False, null = False)
    motivo = models.TextField(blank = True, null = True)
    fecha = models.DateTimeField(auto_now_add=True, blank = True, null = True)  


    def destino(self):
        return {"nombre":"-"}
    
    def operacion(self):
        return "Ajuste de stock"
    
    def type_(self):
        return "CambiosAlmacen"

class Nota(models.Model):
    id = models.AutoField(primary_key=True)
    cantidad = models.IntegerField(default=0,blank = False, null = False)
    monto = models.FloatField(default=0,blank = False, null = False)
    causa = models.TextField(blank = True, null = True)
    motivo = models.TextField(blank = True, null = True)
    turno = models.ForeignKey(Turno,on_delete=models.SET_NULL,null=True,blank=True,related_name="NotaTurnoAlmacen")
    fecha = models.DateTimeField(auto_now_add=True)
    
    def __str__(self) -> str:
        return str(self.motivo)