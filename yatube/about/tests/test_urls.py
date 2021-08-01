# static_pages/tests/test_urls.py
from django.test import TestCase, Client


class StaticPagesURLTests(TestCase):
    def setUp(self):
        # Создаем неавторизованый клиент
        self.guest_client = Client()
        self.adress_template = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html'
        }

    def test_about_url_pages_at_desired_location(self):
        """Проверка доступности адресов приложения about."""
        for adress in self.adress_template.keys():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, 200)

    def test_about_pages_url_uses_correct_template(self):
        """Проверка шаблона для адресов приложения about"""
        for adress, template in self.adress_template.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template)
