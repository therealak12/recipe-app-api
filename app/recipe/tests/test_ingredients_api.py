from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


def create_recipe(user, **params):
    defaults = {
        'title': 'recipe 1',
        'time_minutes': 10,
        'price': 35.00,
    }
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


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

    def test_retrieve_assigned_ingredients_only(self):
        ingredient1 = Ingredient.objects.create(
            user=self.user,
            name='ing name 1'
        )
        ingredient2 = Ingredient.objects.create(
            user=self.user,
            name='ing name 2'
        )
        recipe = create_recipe(user=self.user, title='rec 1')
        recipe.ingredients.add(ingredient1)

        response = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        ingredient_serializer1 = IngredientSerializer(ingredient1)
        ingredient_serializer2 = IngredientSerializer(ingredient2)
        self.assertIn(ingredient_serializer1.data, response.data)
        self.assertNotIn(ingredient_serializer2.data, response.data)

    def test_retrieve_assigned_returns_unique_ingredients(self):
        """Test that retreiving assigned ingredients\
             returns unique ingredients"""
        ingredient = Ingredient.objects.create(
            user=self.user, name='ingredient name')
        recipe1 = create_recipe(user=self.user, title='rec 1')
        recipe2 = create_recipe(user=self.user, title='rec 2')
        recipe1.ingredients.add(ingredient)
        recipe2.ingredients.add(ingredient)

        response = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        self.assertEqual(len(response.data), 1)
