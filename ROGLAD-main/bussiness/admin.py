from django.contrib import admin
from django.utils import timezone
from .models import (Almacen, Cuadre, GastosRecepcion, Medida,Categoria, Nota, Pago, Producto, InformeRecepcion, StockAlmacen, 
                     PuntoVenta, Transferencia, StockPuntoVenta, Cuenta, Turno, UserAccount, Venta, Descuentos,AlertaAdmin, FormulaTransformacion)


admin.site.register(Medida)
admin.site.register(Categoria)

class ProductoAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Producto._meta.fields]
    search_fields = ["id","codigo","nombre","descripcion"]
    list_filter = ["categoria",]
    model = Producto
    
class StockAlmacenAdmin(admin.ModelAdmin):
    list_display=[field.name for field in StockAlmacen._meta.fields]
    list_display.insert(5,"producto_precio_venta")
    

    @admin.display(empty_value="???")
    def producto_precio_venta(self, obj):
        return obj.producto.precio_venta
    
    search_fields = ["id","almacen__nombre","producto__nombre","lote"]
    list_filter = ["almacen__nombre","activo"]
    model = StockAlmacen

class StockPvAdmin(admin.ModelAdmin):
    list_display=[field.name for field in StockPuntoVenta._meta.fields]
    
    search_fields = ["id","lote__almacen__nombre","producto__nombre"]
    list_filter = ["punto_venta__nombre","lote__almacen__nombre","activo"]
    model = StockPuntoVenta


def recepcionar_informe_recepcion(modeladmin, request, queryset):    
    for ir in queryset:
        stock = StockAlmacen.objects.filter(informe_recepcion=ir)
        for s in stock:
            s.cantidad_inicial = s.cantidad_factura
            s.cantidad_actual = s.cantidad_factura
            s.activo = True
            s.save()
        ir.activo = True
        ir.date_confirm = timezone.now()
        ir.user_confirmacion = request.user.user_str()
        ir.save()


recepcionar_informe_recepcion.short_description = "Completar informe recepcion"

class InformeRecepcionAdmin(admin.ModelAdmin):
    list_display=[field.name for field in InformeRecepcion._meta.fields]
    
    search_fields = ["id"]
    list_filter = ["activo"]
    model = InformeRecepcion
    actions = [recepcionar_informe_recepcion,]

class TurnoAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Turno._meta.fields]
    
    search_fields = ["id","punto_venta__nombre","user__user"]
    list_filter = ["punto_venta__nombre","user__user"]
    model = Turno
    
class CuentaAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Cuenta._meta.fields]
    
    search_fields = ["id","nombre","punto_venta__nombre","user__user"]
    list_filter = ["punto_venta__nombre","user__user","abierta"]
    model = Cuenta
    
    
class VentaAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Venta._meta.fields]
    
    search_fields = ["id","producto__nombre",]
    list_filter = ["cuenta__punto_venta__nombre","cuenta__user__user",]
    model = Venta
    
    
def limpiar_stock(modeladmin, request, queryset):    
    for almacen in queryset:
        stock = StockAlmacen.objects.filter(almacen=almacen)
        stock.update(cantidad_actual=0.0)

limpiar_stock.short_description = "Limpiar Stock"

class AlmacenAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Almacen._meta.fields]    
    model = Almacen
    actions = [limpiar_stock,]


class TransferenciaAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Transferencia._meta.fields]
    list_display.append("cant_transferido")
    
    search_fields = ["id",]
    list_filter = ["emisor_id","receptor_id",]
    model = Transferencia

class DescuentosAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Descuentos._meta.fields]    
    model = Descuentos

class PagoAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Pago._meta.fields]   
    search_fields = ["descripcion",] 
    list_filter = ["user_name",]
    model = Pago

admin.site.register(Producto,ProductoAdmin)
admin.site.register(StockAlmacen,StockAlmacenAdmin)
admin.site.register(StockPuntoVenta,StockPvAdmin)
admin.site.register(InformeRecepcion,InformeRecepcionAdmin)
admin.site.register(Turno,TurnoAdmin)
admin.site.register(Cuenta,CuentaAdmin)
admin.site.register(Venta,VentaAdmin)
admin.site.register(Almacen,AlmacenAdmin)
admin.site.register(Transferencia,TransferenciaAdmin)
admin.site.register(Descuentos,DescuentosAdmin)
admin.site.register(Pago,PagoAdmin)


admin.site.register(FormulaTransformacion)
admin.site.register(PuntoVenta)
admin.site.register(Nota)
admin.site.register(Cuadre)
admin.site.register(GastosRecepcion)

admin.site.register(UserAccount)
admin.site.register(AlertaAdmin)



