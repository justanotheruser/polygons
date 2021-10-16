from django.urls import path

from . import views

app_name = 'polygons' 
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:polygon_id>/', views.DetailView.as_view(), name='detail')
]