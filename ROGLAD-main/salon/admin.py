from django.contrib import admin

from .models import Cliente, Turno

# Register your models here.


class TurnoAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Turno._meta.fields]
    model = Turno
admin.site.register(Turno,TurnoAdmin)



class ClienteAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Cliente._meta.fields]
    model = Cliente
admin.site.register(Cliente,ClienteAdmin)

