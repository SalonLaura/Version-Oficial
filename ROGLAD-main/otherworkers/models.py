import json
from django.db import models

from bussiness.models import UserAccount


class Turno(models.Model):
    id = models.AutoField(primary_key=True)
    cuadre = models.JSONField()
    user = models.ForeignKey(UserAccount,on_delete=models.SET_NULL,null=True,blank=True,related_name="UserTurnoWorker")
    
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
        