# posts/tests/tests_url.py
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from ..models import Group, Post
from django.core.cache import cache

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Group.objects.create(
            title='testo',
            slug='slug-testo',
            description='testodescription'
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create(username='testuser')
        self.another_user = User.objects.create(username='not author')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.auth_non_author = Client()
        self.auth_non_author.force_login(self.another_user)
        self.post = Post.objects.create(
            text='This post is written by testuser',
            author=self.user,
        )
        username = self.user.username
        post_id = self.post.pk
        self.pages = {'/': 'index.html',
                      '/group/slug-testo/': 'group.html',
                      f'/{username}/': 'profile.html',
                      f'/{username}/{post_id}/': 'post.html'}
        cache.clear()

    def test_urls(self):
        for page in self.pages.keys():
            with self.subTest(adress=page):
                response_anon = self.guest_client.get(page)
                response_auth = self.authorized_client.get(page)
                self.assertEqual(response_anon.status_code, 200)
                self.assertEqual(response_auth.status_code, 200)

    def test_new_page_url_for_authorized_and_anon_user(self):
        response_anon = self.guest_client.get('/new/',
                                              follow=True)
        response_auth = self.authorized_client.get('/new/')
        self.assertRedirects(response_anon, '/auth/login/?next=/new/')
        self.assertEqual(response_auth.status_code, 200)

    def edit_post_url_for_anon_user(self):
        username = self.user.username
        post_id = self.post.pk
        url = f'/{username}/{post_id}/edit'
        response = self.guest_client.get(url, follow=True)
        self.assertRedirects(response, '/auth/login/?next={url}')

    def edit_post_url_for_author(self):
        username = self.user.username
        post_id = self.post.pk
        url = f'/{username}/{post_id}/edit'
        response = self.authorized_client.get(url)
        self.assertEqual(response.status_code, 200)

    def edit_post_url_for_not_author(self):
        username = self.user.username
        post_id = self.post.pk
        url = f'/{username}/{post_id}/edit'
        response = self.auth_non_author.get(url, follow=True)
        response = self.authorized_client.get(url)
        self.assertRedirects(response,
                             f'/{username}/{post_id}')

    def test_url_templates(self):
        for adress, template in self.pages.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_template_new_post(self):
        url = '/new/'
        response_anon = self.guest_client.get(url,
                                              follow=True)
        response_authorized = self.authorized_client.get(url)
        self.assertTemplateUsed(response_authorized, 'form.html')
        self.assertRedirects(response_anon, f'/auth/login/?next={url}')
