from django.urls import path
from . import views

urlpatterns = [
    path('login/',  views.login_view,  name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('input/',  views.input_view,  name='input'),
    path('layout/', views.layout_view, name='layout'),
    path('layout/select/<int:layout_id>/', views.select_layout, name='select_layout'),
    path('export/', views.export_csv,  name='export_csv'),
    path('simulation/tick/', views.simulation_tick, name='simulation_tick'),
]
