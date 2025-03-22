from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from .models import Usuarios

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