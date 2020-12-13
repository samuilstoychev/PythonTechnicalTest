"""
Defines views for the bonds app.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework import generics
import requests
from .models import Bond
from .serializers import BondSerializer
from .constants import GLEIF_API_ENDPOINT
from bonds.serializers import UserSerializer
from rest_framework import permissions
from rest_framework.permissions import AllowAny

class InvalidLEIException(Exception):
    pass

class BondsList(APIView):
    """
    List all relevant bonds, or create a new bond.
    """
    # Make this view accessible for authenticated users only
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        bonds = Bond.objects.all().filter(owner=request.user)
        return Response(BondSerializer(bonds, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):

        try:
            legal_name =self.get_legal_name(request)
        # Return 503 if error due to unsuccessful get request.
        except ConnectionError as e:
            return Response(str(e), status=status.HTTP_503_SERVICE_UNAVAILABLE)
        # Return 400 if error due to missing or invalid LEI.
        except (ValueError, InvalidLEIException) as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

        request.data["legal_name"] = legal_name

        serializer = BondSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=self.request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # # TODO: Edit this method
    # def perform_create(self, serializer):
    #     serializer.save(owner=self.request.user)
    
    def get_legal_name(self, request):
        # If LEI not specified, raise an exception
        if "lei" not in request.data:
            raise ValueError("LEI not specified")

        lei = request.data["lei"]
        url = GLEIF_API_ENDPOINT +'?lei=' + lei
        # If requests.get fails, raise a ConnectionError.
        try:
            response = requests.get(url)
        except:
            raise ConnectionError("Failed to connect to the GLEIF API.")
        # If status code outside of the 200-200 range or no legal names returned, raise exception.
        if (not response.ok) or (not response.json()):
            raise InvalidLEIException("LEI " + lei + " is invalid or does not exist.")

        legal_name = response.json()[0]['Entity']['LegalName']['$']
        # Remove whitespace from the string
        return legal_name.replace(" ", "")

# Source: https://nemecek.be/blog/23/how-to-createregister-user-account-with-django-rest-framework-api
class UserRegistration(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny, )
