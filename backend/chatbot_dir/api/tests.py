import json
import os

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class SubmitFeedbackViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.submit_feedback_url = reverse('submit_feedback')
        self.test_data = {
            "prompt": "Test question?",
            "response": "Test answer.",
            "correct": 1,
            "rating": 5,
            "comments": "Test comment"
        }

    def test_submit_feedback(self):
        response = self.client.post(
            self.submit_feedback_url,
            data=json.dumps(self.test_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"message": "Feedback stored successfully"})

        # Check if the feedback was actually stored in the file
        file_path = os.path.join(os.path.dirname(__file__), "../data/database_update.json")
        self.assertTrue(os.path.exists(file_path))

        with open(file_path, 'r') as f:
            last_line = f.readlines()[-1]
            stored_data = json.loads(last_line)

        self.assertEqual(stored_data['prompt'], self.test_data['prompt'])
        self.assertEqual(stored_data['response'], self.test_data['response'])
        self.assertEqual(stored_data['correct'], self.test_data['correct'])
        self.assertEqual(stored_data['rating'], self.test_data['rating'])
        self.assertEqual(stored_data['comments'], self.test_data['comments'])

    def tearDown(self):
        # Clean up the test file after the test
        file_path = os.path.join(os.path.dirname(__file__), "../data/database_update.json")
        if os.path.exists(file_path):
            os.remove(file_path).
