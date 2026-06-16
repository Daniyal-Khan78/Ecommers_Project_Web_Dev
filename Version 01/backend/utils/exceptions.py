from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler for Django REST Framework.

    DRF calls this function whenever a view raises an exception.
    We use it to transform all error responses into our standard format:
        { "success": false, "message": "...", "errors": { ... } }

    Without this, DRF returns errors in its own inconsistent format,
    and Django returns HTML pages for 404/500 errors — both useless for a React frontend.

    How to wire this up: in settings.py set
        REST_FRAMEWORK = { 'EXCEPTION_HANDLER': 'utils.exceptions.custom_exception_handler' }
    """

    # First, let DRF's default handler process the exception.
    # This handles AuthenticationFailed, NotAuthenticated, PermissionDenied,
    # NotFound, ValidationError, etc.
    # If DRF doesn't know how to handle it, response will be None.
    response = exception_handler(exc, context)

    if response is not None:
        # DRF handled the exception. Now reformat the response body.

        # Extract DRF's original error data so we can pull out useful messages.
        original_data = response.data

        # Build our standard error payload
        payload = {
            "success": False,
            "message": _extract_message(original_data, response.status_code),
        }

        # If the error has field-level details (e.g., validation errors),
        # include them under "errors" so the frontend can highlight specific fields.
        if isinstance(original_data, dict) and len(original_data) > 1:
            payload["errors"] = original_data
        elif isinstance(original_data, list):
            payload["errors"] = {"non_field_errors": original_data}

        response.data = payload
        return response

    # DRF didn't handle it (e.g., a Python exception like ZeroDivisionError).
    # Return a generic 500 error in our standard format instead of a crash page.
    return Response(
        {
            "success": False,
            "message": "An unexpected server error occurred. Please try again later.",
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _extract_message(data, status_code):
    """
    Pull a human-readable message from DRF's error data.

    DRF uses different structures for different errors:
      - AuthenticationFailed: {"detail": "Given token not valid for any token type"}
      - ValidationError:      {"email": ["This field is required."]}
      - ParseError:           {"detail": "JSON parse error"}
    """
    # Map common HTTP status codes to friendly messages.
    status_messages = {
        400: "Invalid request. Please check your input.",
        401: "Authentication required. Please log in.",
        403: "You do not have permission to perform this action.",
        404: "The requested resource was not found.",
        405: "This HTTP method is not allowed on this endpoint.",
        429: "Too many requests. Please slow down.",
        500: "An unexpected server error occurred.",
    }

    # If DRF put a "detail" key in the error, use that as the message.
    # This covers 401, 403, 404 and most authentication errors.
    if isinstance(data, dict) and "detail" in data:
        return str(data["detail"])

    # For validation errors (400), build a summary message from field errors.
    if isinstance(data, dict) and status_code == 400:
        first_field = next(iter(data), None)
        if first_field:
            first_error = data[first_field]
            if isinstance(first_error, list) and first_error:
                return f"{first_field}: {str(first_error[0])}"

    # Fall back to the generic status message.
    return status_messages.get(status_code, "An error occurred.")
