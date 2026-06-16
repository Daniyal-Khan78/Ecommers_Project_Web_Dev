from rest_framework.response import Response
from rest_framework import status


def success_response(data=None, message="Success", status_code=status.HTTP_200_OK):
    """
    Returns a standardized successful API response.

    Usage examples:
        return success_response(data=serializer.data, message="Product retrieved.")
        return success_response(message="Logged out successfully.", status_code=204)

    The frontend always checks response.data.success to know if it worked.
    """
    payload = {
        "success": True,
        "message": message,
    }

    # Only include "data" key if data was actually provided.
    # This keeps responses clean for operations like delete that have no data to return.
    if data is not None:
        payload["data"] = data

    return Response(payload, status=status_code)


def error_response(message="An error occurred.", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    """
    Returns a standardized error API response.

    Usage examples:
        return error_response(message="Product not found.", status_code=404)
        return error_response(message="Validation failed.", errors=serializer.errors)

    'errors' is typically a dict of field-level validation errors from DRF serializers,
    e.g.: {"email": ["This field is required.", "Enter a valid email address."]}
    """
    payload = {
        "success": False,
        "message": message,
    }

    if errors is not None:
        payload["errors"] = errors

    return Response(payload, status=status_code)


def paginated_response(paginator, data, message="Success", request=None):
    """
    Returns a standardized paginated API response.

    DRF's paginator.get_paginated_response() returns its own format.
    We override it here to keep our consistent structure.

    Usage:
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        return paginated_response(paginator, serializer.data, "Products retrieved.")
    """
    return Response({
        "success":   True,
        "message":   message,
        "data":      data,
        "count":     paginator.page.paginator.count,    # Total number of records
        "next":      paginator.get_next_link(),          # URL to next page (or null)
        "previous":  paginator.get_previous_link(),      # URL to previous page (or null)
        "total_pages": paginator.page.paginator.num_pages,
    })
