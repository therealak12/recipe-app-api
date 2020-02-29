from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


def create_user(email='testemail@example.com', password='testpass'):
    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientsApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required to access ingredients endpoint"""
        response = self.client.get(INGREDIENTS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        Ingredient.objects.create(user=self.user, name='Ing Name 1')
        Ingredient.objects.create(user=self.user, name='Ing Name 2')

        response = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_user_specific_ingredients(self):
        user_ingredient = Ingredient.objects.create(
            user=self.user, name='user_ing_name')

        user2 = create_user(
            email='newemail@example.com',
            password='newpass'
        )
        Ingredient.objects.create(user=user2, name='user2_ing_name')

        response = self.client.get(INGREDIENTS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], user_ingredient.name)

    def test_create_ingredient_success(self):
        payload = {'name': 'ing name'}
        response = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        exists = Ingredient.objects.filter(
            user=self.user, name=payload['name']).exists()
        self.assertTrue(exists)

    def test_create_invalid_ingredient_fails(self):
        payload = {'name': ''}
        response = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
