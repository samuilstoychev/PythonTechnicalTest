"""
Defines views for the bonds app.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from django.contrib.auth.models import User
import requests
from bonds.serializers import UserSerializer
from .models import Bond
from .serializers import BondSerializer

class InvalidLEIException(Exception):
    """
    Raised when a LEI is invalid - i.e. it is malformed or does not map to a legal name.
    """
    pass

GLEIF_API_ENDPOINT = 'https://leilookup.gleif.org/api/v2/leirecords'

class BondsList(APIView):
    """
    List all relevant bonds, or create a new bond.
    """
    # Makes this view accessible for authenticated users only
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        fields = ['isin', 'size', 'currency', 'maturity', 'lei', 'legal_name']
        # Extract the preferences for each value (e.g. ?currency=EUR)
        filters = {field: self.request.GET.get(field, None) for field in fields}
        filters = {key: val for key, val in filters.items() if val is not None}
        # Forcefully filter the results by owner
        filters["owner"] = request.user

        try: 
            bonds = Bond.objects.all().filter(**filters)
        # Value error can occur if invalid query value provided (e.g. ?size=foobar)
        except ValueError: 
            return Response("Invalid query value(s) provided.", status=status.HTTP_400_BAD_REQUEST)
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

class UserRegistration(generics.CreateAPIView):
    """
    View for registering new users. Created following this tutorial: 
    https://nemecek.be/blog/23/how-to-createregister-user-account-with-django-rest-framework-api
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny, )
