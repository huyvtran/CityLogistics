import datetime

from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from .base import FVHAPITestCase


class OutgoingPackagesTests(FVHAPITestCase):
    def test_list_outgoing_packages_anonymous(self):
        # Given that no user is signed in
        # When requesting the list of outgoing packages
        url = reverse('outgoing_package-list')
        response = self.client.get(url)

        # Then an Unauthorized response is received:
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_empty_list_of_outgoing_packages(self):
        # Given that there are no packages registered for delivery
        # And that a user is signed in
        self.create_and_login_courier()

        # When requesting the list of outgoing packages
        url = reverse('outgoing_package-list')
        response = self.client.get(url)

        # Then an OK response is received:
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # And it contains an empty list:
        self.assertEqual(response.data, [])

    def test_get_new_package_schema(self):
        # Given that a user is signed in
        courier = self.create_and_login_courier()

        # When requesting the schema for a new package over ReST
        url = reverse('outgoing_package-jsonschema')
        response = self.client.get(url)

        # Then an OK response is received:
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assert_dict_contains(response.data, {
            'type': 'object',
            'properties': {
                'pickup_at': {
                    'type': 'object',
                    'required': ['lat', 'lon', 'street_address', 'postal_code', 'city', 'country'],
                    'title': 'Pickup at'
                },
                'deliver_to': {
                    'type': 'object',
                    'required': ['lat', 'lon', 'street_address', 'postal_code', 'city', 'country'],
                    'title': 'Deliver to'
                },
                'height': {
                    'type': 'integer', 'title': 'Height', 'description': 'in cm'},
                'width': {
                    'type': 'integer', 'title': 'Width', 'description': 'in cm'},
                'depth': {
                    'type': 'integer', 'title': 'Depth', 'description': 'in cm'},
                'weight': {
                    'type': 'string',
                    'pattern': '^\\-?[0-9]*(\\.[0-9]{1,2})?$',
                    'title': 'Weight',
                    'description': 'in kg'},
                'recipient': {
                    'type': 'string', 'maxLength': 128, 'minLength': 1, 'title': 'Recipient'},
                'recipient_phone': {
                    'type': 'string', 'maxLength': 32, 'minLength': 1, 'title': 'Recipient phone number'},
                'earliest_pickup_time': {
                    'type': 'string', 'format': 'date-time', 'title': 'Earliest pickup time'},
                'latest_pickup_time': {
                    'type': 'string', 'format': 'date-time', 'title': 'Latest pickup time'},
                'earliest_delivery_time': {
                    'type': 'string', 'format': 'date-time', 'title': 'Earliest delivery time'},
                'latest_delivery_time': {
                    'type': 'string', 'format': 'date-time', 'title': 'Latest delivery time'}
            },
            'required': [
                'pickup_at', 'deliver_to', 'height', 'width', 'depth', 'weight', 'recipient', 'recipient_phone',
                'earliest_pickup_time', 'latest_pickup_time', 'earliest_delivery_time', 'latest_delivery_time'
            ]
        })

        self.assert_dict_contains(response.data['properties']['pickup_at'], {
            'properties': {
                'street_address': {
                    'type': 'string',
                    'maxLength': 128,
                    'minLength': 1,
                    'title': 'Street address'},
                'postal_code': {
                    'type': 'string',
                    'maxLength': 16,
                    'minLength': 1,
                    'title': 'Postal code'},
                'city': {
                    'type': 'string',
                    'maxLength': 64,
                    'minLength': 1,
                    'title': 'City'},
                'country': {
                    'type': 'string',
                    'maxLength': 64,
                    'minLength': 1,
                    'title': 'Country'},
                'lat': {'type': 'string', 'pattern': '^\\-?[0-9]*(\\.[0-9]{1,8})?$', 'title': 'Lat'},
                'lon': {'type': 'string', 'pattern': '^\\-?[0-9]*(\\.[0-9]{1,8})?$', 'title': 'Lon'}
            }
        })

    def test_register_outgoing_package(self):
        # Given that there are no packages registered for delivery
        # And that a user is signed in
        sender = self.create_sender()
        self.client.force_login(sender)

        # When requesting to register a new package for delivery
        url = reverse('outgoing_package-list')
        now = timezone.now()
        fields = {
            "pickup_at": {
                "street_address": "Paradisäppelvägen 123",
                "postal_code": "00123",
                "city": "Ankeborg",
                "country": "Ankerige",
                "lat": "64.04000000",
                "lon": "80.65000000"
            },
            "deliver_to": {
                "street_address": "Helvetesapelsinvägen 666",
                "postal_code": "00321",
                "city": "Ankeborg",
                "country": "Ankerige",
                "lat": "64.54000000",
                "lon": "80.05000000"
            },
            "height": 20,
            "width": 30,
            "depth": 20,
            "weight": "2.00",
            "recipient": "Reginald Receiver",
            "recipient_phone": "+358505436657",
        }

        timestamps = {
            "earliest_pickup_time": now,
            "latest_pickup_time": now + datetime.timedelta(hours=1),

            "earliest_delivery_time": now + datetime.timedelta(hours=1),
            "latest_delivery_time": now + datetime.timedelta(hours=2)
        }
        response = self.client.post(url, dict(fields, **timestamps), format='json')

        # Then an OK response is received with the created package:
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assert_dict_contains(response.data, fields)

        # And when subsequently requesting the list of outgoing packages
        response = self.client.get(url)

        # Then an OK response is received:
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # And it contains the registered package:
        self.assertEqual(len(response.data), 1)
        self.assert_dict_contains(response.data[0], fields)