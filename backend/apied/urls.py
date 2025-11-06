# apied/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Auth Endpoints
    path('register/', views.register_view, name='api-register'),
    path('login/', views.login_view, name='api-login'),
    path('logout/', views.logout_view, name='api-logout'),
    path('user/', views.current_user_view, name='api-current-user'),

    # Project Endpoints
    path('projects/', views.projects_list_create_view, name='api-projects'),
    path('projects/<int:pk>/', views.project_detail_update_delete_view, name='api-project-detail'),
    
    # Interaction Endpoints
    path('projects/<int:pk>/like/', views.like_toggle_view, name='api-like-toggle'),
    path('projects/<int:pk>/comments/', views.comment_list_create_view, name='api-comments'),
    path('projects/<int:pk>/resources/', views.resource_list_create_view, name='api-resources'),

    # --- NEW: Comment Deletion Endpoint ---
    path('projects/<int:pk>/comments/<int:comment_id>/', views.comment_delete_view, name='api-comment-delete'),

    # --- NEW: Search Endpoint ---
    path('search/', views.project_search_view, name='api-search'),

    # Portfolio Endpoint
    path('portfolio/<str:username>/', views.user_portfolio_view, name='api-user-portfolio'),
    
    # --- NEW: Service Request Endpoints ---
    path('service-request/create/', views.service_request_create_view, name='api-service-request-create'),
    path('service-request/view/', views.service_request_detail_view, name='api-service-request-detail'),

    # --- NEW: Tariff Endpoint ---
    path('tariffs/', views.tariff_list_view, name='api-tariffs'),
]
