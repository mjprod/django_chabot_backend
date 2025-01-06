from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from unittest.mock import patch

class UserInputViewTests(APITestCase):
    """
    Tests for the UserInputView.
    """

    def setUp(self):
        self.url = reverse("user-input")  # Replace with your URL name if different.

    def test_valid_input(self):
        """
        Test valid user input and successful response.
        """
        data = {"prompt": "Hello!", "user_id": "12345"}
        response = self.client.post(self.url, data, format="json")

        # Check response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response structure
        self.assertIn("user_id", response.data)
        self.assertIn("prompt", response.data)
        self.assertIn("response", response.data)

    def test_invalid_input(self):
        """
        Test invalid input and validation errors.
        """
        data = {"prompt": ""}  # Invalid because 'prompt' is empty
        response = self.client.post(self.url, data, format="json")

        # Check response status
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Check error message
        self.assertIn("prompt", response.data)

    @patch("mixins.mongodb_mixin.MongoDBMixin.get_db")
    def test_mongodb_error(self, mock_get_db):
        """
        Test database connection failure.
        """
        # Mock MongoDB error
        mock_get_db.side_effect = Exception("Database connection failed.")

        data = {"prompt": "Test error", "user_id": "12345"}
        response = self.client.post(self.url, data, format="json")

        # Check response status
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Check error message
        self.assertIn("error", response.data)