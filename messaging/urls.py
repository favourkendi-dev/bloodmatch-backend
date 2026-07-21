from django.urls import path
from .views import MessageListCreateView, MarkMessageAsReadView, UnreadMessageCountView

urlpatterns = [
    path('', MessageListCreateView.as_view(), name='message-list-create'),
    path('<int:pk>/read/', MarkMessageAsReadView.as_view(), name='message-mark-read'),
    path('unread_count/', UnreadMessageCountView.as_view(), name='message-unread-count'),
]
