from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.deletion import CASCADE, SET_NULL

User = get_user_model()


class Group(models.Model):

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField()
    pub_date = models.DateTimeField("date_published", auto_now_add=True,
                                    db_index=True)
    author = models.ForeignKey(User, on_delete=CASCADE, related_name="posts")
    group = models.ForeignKey(Group, blank=True, null=True,
                              on_delete=SET_NULL, related_name="posts")
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    def __str__(self):
        return self.text[:15]

    class Meta:
        ordering = ["-pub_date"]


class Comment(models.Model):
    text = models.TextField()
    created = models.DateTimeField("date_published", auto_now_add=True)
    author = models.ForeignKey(User, on_delete=CASCADE,
                               related_name="comments")
    post = models.ForeignKey(Post, on_delete=CASCADE,
                             related_name="comments")

    def __str__(self):
        return self.text[:15]

    class Meta:
        ordering = ["-created"]


class Follow(models.Model):
    user = models.ForeignKey(User, related_name="follower",
                             null=True, on_delete=SET_NULL)
    author = models.ForeignKey(User, related_name="following",
                               on_delete=CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name="unique_followers")
        ]

    def __repr__(self):
        return {'user': self.user,
                'author': self.author}
