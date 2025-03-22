
import datetime
from django.shortcuts import redirect
from django.contrib.auth import logout

from django.conf import settings

def toMoneyList(val) -> str:
    l = str(val).split(".")
    start = l[0]
    if len(l) == 1: return [start,"00"]
    end =  l[1]
    if len(end) == 1: end += "0"
    return [start,end]

def toMoney(val) -> str:
    l = str(val).split(".")
    start = l[0]
    if len(l) == 1: return [start,"00"]
    end =  l[1]
    if len(end) == 1: end += "0"
    return f"{start}.{end}"


def punto_venta_required(view_func):
    def wrapper(request, *args, **kwargs):
        if len(request.user.puntos_venta.all()) == 0:
            logout(request)
            return redirect('login')

        return view_func(request, *args, **kwargs)
    return wrapper


def login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            logout(request)
            return redirect('login')

        return view_func(request, *args, **kwargs)
    return wrapper

def get_days_in_month(year, month):
    if month == 2:
        if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
            return 29
        else:
            return 28
    else:
        return [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]


def set_cookie(response, key, value, days_expire=365):
    if days_expire is None:
        max_age = 365 * 24 * 60 * 60  # one year
    else:
        max_age = days_expire * 24 * 60 * 60
    expires = datetime.datetime.strftime(
        datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age),
        "%a, %d-%b-%Y %H:%M:%S GMT",
    )
    response.set_cookie(
        key,
        value,
        max_age=max_age,
        expires=expires,
        domain=settings.SESSION_COOKIE_DOMAIN,
        secure=settings.SESSION_COOKIE_SECURE or None,
    )