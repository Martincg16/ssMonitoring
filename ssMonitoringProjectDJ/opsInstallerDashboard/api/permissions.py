import os

from rest_framework.permissions import BasePermission


class HasApiKey(BasePermission):
    """
    Allows access only if the request includes a valid X-API-Key header.
    The key is checked against the OPS_API_KEY environment variable.
    """

    def has_permission(self, request, view):
        api_key = request.headers.get('X-API-Key', '')
        expected = os.environ.get('OPS_API_KEY', '')
        return api_key and api_key == expected
