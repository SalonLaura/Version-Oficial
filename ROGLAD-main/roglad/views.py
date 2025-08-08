from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.shortcuts import render
from .models import Usuarios
from bussiness.models import StockAlmacen, Producto, StockPuntoVenta 

class CustomLoginView(auth_views.LoginView):
    template_name = 'registration/login.html'
    model = Usuarios
    

    def form_valid(self, form):
        business_id = self.request.POST.get('business')
        print(business_id)
        # Guardar el business_id en la sesión o procesarlo según necesites
        self.request.session['selected_business'] = business_id
        user = Usuarios.objects.get(negocio = business_id)
        
        # Redirección basada en el negocio seleccionado
        if(business_id == '1'):
            redirect_url = f'/roglad/bussiness/'
        else:
            redirect_url = f'/roglad/resguardo/'
        return redirect(redirect_url)
    
def lista_stock(request):
    productos = Producto.objects.all()  # Obtén todos los registros de stock
    almacen = StockAlmacen.objects.filter(cantidad_actual__gt=0,activo=True).order_by('producto')  # Obtén todos los registros de stock
    pv = StockPuntoVenta.objects.filter(cantidad_actual__gt=0,activo=True).order_by('producto')  # Obtén todos los registros de stock
    return render(request, 'resguardo/imprimir.html', {'productos': productos, 'productos_almacen': almacen, 'productos_pv': pv})