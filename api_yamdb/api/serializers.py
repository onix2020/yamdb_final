from core.validators import validate_username
from rest_framework import serializers
from reviews.models import Category, Comment, Genre, Review, Title
from users.models import User


class GetTokenSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    confirmation_code = serializers.CharField(required=True)

    def create(self, validated_data):
        return User.objects.create(**validated_data)


class SignUpSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    username = serializers.CharField(required=True,
                                     validators=[validate_username])


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        exclude = ('id', )


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        exclude = ('id', )


class TitleSerializer(serializers.ModelSerializer):
    category = CategorySerializer(many=False)
    genre = GenreSerializer(many=True)
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        model = Title
        fields = '__all__'


class TitleCreateSerializer(serializers.ModelSerializer):
    genre = serializers.SlugRelatedField(
        slug_field='slug',
        many=True,
        queryset=Genre.objects.all()
    )
    category = serializers.SlugRelatedField(
        slug_field='slug',
        many=False,
        queryset=Category.objects.all(),
    )
    description = serializers.CharField(required=False)

    class Meta:
        model = Title
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'score', 'pub_date')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username',
                  'role',
                  'bio',
                  'email',
                  'first_name',
                  'last_name')

    def validate_username(self, value):
        return validate_username(value)
