from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def sample_user(email='testemail@example.com', password='testpass'):
    """Create and return a sample user"""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):

    def test_create_user_with_email(self):
        """Test if a user is created with an email"""
        email = 'somemail@example.com'
        password = 'somepass'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_created_user_email_normalized(self):
        email = 'testmail@ExAmPle.CoM'
        user = get_user_model().objects.create_user(email, 'testpass')

        self.assertEqual(email.lower(), user.email)

    def test_created_user_no_mail_invalid(self):
        """Test that a new user cannot be created without email"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'testpass')

    def test_create_superuser(self):
        superuser = get_user_model().objects.create_superuser(
            email='somemail@example.com',
            password='somepass'
        )

        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)

    def test_tag_str(self):
        """Test the tag __str__ method"""
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='TagName'
        )

        self.assertEqual(str(tag), tag.name)
