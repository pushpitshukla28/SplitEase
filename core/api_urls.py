from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import api_views

urlpatterns = [
    # Auth
    path('auth/register/', api_views.api_register, name='api_register'),
    path('auth/login/', api_views.api_login, name='api_login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('auth/me/', api_views.api_me, name='api_me'),

    # Dashboard
    path('dashboard/', api_views.api_dashboard, name='api_dashboard'),

    # Trips
    path('trips/create/', api_views.api_create_trip, name='api_create_trip'),
    path('trips/<int:pk>/', api_views.api_trip_detail, name='api_trip_detail'),
    path('trips/<int:pk>/delete/', api_views.api_delete_trip, name='api_delete_trip'),
    path('trips/<int:trip_pk>/add-expense/', api_views.api_add_expense, name='api_add_expense'),
    path('trips/<int:trip_pk>/settle/', api_views.api_settle_up, name='api_settle_up'),

    # Expenses
    path('expenses/<int:expense_pk>/delete/', api_views.api_delete_expense, name='api_delete_expense'),

    # Personal Expenses
    path('personal/', api_views.api_personal_expenses, name='api_personal_expenses'),
    path('personal/add/', api_views.api_add_personal_expense, name='api_add_personal_expense'),
    path('personal/<int:pk>/delete/', api_views.api_delete_personal_expense, name='api_delete_personal_expense'),

    # Friends
    path('friends/', api_views.api_friends, name='api_friends'),
    path('friends/request/<int:user_id>/', api_views.api_send_friend_request, name='api_send_friend_request'),
    path('friends/accept/<int:request_id>/', api_views.api_accept_friend_request, name='api_accept_friend_request'),
    path('friends/decline/<int:request_id>/', api_views.api_decline_friend_request, name='api_decline_friend_request'),
    path('friends/remove/<int:user_id>/', api_views.api_remove_friend, name='api_remove_friend'),

    # Account
    path('account/delete/', api_views.api_delete_account, name='api_delete_account'),
]
