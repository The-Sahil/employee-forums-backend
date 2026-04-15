from django.db import models
from django.contrib.auth.models import User

class Interest(models.Model):
    """
    Model strictly representing an interest/tag a user can have.
    """
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    """
    Extended user profile strictly linked 1-to-1 with the Django User model.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    slug = models.SlugField(unique=True, max_length=150)
    interests = models.ManyToManyField(Interest, related_name='users', blank=True)

    def __str__(self):
        return self.user.username

class Post(models.Model):
    """
    Social media post authored by a User.
    """
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Post by {self.author.username} at {self.created_at}"

class Like(models.Model):
    """
    Tracks likes on posts, logic ensuring one like per user per post handled via unique_together.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f"{self.user.username} likes {self.post.id}"

class Connection(models.Model):
    """
    Connection system tracking requests to establish social links.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined')
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections_sent')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections_received')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'receiver')

    def __str__(self):
        return f"Conn({self.sender} -> {self.receiver}) [{self.status}]"
