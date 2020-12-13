"""
Defines serializers.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from bonds.models import Bond

class BondSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    class Meta:
        model = Bond
        fields = ['isin', 'size', 'currency', 'maturity', 'lei', 'legal_name', 'owner']

    def create(self, validated_data):
        return Bond.objects.create(**validated_data)

class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['id', 'username', 'password']
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    