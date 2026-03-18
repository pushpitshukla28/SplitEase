from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard_root'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('trips/create/', views.create_trip, name='create_trip'),
    path('trips/<int:pk>/', views.trip_detail, name='trip_detail'),
    path('trips/<int:trip_pk>/add-expense/', views.add_expense, name='add_expense'),
    path('expenses/<int:expense_pk>/delete/', views.delete_expense, name='delete_expense'),
    path('personal/', views.personal_expenses, name='personal_expenses'),
    path('personal/<int:pk>/delete/', views.delete_personal_expense, name='delete_personal_expense'),
]
