from rest_framework import serializers
from bonds.models import Bond

class BondSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bond
        fields = ['isin', 'size', 'currency', 'maturity', 'lei', 'legal_name']
    def create(self, validated_data):
        return Bond.objects.create(**validated_data)