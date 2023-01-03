from api.views import (APIGetToken, APISignup, CategoryViewSet, CommentViewSet,
                       GenreViewSet, ReviewViewSet, TitleViewSet, UserViewSet)
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router_v1 = DefaultRouter()
router_v1.register('genres', GenreViewSet, basename='genre')
router_v1.register('titles', TitleViewSet, basename='title')
router_v1.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet, basename='comment'
)
router_v1.register('categories', CategoryViewSet, basename='category')
router_v1.register('users', UserViewSet, basename='user')
router_v1.register(
    r'titles/(?P<title_id>\d+)/reviews',
    ReviewViewSet,
    basename='reviews'
)

urlpatterns = [
    path('v1/', include(router_v1.urls)),
    path('v1/auth/token/', APIGetToken.as_view(), name='get_token'),
    path('v1/auth/signup/', APISignup.as_view(), name='signup'),
]
