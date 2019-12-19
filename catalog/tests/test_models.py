from django.test import TestCase
from catalog.models import Author, Book


class MyTestClass(TestCase):

    # Test Author

    @classmethod
    def setUpTestData(cls):
        Author.objects.create(first_name='Big', last_name='Bob')

    def test_first_name_label(self):
        author = Author.objects.get(id=1)
        field_label = author._meta.get_field('first_name').verbose_name
        self.assertEqual(field_label, 'first name')

    def test_date_of_death_label(self):
        author = Author.objects.get(id=1)
        field_label = author._meta.get_field('date_of_death').verbose_name
        self.assertEqual(field_label, 'died')

    def test_first_name_max_length(self):
        author = Author.objects.get(id=1)
        max_length = author._meta.get_field('first_name').max_length
        self.assertEqual(max_length, 100)

    def test_str_comma(self):
        author = Author.objects.get(id=1)
        expected_object = '%s, %s' % (author.last_name, author.first_name)
        self.assertEqual(expected_object, str(author))

    def test_get_url(self):
        author = Author.objects.get(id=1)
        self.assertEqual(author.get_absolute_url(), '/catalog/author/1')
