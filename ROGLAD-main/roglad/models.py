from django.db import models
from django.contrib.auth.models import User
from bussiness.models import UserAccount

class Negocio(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=100)
    caracteristicas = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    # Agrega más campos según necesites

    def __str__(self):
        return self.nombre

class Usuarios(models.Model):
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE)
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE)

    
