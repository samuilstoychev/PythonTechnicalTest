"""
Defining views for the bonds app. 
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Bond
from .serializers import BondSerializer

class BondsList(APIView): 
    """
    List all relevant bonds, or create a new bond.
    """
    def get(self, request): 
        bonds = Bond.objects.all()
        return Response(BondSerializer(bonds, many=True).data)

    def post(self, request): 
        serializer = BondSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        