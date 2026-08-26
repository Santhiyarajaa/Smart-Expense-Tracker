"""
Serializers for the Smart Expense Tracker REST API.
These translate Expense/Budget/User model instances to/from JSON for
the Flutter mobile app (and any other API client) without touching
the existing Django template views at all.
"""
from django.contrib.auth.models import User
from rest_framework import serializers

from .category_predictor import predict_category
from .models import Budget, Expense


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('This username is already taken.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class ExpenseSerializer(serializers.ModelSerializer):
    """
    `category` is read-only from the client's perspective: it is always
    (re)computed server-side from `description` via the same
    keyword-based predictor used by the web app, so the API and the web
    UI can never disagree on what category an expense belongs to.
    """

    class Meta:
        model = Expense
        fields = [
            'id', 'description', 'amount', 'category',
            'date', 'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'category', 'created_at', 'updated_at']

    def validate_amount(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError('Amount must be greater than 0.')
        return value

    def validate_description(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Description is required.')
        return value

    def create(self, validated_data):
        validated_data['category'] = predict_category(validated_data['description'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        new_description = validated_data.get('description', instance.description)
        if new_description != instance.description:
            validated_data['category'] = predict_category(new_description)
        return super().update(instance, validated_data)


class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ['id', 'monthly_budget', 'month', 'year', 'created_at', 'updated_at']
        read_only_fields = ['id', 'month', 'year', 'created_at', 'updated_at']

    def validate_monthly_budget(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError('Monthly budget must be greater than 0.')
        return value
