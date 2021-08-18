from django.urls import path
from django.contrib.auth.views import LogoutView, LoginView
from . import views

urlpatterns = [
    path('signup/', views.SignUp.as_view(), name='signup'),
    path('logout/',
         LogoutView.as_view(template_name='registration/logged_out.html'),
         name='logout'),
    path('login/',
         LoginView.as_view(template_name='registration/login.html'),
         name='login')
]
