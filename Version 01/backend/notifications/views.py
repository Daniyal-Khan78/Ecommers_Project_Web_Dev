from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from .serializers import NotificationSerializer
from utils.responses import success_response


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifs = Notification.objects.filter(user=request.user).order_by('-created_at')
        unread_count = notifs.filter(is_read=False).count()
        serializer = NotificationSerializer(notifs, many=True)
        return success_response(
            data={'notifications': serializer.data, 'unread_count': unread_count},
            message="Notifications retrieved."
        )


class MarkAllReadView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return success_response(message="All notifications marked as read.")
