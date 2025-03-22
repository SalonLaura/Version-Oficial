from django.contrib import admin

from almacen.models import Pedidos,Turno

class PedidosAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Pedidos._meta.fields]
    model = Pedidos
admin.site.register(Pedidos, PedidosAdmin)

class TurnoAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Turno._meta.fields]
    model = Turno
admin.site.register(Turno, TurnoAdmin)