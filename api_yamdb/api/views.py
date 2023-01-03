from api.serializers import (CategorySerializer, CommentSerializer,
                             GenreSerializer, GetTokenSerializer,
                             ReviewSerializer, SignUpSerializer,
                             TitleCreateSerializer, TitleSerializer,
                             UserSerializer)
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.db import IntegrityError
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from rest_framework import mixins, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken
from reviews.models import Category, Genre, Review, Title
from users.models import User

from .filters import TitleFilter
from .permissions import AuthorStaffOrReadOnly, IsAdmin, IsAdminOrReadOnly


class UpdateDeleteViewSet(mixins.CreateModelMixin,
                          mixins.ListModelMixin,
                          mixins.DestroyModelMixin,
                          viewsets.GenericViewSet
                          ):
    pass


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    search_fields = ('username', )
    lookup_field = 'username'

    @action(
        methods=['get', 'patch'],
        detail=False,
        url_path='me',
        permission_classes=[IsAuthenticated, ]
    )
    def get_patch_me(self, request):
        user = get_object_or_404(User, username=self.request.user)
        if request.method == 'GET':
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        if request.method == 'PATCH':
            serializer = UserSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            if (
                (request.data.get('role') is not None)
                    and request.user.role == 'user'):
                serializer.save(role='user')
            return Response(serializer.data, status=status.HTTP_200_OK)
        return None


class CategoryViewSet(UpdateDeleteViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsAdminOrReadOnly
    ]
    search_fields = ('name', 'slug')
    lookup_field = 'slug'


class GenreViewSet(UpdateDeleteViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsAdminOrReadOnly
    ]
    search_fields = ('name',)
    lookup_field = 'slug'


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all()
    serializer_class = TitleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          IsAdminOrReadOnly, ]
    filterset_class = TitleFilter
    filterset_fields = ('year',)

    def get_serializer(self, *args, **kwargs):
        if self.action in ('create', 'update', 'partial_update'):
            return TitleCreateSerializer(*args, **kwargs)
        return self.serializer_class(*args, **kwargs)

    def get_queryset(self):
        return (
            Title.objects
            .prefetch_related('genre')
            .select_related('category')
            .annotate(rating=Avg('reviews__score'))
        )


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        AuthorStaffOrReadOnly,
    ]

    def get_queryset(self):
        review = get_object_or_404(Review, id=self.kwargs.get('review_id'))
        return review.comments.all()

    def perform_create(self, serializer):
        review = get_object_or_404(Review, id=self.kwargs.get('review_id'))
        return serializer.save(author=self.request.user, review=review)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        AuthorStaffOrReadOnly,
    ]

    def get_queryset(self):
        title = get_object_or_404(Title, id=self.kwargs.get('title_id'))
        return Review.objects.filter(title=title)

    def perform_create(self, serializer):
        title = get_object_or_404(Title, id=self.kwargs.get('title_id'))
        if Review.objects.filter(author=self.request.user,
                                 title=title).exists():
            raise serializers.ValidationError(
                'Вы уже оставили отзыв на этот произведение')
        serializer.save(author=self.request.user, title=title)


class APIGetToken(APIView):
    """
    Получение JWT-токена в обмен на username и confirmation code.
    Права доступа: Доступно без токена. Пример тела запроса:
    {
        "username": "string",
        "confirmation_code": "string"
    }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = GetTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            user = User.objects.get(username=data.get('username'))
        except User.DoesNotExist:
            return Response(
                {'username': 'Пользователь не найден!'},
                status=status.HTTP_404_NOT_FOUND)

        if data.get('confirmation_code') == user.confirmation_code:
            token = AccessToken.for_user(user)
            return Response({'token': str(token)},
                            status=status.HTTP_201_CREATED)
        return Response(
            {'confirmation_code': 'Неверный код подтверждения!'},
            status=status.HTTP_400_BAD_REQUEST)


class APISignup(APIView):
    """
    Получить код подтверждения на переданный email. Права доступа: Доступно без
    токена. Пример тела запроса:
    {
        "email": "string",
        "username": "string"
    }
    """
    permission_classes = [permissions.AllowAny]

    def send_email(self, data):
        email = EmailMessage(
            subject=data.get('email_subject'),
            body=data.get('email_body'),
            to=[data.get('to_email')]
        )
        email.send()

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user, _ = (
                User
                .objects
                .get_or_create(
                    **serializer.validated_data
                )
            )
        except IntegrityError:
            return Response(
                {'username': 'Пользователь с таким именем уже существует!'},
                status=status.HTTP_400_BAD_REQUEST)
        confirmation_code = default_token_generator.make_token(user)
        user.confirmation_code = confirmation_code
        user.save()
        email_body = (
            f'Здравствуйте, {user.username}.'
            f'\nКод подтверждения для доступа к API: {confirmation_code}'
        )
        data = {
            'email_body': email_body,
            'to_email': user.email,
            'email_subject': 'Код подтверждения для доступа к API!'
        }
        self.send_email(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
