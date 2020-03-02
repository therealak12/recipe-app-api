from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Ingredient, Tag
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_tag(user, name='sample tag name'):
    return Tag.objects.create(user=user, name=name)


def create_ingredient(user, name='sample ing name'):
    return Ingredient.objects.create(user=user, name=name)


def create_user(email='testemail@example.com', password='testpass'):
    return get_user_model().objects.create_user(email=email, password=password)


def create_recipe(user, **params):
    defaults = {
        'title': 'sample title',
        'time_minutes': 10,
        'price': 10.00
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipesApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        response = self.client.get(RECIPES_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipesApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        response = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.all().order_by('id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_user_specific_recipes(self):
        """Test retrieving recipes for a user"""
        user2 = create_user(
            email='newemail@example.com',
            password='newpass'
        )
        create_recipe(user=self.user)
        create_recipe(user=user2)

        response = self.client.get(RECIPES_URL)
        user_recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(user_recipes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data, serializer.data)

    def test_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(create_ingredient(user=self.user))
        recipe.tags.add(create_tag(user=self.user))

        response = self.client.get(detail_url(recipe.id))
        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(response.data, serializer.data)
