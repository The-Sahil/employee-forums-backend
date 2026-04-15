from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from knox.models import AuthToken
from knox.views import LoginView as KnoxLoginView
from django.contrib.auth import login
from django.db.models import Q, Count

from .models import Interest, Post, Like, Connection
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer, 
    PostSerializer, ConnectionSerializer, InterestSerializer
)
from django.contrib.auth.models import User

# --- AUTHENTICATION VIEWS ---

class RegisterAPI(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        _, token = AuthToken.objects.create(user)
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "token": token
        }, status=status.HTTP_201_CREATED)

class LoginAPI(KnoxLoginView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        login(request, user)
        return super(LoginAPI, self).post(request, format=None)

# --- INTERESTS VIEWS ---

class InterestListCreateAPI(generics.ListCreateAPIView):
    queryset = Interest.objects.all()
    serializer_class = InterestSerializer
    permission_classes = [permissions.IsAuthenticated]

# --- POST VIEWS ---

class PostListCreateAPI(generics.ListCreateAPIView):
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class FeedAPI(generics.ListAPIView):
    """
    Returns posts from the user's accepted connections and the user's own posts.
    """
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        friends_from_sent = Connection.objects.filter(sender=user, status='accepted').values_list('receiver_id', flat=True)
        friends_from_received = Connection.objects.filter(receiver=user, status='accepted').values_list('sender_id', flat=True)
        friend_ids = set(friends_from_sent).union(set(friends_from_received))
        friend_ids.add(user.id) # Include self
        
        return Post.objects.filter(author_id__in=friend_ids).order_by('-created_at')

class LikeToggleAPI(views.APIView):
    """
    Toggles a like for a specific post.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, post_id):
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)
        
        like, created = Like.objects.get_or_create(user=request.user, post=post)
        if not created:
            # Already liked, so we toggle it off (unlike)
            like.delete()
            return Response({"message": "Unliked post successfully"}, status=status.HTTP_200_OK)
            
        return Response({"message": "Liked post successfully"}, status=status.HTTP_201_CREATED)

# --- CONNECTION VIEWS ---

class SendConnectionRequestAPI(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        if request.user.id == user_id:
            return Response({"error": "Cannot send request to yourself."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            receiver = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if inverse connection exists
        if Connection.objects.filter(sender=receiver, receiver=request.user).exists():
            return Response({"error": "This user already sent you a request."}, status=status.HTTP_400_BAD_REQUEST)

        connection, created = Connection.objects.get_or_create(
            sender=request.user, receiver=receiver,
            defaults={'status': 'pending'}
        )
        if not created:
            return Response({"error": "Connection request already sent or exists."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Connection request sent."}, status=status.HTTP_201_CREATED)

class PendingConnectionsAPI(generics.ListAPIView):
    serializer_class = ConnectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Connection.objects.filter(receiver=self.request.user, status='pending')

class AcceptConnectionAPI(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, connection_id):
        try:
            connection = Connection.objects.get(id=connection_id, receiver=request.user, status='pending')
        except Connection.DoesNotExist:
            return Response({"error": "Connection request not found or not pending."}, status=status.HTTP_404_NOT_FOUND)
            
        connection.status = 'accepted'
        connection.save()
        return Response({"message": "Connection accepted."}, status=status.HTTP_200_OK)

class DeclineConnectionAPI(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, connection_id):
        try:
            connection = Connection.objects.get(id=connection_id, receiver=request.user, status='pending')
        except Connection.DoesNotExist:
            return Response({"error": "Connection request not found or not pending."}, status=status.HTTP_404_NOT_FOUND)
            
        connection.status = 'declined'
        connection.save()
        return Response({"message": "Connection declined."}, status=status.HTTP_200_OK)

# --- USER RECOMMENDATION ENGINE ---

class UserRecommendationAPI(generics.ListAPIView):
    """
    Complex Task: Recommends new users based on mutual connections first, then shared interests.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        
        # 1. Identify users already connected (pending, accepted, declined) or sent requests to
        conn_sent_to = Connection.objects.filter(sender=user).values_list('receiver_id', flat=True)
        conn_received_from = Connection.objects.filter(receiver=user).values_list('sender_id', flat=True)
        
        exclude_ids = set(conn_sent_to).union(set(conn_received_from))
        exclude_ids.add(user.id) # exclude self

        # 2. Identify ONLY accepted friends for mutual connections calculation
        friends_from_sent = Connection.objects.filter(sender=user, status='accepted').values_list('receiver_id', flat=True)
        friends_from_received = Connection.objects.filter(receiver=user, status='accepted').values_list('sender_id', flat=True)
        friend_ids = list(set(friends_from_sent).union(set(friends_from_received)))

        my_interests = user.userprofile.interests.all()

        # 3. Recommendation Engine Logic:
        # Exclude already connected users. Annotate with shared interests count and mutual friends count.
        queryset = User.objects.exclude(id__in=exclude_ids).annotate(
            shared_interests_count=Count(
                'userprofile__interests', 
                filter=Q(userprofile__interests__in=my_interests), 
                distinct=True
            ),
            mutual_friends_count=Count(
                'connections_received__sender',
                filter=Q(
                    connections_received__status='accepted', 
                    connections_received__sender__in=friend_ids
                ),
                distinct=True
            ) + Count(
                'connections_sent__receiver',
                filter=Q(
                    connections_sent__status='accepted', 
                    connections_sent__receiver__in=friend_ids
                ),
                distinct=True
            )
        ).filter(
            Q(shared_interests_count__gt=0) | Q(mutual_friends_count__gt=0)
        ).order_by('-mutual_friends_count', '-shared_interests_count')[:20]

        return queryset
