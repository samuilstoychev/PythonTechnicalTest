"""
Tests for the `bonds` application.
"""
from rest_framework.test import APITestCase
from rest_framework import status
import requests
import responses
from bonds.models import Bond
from bonds.serializers import BondSerializer, UserSerializer
from bonds.constants import GLEIF_API_ENDPOINT
from django.contrib.auth.models import User
from rest_framework.test import force_authenticate

class RoutingTest(APITestCase):
    """
    Tests for the routing of the API (as defined in origin/urls.py)
    """
    def test_bonds_path_returns_200_for_authenticated_users(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        login = self.client.login(username='testuser', password='testpass')
        resp = self.client.get("/bonds/")
        assert resp.status_code == status.HTTP_200_OK
    
    def test_bonds_path_returns_403_for_anonymous_users(self): 
        resp = self.client.get("/bonds/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN
    
    def test_admin_path_returns_302(self):
        resp = self.client.get("/admin/")
        assert resp.status_code == status.HTTP_302_FOUND

    def test_wrong_path_returns_404(self):
        resp = self.client.get("/foobar/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
    
MOCK_POST_DATA = {
    "isin": "FR0000131104",
    "size": 100000000,
    "currency": "EUR",
    "maturity": "2025-02-28",
    "lei": "R0MUWSFPU8MPRO8K5P83"
}

MOCK_GLEIF_RESPONSE = [{"Entity":{"LegalName":{"$":"MOCK BANK"}}}]

class GetAndPostTest(APITestCase):
    """
    Tests for the GET and POST request logic in views.py. 
    Requests to the GLEIF API are mocked. 
    """
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')

    def test_return_empty_list_if_no_bonds(self):
        resp = self.client.get("/bonds/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        assert not resp.json()

    # Using the `responses` library to mock requests to the GLEIF API. 
    @responses.activate
    def test_post_request_creates_a_bond(self):
        # This will return a mock response from the call to requests.get
        responses.add(responses.GET, GLEIF_API_ENDPOINT, json=MOCK_GLEIF_RESPONSE, status=200)
        self.assertEqual(Bond.objects.count(), 0)
        resp = self.client.post("/bonds/", MOCK_POST_DATA, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Bond.objects.count(), 1)
        self.assertEqual(Bond.objects.get().isin, MOCK_POST_DATA["isin"])
    
    @responses.activate
    def test_post_request_translates_legal_name(self):
        responses.add(responses.GET, GLEIF_API_ENDPOINT, json=MOCK_GLEIF_RESPONSE, status=200)
        self.client.post("/bonds/", MOCK_POST_DATA, format='json')
        self.assertEqual(Bond.objects.get().legal_name, "MOCKBANK")

    @responses.activate
    def test_unspecified_lei_returns_400(self):
        INVALID_POST_DATA = MOCK_POST_DATA.copy()
        del INVALID_POST_DATA["lei"]
        resp = self.client.post("/bonds/", INVALID_POST_DATA, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
    
    @responses.activate
    def test_invalid_lei_returns_400(self):
        # Mock status 400 response (LEI provided has invalid length/characters)
        responses.add(responses.GET, GLEIF_API_ENDPOINT, json={'message': 'Invalid LEI'}, status=400)
        INVALID_POST_DATA = MOCK_POST_DATA.copy()
        INVALID_POST_DATA["lei"] = "AAAAAAAAAAAAAAAAAAAA"
        resp = self.client.post("/bonds/", INVALID_POST_DATA, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
    
    @responses.activate
    def test_nonexistent_lei_returns_400(self):
        # Mock empty response (LEI has valid length but does not correspond to a legal name)
        responses.add(responses.GET, GLEIF_API_ENDPOINT, json=[], status=200)
        resp = self.client.post("/bonds/", MOCK_POST_DATA, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
    
    @responses.activate
    def test_failed_gleif_request_returns_503(self):
        # Mock a failed call to requests.get (e.g. due to timeout or GLEIF API being down) 
        responses.add(responses.GET, GLEIF_API_ENDPOINT, body=Exception('...'))

        resp = self.client.post("/bonds/", MOCK_POST_DATA, format='json')
        self.assertEqual(resp.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
    
    @responses.activate
    def test_get_returns_all_relevant_bonds(self):
        responses.add(responses.GET, GLEIF_API_ENDPOINT, json=MOCK_GLEIF_RESPONSE, status=200)
        responses.add(responses.GET, GLEIF_API_ENDPOINT, json=MOCK_GLEIF_RESPONSE, status=200)
        self.client.post("/bonds/", MOCK_POST_DATA, format='json')
        self.client.post("/bonds/", MOCK_POST_DATA, format='json')
        resp = self.client.get("/bonds/")
        self.assertEqual(len(resp.json()), 2)
    
    @responses.activate
    def test_users_only_see_their_bonds(self):
        responses.add(responses.GET, GLEIF_API_ENDPOINT, json=MOCK_GLEIF_RESPONSE, status=200)
        self.client.post("/bonds/", MOCK_POST_DATA, format='json')
        self.client.logout()
        self.user = User.objects.create_user(username='anotheruser', password='testpass')
        self.client.login(username='anotheruser', password='testpass')
        self.client.post("/bonds/", MOCK_POST_DATA, format='json')
        resp = self.client.get("/bonds/")
        # Assert `anotheruser` only sees their own post 
        self.assertEqual(len(resp.json()), 1)
    
    @responses.activate
    def test_query_parameters_filter_bonds(self):
        responses.add(responses.GET, GLEIF_API_ENDPOINT, json=MOCK_GLEIF_RESPONSE, status=200)
        self.client.post("/bonds/", MOCK_POST_DATA, format='json')
        EDITED_POST_DATA = MOCK_POST_DATA.copy()
        EDITED_POST_DATA["currency"] = "USD"
        self.client.post("/bonds/", EDITED_POST_DATA, format='json')
        resp = self.client.get("/bonds/?currency=USD")
        # Only show the bond with USD currency
        self.assertEqual(len(resp.json()), 1)
    
    @responses.activate
    def test_invalid_params_return_query(self):
        responses.add(responses.GET, GLEIF_API_ENDPOINT, json=MOCK_GLEIF_RESPONSE, status=200)
        self.client.post("/bonds/", MOCK_POST_DATA, format='json')
        # Invalid query value since `size` is an integer
        resp = self.client.get("/bonds/?size=foobar")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

MOCK_BOND_ATTRIBUTES = {
    "isin": "foobar",
    "size": 100000000,
    "currency": "foo",
    "maturity": "2020-02-20",
    "lei": "foobar", 
    "legal_name": "foobar"
}

class BondSerializerTest(APITestCase):
    """
    Tests for the BondSerializer defined in bonds/serializers.py.
    """
    def test_serialized_bond_has_correct_fields(self):
        bond = Bond(**MOCK_BOND_ATTRIBUTES)
        bond_serializer = BondSerializer(instance=bond)
        bond_data = bond_serializer.data
        self.assertEqual(set(bond_data.keys()), set(['isin', 'size', 'currency', 'maturity', 'lei', 'legal_name', 'owner']))
    
    def test_serializer_serializes_valid_data_correctly(self): 
        bond_serializer = BondSerializer(data=MOCK_BOND_ATTRIBUTES)
        assert bond_serializer.is_valid()
    
    def test_serializer_detects_invalid_data(self): 
        INVALID_BOND_ATTRIBUTES = MOCK_BOND_ATTRIBUTES.copy() 
        # Entering a non-existent date
        INVALID_BOND_ATTRIBUTES["maturity"] = "2020-99-10"
        bond_serializer = BondSerializer(data=INVALID_BOND_ATTRIBUTES)
        assert not bond_serializer.is_valid()

MOCK_USER_ATTRIBUTES = {
    "username": "testuser",
    "password": "testpassword"
}

class UserSerializerTest(APITestCase):
    """
    Tests for the UserSerializer defined in bonds/serialisers.py.
    """
    def test_serialized_bond_has_correct_fields(self):
        user = User.objects.create_user(username='testuser', password='testpass')
        user_serializer = UserSerializer(instance=user)
        user_data = user_serializer.data
        self.assertEqual(set(user_data.keys()), set(['id', 'username', 'password']))

    def test_serializer_serializes_valid_data_correctly(self): 
        user_serializer = UserSerializer(data={"username": "testuser", "password": "testpass"})
        assert user_serializer.is_valid()
    
    def test_serializer_detects_invalid_data(self): 
        # Missing password field
        user_serializer = UserSerializer(data={"username": "testuser"})
        assert not user_serializer.is_valid()