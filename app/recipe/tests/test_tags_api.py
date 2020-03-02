from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe
from recipe.serializers import TagSerializer


TAGS_URL = reverse('recipe:tag-list')


def create_user(email='testemail@example.com', password='testpass'):
    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagsApiTests(TestCase):
    """Test the publicly available tags API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        response = self.client.get(TAGS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Test the authorized user tags API"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        Tag.objects.create(user=self.user, name='TagName 1')
        Tag.objects.create(user=self.user, name='TagName 2')

        response = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_user_specific_tags(self):
        """Test that tags returned are for the current user"""
        user2 = create_user(
            'user2@example.com',
            'user2pass'
        )
        user_tag = Tag.objects.create(user=self.user, name='user1_tag')
        Tag.objects.create(user=user2, name='user2_tag')

        response = self.client.get(TAGS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], user_tag.name)

    def test_create_tag_successful(self):
        payload = {'name': 'Test tag'}
        response = self.client.post(TAGS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        exists = Tag.objects.filter(
            user=self.user, name=payload['name']).exists()
        self.assertTrue(exists)

    def create_invalid_tag(self):
        """Test creating a tag with invalid payload fails"""
        payload = {'name': ''}
        response = self.client.post(TAGS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_assigned_tags_only(self):
        """Test getting only tags that are assigned to some recipe"""
        tag1 = Tag.objects.create(user=self.user, name='tag name 1')
        tag2 = Tag.objects.create(user=self.user, name='tag name 2')

        recipe = Recipe.objects.create(
            title='recipe 1',
            time_minutes=10,
            price=35.00,
            user=self.user
        )
        recipe.tags.add(tag1)

        response = self.client.get(TAGS_URL, {'assigned_only': 1})

        tag1_serializer = TagSerializer(tag1)
        tag2_serializer = TagSerializer(tag2)
        self.assertIn(tag1_serializer.data, response.data)
        self.assertNotIn(tag2_serializer.data, response.data)
