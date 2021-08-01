from django.test import Client, TestCase
from django.urls import reverse


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.pages = {'about:author': 'about/author.html',
                      'about:tech': 'about/tech.html'}

    def test_about_pages_accessible_by_name(self):
        """URL, генерируемый при помощи имен about, доступен."""
        for reversed_name in self.pages.keys():
            with self.subTest(reversed_name=reversed_name):
                response = self.guest_client.get(reverse(reversed_name))
                self.assertEqual(response.status_code, 200)

    def test_about_page_uses_correct_template(self):
        """При запросе к страницам about
        применяется правильный шаблон"""
        for reversed_name, template in self.pages.items():
            with self.subTest(reversed_name=reversed_name):
                response = self.guest_client.get(reverse(reversed_name))
                self.assertTemplateUsed(response, template)
