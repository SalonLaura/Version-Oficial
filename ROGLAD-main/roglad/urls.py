from django.urls import path
from .views import CustomLoginView
from .views import lista_stock

urlpatterns = [
    path('', CustomLoginView.as_view(), name='login'),
    #path('login/', CustomLoginView.as_view(), name='login'),
    # Agrega tus demás URLs aquí
    path('stock/', lista_stock, name='lista_stock'),
]