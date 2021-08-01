from django.test import TestCase
from ..models import Group, Post
from django.contrib.auth import get_user_model

User = get_user_model()


class ModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='1'
        )
        cls.post = Post.objects.create(
            text='1' * 20,
            author=cls.user
        )
        cls.group = Group.objects.create(
            title='TestGroup'
        )

    def test_group_str(self):
        group = ModelTest.group
        expected_str = group.title
        self.assertEqual(expected_str, str(group))

    def test_post_str(self):
        post = ModelTest.post
        expected_str = post.text[:15]
        self.assertEqual(expected_str, str(post))
