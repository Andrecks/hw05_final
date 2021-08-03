from django.test import Client, TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.contrib.auth import get_user_model
from ..forms import PostForm
from ..models import Comment, Post, Group
from django import forms
User = get_user_model()


class PostsFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем запись в базе данных
        cls.user = User.objects.create(
            username='testuser123'
        )
        cls.post = Post.objects.create(
            text='Test text',
            author=PostsFormsTests.user
        )
        cls.form = PostForm()
        cls.group = Group.objects.create(
            slug='FormTestGroup',
            title='Group for testing forms'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsFormsTests.user)
        self.guest_client = Client()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'author': PostsFormsTests.user
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:new_post'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse('posts:index'))
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создалась запись
        self.assertTrue(
            Post.objects.filter(
                text='Test text',
                author=PostsFormsTests.user
            ).exists()
        )

    def test_post_edit_context(self):
        posts_count = Post.objects.count()
        username = PostsFormsTests.user.username
        form_data = {
            'text': 'post editing test',
            'author': PostsFormsTests.user,
            'image': self.uploaded
        }
        url = reverse('posts:post_edit',
                      kwargs={'username': username,
                              'post_id': PostsFormsTests.post.pk})
        response = self.authorized_client.post(url,
                                               data=form_data,
                                               follow=True)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(Post.objects.filter(
            text='post editing test').exists())
        redirect_url = reverse('posts:post',
                               kwargs={'username': username,
                                       'post_id': PostsFormsTests.post.pk})
        self.assertRedirects(response, redirect_url)

    def test_new_post_page_shows_correct_context(self):
        """Шаблон new сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:new_post'))
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            'text': forms.fields.CharField,
            # При создании формы поля модели типа TextField
            # преобразуются в CharField с виджетом forms.Textarea
            'group': forms.fields.ChoiceField
        }

        # Проверяем, что типы полей формы в словаре context
        # соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_only_authorized_users_can_comment(self):
        self.comment = {
            'text': 'Test commenting'
        }
        self.testpost = Post.objects.create(
            text='Post for testing comments',
            author=PostsFormsTests.user
        )
        url = reverse('posts:add_comment',
                      kwargs={'username': PostsFormsTests.user.username,
                              'post_id': self.testpost.pk})
        # замеряем количество комментов
        count = Comment.objects.count()
        self.authorized_client.post(url, data=self.comment)
        response_anon = self.guest_client.post(url, data=self.comment)
        self.assertRedirects(response_anon,
                             f'/auth/login/?next='
                             f'/{PostsFormsTests.user.username}/'
                             f'{self.testpost.pk}/comment')
        self.assertEqual(Comment.objects.count(),
                         count + 1)
        self.testpost.delete()
