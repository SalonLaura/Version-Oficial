from django.contrib import admin

from caja.models import Caja, Operaciones, ReciboEfectivo ,Nomina

# Register your models here.

class CajaAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Caja._meta.fields]
    model = Caja
    
class ReciboEfectivoAdmin(admin.ModelAdmin):
    list_display=[field.name for field in ReciboEfectivo._meta.fields]
    model = ReciboEfectivo
    
class OperacionesAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Operaciones._meta.fields]
    model = Operaciones
    
class NominaAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Nomina._meta.fields]
    model = Nomina

admin.site.register(Nomina, NominaAdmin)    
admin.site.register(Caja, CajaAdmin)
admin.site.register(ReciboEfectivo, ReciboEfectivoAdmin)
admin.site.register(Operaciones, OperacionesAdmin)
