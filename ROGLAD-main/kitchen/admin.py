from django.contrib import admin

from kitchen.models import Cocina, Consumo, GastosElaboracion, Nota, SolicitudCocina, StockProductoCompuestoCocina,Turno,Cuadre,StockCocina,CantidadSubproducto,Formula

class StockCocinaAdmin(admin.ModelAdmin):
    list_display=[field.name for field in StockCocina._meta.fields]
    search_fields = ["id","producto__nombre"]
    list_filter = ["cocina__nombre","activo"]
    model = StockCocina
admin.site.register(StockCocina,StockCocinaAdmin)

    
class SolicitudCocinaAdmin(admin.ModelAdmin):
    list_display=[field.name for field in SolicitudCocina._meta.fields]
    model = SolicitudCocina
admin.site.register(SolicitudCocina,SolicitudCocinaAdmin)
    
class StockProductoCompuestoCocinaAdmin(admin.ModelAdmin):
    list_display=[field.name for field in StockProductoCompuestoCocina._meta.fields]
    search_fields = ["id","producto__nombre"]
    list_filter = ["turno__cocina__nombre","activo"]
    model = StockProductoCompuestoCocina
admin.site.register(StockProductoCompuestoCocina,StockProductoCompuestoCocinaAdmin)

    
class CocinaAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Cocina._meta.fields]
    model = Cocina
admin.site.register(Cocina,CocinaAdmin)

    
class TurnoAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Turno._meta.fields]
    model = Turno
admin.site.register(Turno,TurnoAdmin)

    
class CuadreAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Cuadre._meta.fields]
    model = Cuadre
admin.site.register(Cuadre,CuadreAdmin)

    
class CantidadSubproductoAdmin(admin.ModelAdmin):
    list_display=[field.name for field in CantidadSubproducto._meta.fields]
    model = CantidadSubproducto
admin.site.register(CantidadSubproducto,CantidadSubproductoAdmin)

    
class FormulaAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Formula._meta.fields]
    model = Formula
admin.site.register(Formula,FormulaAdmin)

    
class NotaAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Nota._meta.fields]
    model = Nota
admin.site.register(Nota,NotaAdmin)


class ConsumoAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Consumo._meta.fields]
    model = Consumo
admin.site.register(Consumo,ConsumoAdmin)

