from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.home_view, name='home'),
    path('generate/', views.generate_quiz_view, name='generate_quiz'),
    path('quiz/<uuid:quiz_id>/', views.quiz_detail_view, name='quiz_detail'),
    path('quiz/<uuid:quiz_id>/take/', views.take_quiz_view, name='take_quiz'),
    path('result/<uuid:session_id>/', views.quiz_result_view, name='quiz_result'),
]
