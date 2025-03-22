from django import template

register = template.Library()

@register.filter
def sum_importe_inicial(obj):
    try:
        total = round(float(sum(objeto.importe_inicial() for objeto in obj)),2)
        total_list = str(total).split(".")
        if len(str(total_list[1])) == 1: total_list[1] = str(total_list[1]) + "0"
        return total_list
    except:
        return ["0","00"]

@register.filter
def sum_importe_remitido(obj):
    try:
        total = round(float(sum(objeto.importe_remitido() for objeto in obj)),2)
        total_list = str(total).split(".")
        if len(str(total_list[1])) == 1: total_list[1] = str(total_list[1]) + "0"
        return total_list
    except:
        return ["0","00"]

@register.filter
def sum_importe_recibido(obj):
    try:
        total = round(float(sum(objeto.importe_recibido() for objeto in obj)),2)
        total_list = str(total).split(".")
        if len(str(total_list[1])) == 1: total_list[1] = str(total_list[1]) + "0"
        return total_list
    except:
        return ["0","00"]



@register.filter
def divide(obj,valor):
    try:
        return float(obj)/float(valor)
    except:
        return 0.0

@register.filter
def concatenate(obj,valor):
    try:
        return str(obj)+str(valor)
    except:
        return 0.0

@register.filter
def multiplica(obj,valor):    
    try:
        return float(obj)*float(valor)
    except:
        return 0.0

@register.filter
def parseFloat(obj):
    try:
        return str(round(float(obj),2)).replace(",",".")
    except: return "0.0"

@register.filter
def parseFloatOrNull(obj):
    if obj == None: return ""
    try:
        return str(round(float(obj),2)).replace(",",".")
    except: 
        return ""


@register.filter
def parseFloatOrBlank(obj):
    try:        
        if obj == None:return "-"
        return str(obj).replace(",",".")
    except:
        return "-"

@register.filter
def toMoneyList(objet) -> str:
    try:
        l = str(round(float(objet),2)).split(".")
        start = l[0]
        if len(l) == 1: return [start,"00"]
        end =  l[1]
        if len(end) == 1: end += "0"
        return [start,end]
    except:
        return ["0","00"]

@register.filter
def toMoney(objet) -> str:
    try:
        objet = round(float(objet),2)
        l = str(objet).split(".")
        start = l[0]
        if len(l) == 1: return f"{start}.00"
        end =  l[1]
        if len(end) == 1: end += "0"
        m = f"{start}.{end}"
        if m == "-0.00":m="0.00"
        return m
    except:
        return "0.00"

@register.filter
def nullToBlank(objet) -> str:
    if objet == None: return "-"
    else: return objet

@register.filter
def nullToNone(objet) -> str:
    if objet == None: return ""
    else: return objet

@register.filter
def blankShow(objet) -> str:
    try:
        if objet == None: return "-"
        if objet == "": return "-"
        else: return objet
    except:
        return "-"

@register.filter
def mod(obj):
    try:
        if obj < 0:return obj * -1
        return obj
    except:
        return obj
    

import urllib.parse
@register.filter
def parseUrl(objet) -> str:
    return urllib.parse.quote(objet)






@register.filter
def next(some_list, current_index):
    try:
        return some_list[int(current_index) + 1] # access the next element
    except:
        return '' # return empty string in case of exception

@register.filter
def previous(some_list, current_index):
    try:
        return some_list[int(current_index) - 1] # access the previous element
    except:
        return '' # return empty string in case of exception