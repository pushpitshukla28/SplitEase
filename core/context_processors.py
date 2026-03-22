from .models import FriendRequest


def pending_friend_requests(request):
    if request.user.is_authenticated:
        count = FriendRequest.objects.filter(to_user=request.user, accepted=False).count()
        return {'pending_friend_requests_count': count}
    return {'pending_friend_requests_count': 0}
