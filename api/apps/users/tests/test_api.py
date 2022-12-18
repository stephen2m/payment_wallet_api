from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

PASSWORD = 'hackobob'


def create_user(email_address='user@example.com', password=PASSWORD):
    return get_user_model().objects.create_user(
        email=email_address,
        full_name='Ozzy Osbourne',
        short_name='Ozzy',
        password=password
    )


class AuthenticationTest(APITestCase):
    def test_user_can_enroll(self):
        response = self.client.post(reverse('signup'), data={
            'email': 'user@example.com',
            'full_name': 'Ozzy Osbourne',
            'short_name': 'Ozzy',
            'password': PASSWORD
        })
        user = get_user_model().objects.last()

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(response.data['email'], user.email)
        self.assertEqual(response.data['full_name'], user.full_name)

    def test_user_can_log_in(self):
        user = create_user()
        response = self.client.post(reverse('signin'), data={
            'username': user.username,
            'password': PASSWORD,
        })

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertIsNotNone(response.data['user'])
        self.assertIsNotNone(response.data['wallet'])
        self.assertIsNotNone(response.data['tokens'])
