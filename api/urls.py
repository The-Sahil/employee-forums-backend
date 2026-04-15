from django.urls import path
from knox import views as knox_views
from .views import (
    RegisterAPI, LoginAPI, InterestListCreateAPI,
    PostListCreateAPI, FeedAPI, LikeToggleAPI,
    SendConnectionRequestAPI, PendingConnectionsAPI, AcceptConnectionAPI, DeclineConnectionAPI,
    UserRecommendationAPI
)

urlpatterns = [
    # Auth
    path('auth/register/', RegisterAPI.as_view(), name='register'),
    path('auth/login/', LoginAPI.as_view(), name='login'),
    path('auth/logout/', knox_views.LogoutView.as_view(), name='logout'),
    path('auth/logoutall/', knox_views.LogoutAllView.as_view(), name='logoutall'),

    # Interests
    path('interests/', InterestListCreateAPI.as_view(), name='interests'),

    # Posts & Feed
    path('posts/', PostListCreateAPI.as_view(), name='posts'),
    path('posts/feed/', FeedAPI.as_view(), name='feed'),
    path('posts/<int:post_id>/like/', LikeToggleAPI.as_view(), name='like_toggle'),

    # Connections
    path('connections/request/<int:user_id>/', SendConnectionRequestAPI.as_view(), name='send_request'),
    path('connections/pending/', PendingConnectionsAPI.as_view(), name='pending_requests'),
    path('connections/accept/<int:connection_id>/', AcceptConnectionAPI.as_view(), name='accept_request'),
    path('connections/decline/<int:connection_id>/', DeclineConnectionAPI.as_view(), name='decline_request'),

    # Recommendations
    path('users/recommendations/', UserRecommendationAPI.as_view(), name='recommendations'),
]
