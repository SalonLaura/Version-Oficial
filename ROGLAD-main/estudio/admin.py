from django.contrib import admin

from estudio.models import (FichaCliente, Servicio, Fotografo, Editor, CasaImpresion, EnviosEdicion,
EnviosImpresion, TipoContrato, ServicioContrato, Contrato,Estado)

class FichaClienteAdmin(admin.ModelAdmin):
    list_display=[field.name for field in FichaCliente._meta.fields]
    model = FichaCliente

admin.site.register(FichaCliente,FichaClienteAdmin)

class EstadoAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Estado._meta.fields]
    model = Estado

admin.site.register(Estado,EstadoAdmin)


class FotografoAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Fotografo._meta.fields]
    model = Fotografo
admin.site.register(Fotografo,FotografoAdmin)

class EditorAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Editor._meta.fields]
    model = Editor
admin.site.register(Editor,EditorAdmin)

class CasaImpresionAdmin(admin.ModelAdmin):
    list_display=[field.name for field in CasaImpresion._meta.fields]
    model = CasaImpresion
admin.site.register(CasaImpresion,CasaImpresionAdmin)

class TipoContratoAdmin(admin.ModelAdmin):
    list_display=[field.name for field in TipoContrato._meta.fields]
    model = TipoContrato
admin.site.register(TipoContrato,TipoContratoAdmin)

class ServicioContratoAdmin(admin.ModelAdmin):
    list_display=[field.name for field in ServicioContrato._meta.fields]
    model = ServicioContrato
admin.site.register(ServicioContrato,ServicioContratoAdmin)


class ContratoAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Contrato._meta.fields]
    model = Contrato
admin.site.register(Contrato,ContratoAdmin)

class ServicioAdmin(admin.ModelAdmin):
    list_display=[field.name for field in Servicio._meta.fields]
    model = Servicio
admin.site.register(Servicio,ServicioAdmin)

class EnviosEdicionAdmin(admin.ModelAdmin):
    list_display=[field.name for field in EnviosEdicion._meta.fields]
    model = EnviosEdicion
admin.site.register(EnviosEdicion,EnviosEdicionAdmin)

class EnviosImpresionAdmin(admin.ModelAdmin):
    list_display=[field.name for field in EnviosImpresion._meta.fields]
    model = EnviosImpresion
admin.site.register(EnviosImpresion,EnviosImpresionAdmin)

