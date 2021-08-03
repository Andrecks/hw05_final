from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from ..models import Follow, Group, Post
from django import forms
from django.core.cache import cache


User = get_user_model()


class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.author = User.objects.create(
            username='testuser'
        )
        cls.not_author = User.objects.create(
            username='ReadOnly'
        )
        cls.group = Group.objects.create(
            title='testgroup',
            slug='test-group'
        )
        cls.another_group = Group.objects.create(
            title='group with 15 posts',
            slug='test-group-2',
        )
        cls.null_group = Group.objects.create(
            slug='no-posts-allowed'
        )
        # Создаем 15 постов на тестовой группе для проверки паджинатора
        # главной страницы и страницы группы
        for i in range(15):
            Post.objects.create(
                text=f'This is post number {i + 1}',
                author=PostsViewsTests.author,
                group=PostsViewsTests.another_group,
            )
        cls.post = Post.objects.create(
            text='this post was written by testusername',
            author=PostsViewsTests.author,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsViewsTests.author)
        self.client = Client()
        self.authoruzed_not_author_client = Client()
        self.authoruzed_not_author_client.force_login(
            PostsViewsTests.not_author
        )
        self.testpost = Post.objects.create(
            text='This post belongs to a test group!',
            author=PostsViewsTests.author,
            group=PostsViewsTests.group,
            image=PostsViewsTests.uploaded
        )
        cache.clear()

    def test_post_appears_on_homepaga_and_group_page(self):
        slug = PostsViewsTests.group.slug
        slug_no_posts = PostsViewsTests.null_group.slug
        response = self.authorized_client.get(reverse('posts:index'))
        response2 = self.authorized_client.get(reverse(
                                               'posts:group_posts',
                                               kwargs={'slug': slug})
                                               )
        response3 = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': slug_no_posts}))
        first_object_index = response.context['page'][0]
        first_object_group = response2.context['page'][0]
        self.assertEqual(first_object_index, first_object_group)
        self.assertEqual(len(response3.context['page']), 0)

    def test_context_for_index_group_page_and_profile(self):
        username = PostsViewsTests.author.username
        slug = PostsViewsTests.group.slug
        self.reversed_pages = [reverse('posts:index'),
                               reverse('posts:group_posts',
                               kwargs={'slug': slug}),
                               reverse('posts:profile',
                               kwargs={'username': username}),
                               ]
        for reversed_page in self.reversed_pages:
            with self.subTest(adress=reversed_page):
                response = self.authorized_client.get(reversed_page)
                first_object = response.context['page'][0]
                post_text_0 = first_object.text
                post_author_0 = first_object.author
                post_group_0 = first_object.group
                image_group_0 = first_object.image
                self.assertEqual(post_text_0,
                                 'This post belongs to a test group!'
                                 )
                self.assertEqual(post_author_0, PostsViewsTests.author)
                self.assertEqual(post_group_0, PostsViewsTests.group)
                self.assertEqual(image_group_0, self.testpost.image)

    def test_post_page_context(self):
        pk = self.testpost.pk
        username = PostsViewsTests.author.username
        reversed_url = reverse('posts:post', kwargs={'username': username,
                                                     'post_id': pk})
        response = self.client.get(reversed_url)
        post_text = response.context['post'].text
        post_group = response.context['post'].group
        post_image = response.context['post'].image
        post_author = response.context['author']
        self.assertEqual(post_text, self.testpost.text)
        self.assertEqual(post_group, self.testpost.group)
        self.assertEqual(post_image, self.testpost.image)
        self.assertEqual(post_author, self.testpost.author)

    def test_first_index_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page']), 10)

    def test_first_group_page_contains_ten_records(self):
        slug = PostsViewsTests.another_group.slug
        url = reverse('posts:group_posts', kwargs={'slug': slug})
        response = self.client.get(url)
        self.assertEqual(len(response.context['page']), 10)

    def test_second_index_page_contains_seven_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page']), 7)

    def test_second_group_page_contains_five_records(self):
        slug = PostsViewsTests.another_group.slug
        url = reverse('posts:group_posts', kwargs={'slug': slug})
        response = self.client.get(url + '?page=2')
        self.assertEqual(len(response.context['page']), 5)

    def test_posts_views_use_correct_template(self):
        slug = PostsViewsTests.group.slug
        """Шаблон task_list сформирован с правильным контекстом."""
        self.names_templates = {reverse('posts:index'): 'index.html',
                                reverse('posts:group_posts',
                                kwargs={'slug': slug}): 'group.html',
                                reverse('posts:new_post'): 'form.html'}

        for reversed_name, template in self.names_templates.items():
            with self.subTest(reversed_name=reversed_name):
                response = self.authorized_client.get(reversed_name)
                self.assertTemplateUsed(response, template)

    def test_new_post_shows_correct_context(self):
        """Шаблон new сформирован с правильным контекстом."""
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        url = reverse('posts:new_post')
        response = self.authorized_client.get(url)
        form_fields = {
            'text': forms.fields.CharField,
            # При создании формы поля модели типа TextField
            # преобразуются в CharField с виджетом forms.Textarea
            'group': forms.fields.ChoiceField
        }
        # Проверяем, что типы полей формы и значения
        # в словаре context соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_post_edit_shows_correct_context(self):
        username = PostsViewsTests.author.username
        post_id = PostsViewsTests.post.pk
        """Шаблон post_edit сформирован с правильным контекстом."""
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        url = reverse('posts:post_edit',
                      kwargs={'username': username,
                              'post_id': post_id})
        response = self.authorized_client.get(url)
        form_fields = {
            'text': forms.fields.CharField,
            # При создании формы поля модели типа TextField
            # преобразуются в CharField с виджетом forms.Textarea
            'group': forms.fields.ChoiceField
        }
        # Проверяем, что типы полей формы и значения
        # в словаре context соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_group_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        slug = PostsViewsTests.group.slug
        title = PostsViewsTests.group.title
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': slug})
        )
        self.assertEqual(response.context['group'].title, title)
        self.assertEqual(response.context['group'].slug, slug)
        self.assertEqual(len(response.context['posts']), 1)
        self.assertEqual(len(response.context['page']), 1)

    def test_edit_possible_anon(self):
        username = PostsViewsTests.author.username
        post_id = PostsViewsTests.post.pk
        url = reverse('posts:post_edit',
                      kwargs={'username': username,
                              'post_id': post_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_edit_possible_author(self):
        username = PostsViewsTests.author.username
        url = reverse('posts:post_edit',
                      kwargs={'username': username,
                              'post_id': PostsViewsTests.post.pk})
        response = self.authorized_client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_edit_possible_not_author(self):
        username = PostsViewsTests.author.username

        redirect_url = reverse('posts:post',
                               kwargs={'username': username,
                                       'post_id': PostsViewsTests.post.pk})
        url = reverse('posts:post_edit',
                      kwargs={'username': username,
                              'post_id': PostsViewsTests.post.pk})
        response = self.authoruzed_not_author_client.get(url)
        self.assertRedirects(response, redirect_url)

    def test_error_404_status_code(self):
        url = 'made_up_url'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_cache_holds_20_second(self):
        url = reverse('posts:index')
        response = self.client.get(url + '?page=2')
        count = len(response.context['page'])
        self.testpost.delete()
        self.assertEqual(len(response.context['page']), count)
        cache.clear()
        response = self.client.get(url + '?page=2')
        self.assertEqual(len(response.context['page']), count - 1)

    def test_user_can_subscribe_to_other_user_and_unsubscribe(self):
        not_author = PostsViewsTests.not_author
        author = PostsViewsTests.author
        url = reverse('posts:profile_follow', kwargs={'username':
                                                      author.username})
        sub_counter = Follow.objects.filter(user=not_author).count()
        self.authoruzed_not_author_client.get(url)
        self.assertEqual(Follow.objects.filter(user=not_author).count(),
                         sub_counter + 1)
        url = reverse('posts:profile_unfollow', kwargs={'username':
                                                        author.username})
        sub_counter = Follow.objects.filter(user=not_author).count()
        self.authoruzed_not_author_client.get(url)
        self.assertEqual(Follow.objects.filter(user=not_author).count(),
                         sub_counter - 1)

    def test_index_follow_shows_subscribed_author_post(self):
        self.new_user = User.objects.create(
            username='newuser'
        )
        self.new_author = User.objects.create(
            username='newauthor'
        )
        self.link = Follow.objects.create(
            user=self.new_user,
            author=self.new_author
        )
        self.new_client = Client()
        self.new_client.force_login(self.new_user)
        self.new_author_client = Client()
        self.new_author_client.force_login(self.new_author)
        url = reverse('posts:follow_index')
        newuser_follow = self.new_client.get(url)
        author_follow = self.new_author_client.get(url)
        count_follow_not_author = len(newuser_follow.context['page'])
        count_follow_author = len(author_follow.context['page'])
        self.test_post = Post.objects.create(
            text='test post for not author by author',
            author=self.new_author
        )
        newuser_follow = self.new_client.get(url)
        author_follow = self.new_author_client.get(url)
        self.assertEqual(len(author_follow.context['page']),
                         count_follow_author)
        self.assertEqual(len(newuser_follow.context['page']),
                         count_follow_not_author + 1)
        self.link.delete()
        self.new_author.delete()
        self.new_user.delete()
