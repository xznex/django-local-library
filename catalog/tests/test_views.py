from django.test import TestCase
from catalog.models import Author, BookInstance, Book, Genre, Language
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.utils import timezone
import datetime


class AuthorListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        for test_user in range(13):
            Author.objects.create(first_name='George Anatolyevich %s' % test_user, last_name='Sir %s' % test_user)

    def test_view_url_exists_at_desired_location(self):
        resp = self.client.get('/catalog/authors/')
        self.assertEqual(resp.status_code, 200)

    def test_view_url_accessible_by_name(self):
        resp = self.client.get(reverse('authors'))
        self.assertEqual(resp.status_code, 200)

    def test_view_correct_template(self):
        resp = self.client.get(reverse('authors'))
        self.assertEqual(resp.status_code, 200)

        self.assertTemplateUsed(resp, 'catalog/author_list.html')

    def test_pagination_is_ten(self):
        resp = self.client.get(reverse('authors'))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('is_paginated' in resp.context)
        self.assertTrue(resp.context['is_paginated'] is True)
        self.assertTrue(len(resp.context['author_list']) == 10)

    def test_lists_all_authors(self):
        resp = self.client.get(reverse('authors') + '?page=2')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('is_paginated' in resp.context)
        self.assertTrue(resp.context['is_paginated'] is True)
        self.assertTrue(len(resp.context['author_list']) == 3)


class LoanedListViewTest(TestCase):

    def setUp(self):
        test_user1 = User.objects.create_user(username='test_user1', password='123')
        test_user1.save()
        test_user2 = User.objects.create_user(username='test_user2', password='456')
        test_user2.save()

        test_author = Author.objects.create(first_name='John', last_name='Smith')
        test_genre = Genre.objects.create(name='Fantasy')
        test_language = Language.objects.create(name='Ukrainian')
        test_book = Book.objects.create(title='Book Title', summary='My book summary', isbn='ABCDEFG',
                                        author=test_author, language=test_language)

        genre_objects_for_book = Genre.objects.all()
        test_book.genre.set(genre_objects_for_book)

        copies = 30
        for copy in range(copies):
            return_date = timezone.now() + datetime.timedelta(days=copy % 5)
            if copy % 2:
                borrower = test_user1
            else:
                borrower = test_user2
            status = 'm'
            BookInstance.objects.create(book=test_book, imprint='Unlikely Imprint, 2016', due_back=return_date,
                                        borrower=borrower, status=status)

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('my-borrowed'))
        self.assertRedirects(resp, '/accounts/login/?next=/catalog/mybooks/')

    def test_logged_in_uses_correct_template(self):
        login = self.client.login(username='test_user1', password='123')
        resp = self.client.get(reverse('my-borrowed'))

        self.assertEqual(str(resp.context['user']), 'test_user1')
        self.assertEqual(resp.status_code, 200)

        self.assertTemplateUsed(resp, 'catalog/loaned_list.html')

    def test_only_borrowed_books_in_list(self):
        login = self.client.login(username='test_user1', password='123')
        resp = self.client.get(reverse('my-borrowed'))

        self.assertEqual(str(resp.context['user']), 'test_user1')
        self.assertEqual(resp.status_code, 200)

        self.assertTrue('bookinstance_list' in resp.context)
        self.assertEqual(len(resp.context['bookinstance_list']), 0)

        get_ten_books = BookInstance.objects.all()[:10]

        for copy in get_ten_books:
            copy.status = 'o'
            copy.save()

        resp = self.client.get(reverse('my-borrowed'))
        self.assertEqual(str(resp.context['user']), 'test_user1')
        self.assertEqual(resp.status_code, 200)

        self.assertTrue('bookinstance_list' in resp.context)

        for book in resp.context['bookinstance_list']:
            self.assertEqual(resp.context['user'], book.borrower)
            self.assertEqual('o', book.status)

    def test_pages_ordered_by_due_date(self):
        for copy in BookInstance.objects.all():
            copy.status = 'o'
            copy.save()

        login = self.client.login(username='test_user1', password='123')
        resp = self.client.get(reverse('my-borrowed'))

        self.assertEqual(str(resp.context['user']), 'test_user1')
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(len(resp.context['bookinstance_list']), 10)

        last_date = 0
        for copy in resp.context['bookinstance_list']:
            if last_date == 0:
                last_date = copy.due_back
            else:
                self.assertTrue(last_date <= copy.due_back)


class RenewBookInstancesViewTest(TestCase):

    def setUp(self):
        test_user1 = User.objects.create_user(username='test_user1', password='123')
        test_user1.save()

        test_user2 = User.objects.create_user(username='test_user2', password='456')
        test_user2.save()
        permission = Permission.objects.get(name='Set book as returned')
        test_user2.user_permissions.add(permission)
        test_user2.save()

        test_author = Author.objects.create(first_name='John', last_name='Smith')
        test_genre = Genre.objects.create(name='Fantasy')
        test_language = Language.objects.create(name='Ukrainian')
        test_book = Book.objects.create(title='Book Title', summary='My book summary', isbn='ABCDEFG',
                                        author=test_author, language=test_language)

        genre_objects_for_book = Genre.objects.all()
        test_book.genre.set(genre_objects_for_book)
        test_book.save()

        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_book_instance1 = BookInstance.objects.create(book=test_book, imprint='Unlikely Imprint, 2016',
                                                               due_back=return_date, borrower=test_user1, status='o')

        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_book_instance2 = BookInstance.objects.create(book=test_book, imprint='Unlikely Imprint, 2016',
                                                               due_back=return_date, borrower=test_user2, status='o')

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('renew-book', kwargs={'pk': self.test_book_instance1.pk}))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith('/accounts/login/'))

    def test_redirect_if_logged_in_but_not_correct_permission(self):
        login = self.client.login(username='test_user1', password='123')
        resp = self.client.get(reverse('renew-book', kwargs={'pk': self.test_book_instance1.pk}))

        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith('/accounts/login/'))

    def test_logged_in_with_permission_borrowed_book(self):
        login = self.client.login(username='test_user2', password='456')
        resp = self.client.get(reverse('renew-book', kwargs={'pk': self.test_book_instance1.pk}))

        self.assertTrue(resp.status_code, 200)

    def test_logged_in_with_permission_another_users_borrowed_book(self):
        login = self.client.login(username='test_user2', password='456')
        resp = self.client.get(reverse('renew-book', kwargs={'pk': self.test_book_instance1.pk}))

        self.assertTrue(resp.status_code, 200)

    def test_HTTP404_for_invalid_book_if_logged_in(self):
        import uuid
        test_uuid = uuid.uuid4()
        login = self.client.login(username='test_user2', password='456')
        resp = self.client.get(reverse('renew-book', kwargs={'pk': test_uuid}))

        self.assertEqual(resp.status_code, 404)

    def test_uses_correct_template(self):
        login = self.client.login(username='test_user2', password='456')
        resp = self.client.get(reverse('renew-book', kwargs={'pk': self.test_book_instance1.pk}))

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'catalog/book_renew.html')

    def test_form_renewal_date_initially_has_date_three_weeks_in_future(self):
        login = self.client.login(username='test_user2', password='456')
        resp = self.client.get(reverse('renew-book', kwargs={'pk': self.test_book_instance1.pk}))

        self.assertEqual(resp.status_code, 200)

        date_3_weeks_in_future = datetime.date.today() + datetime.timedelta(weeks=3)
        self.assertEqual(resp.context['form'].initial['renewal_date'], date_3_weeks_in_future)

    def test_redirects_to_all_borrowed_book_list_on_success(self):
        login = self.client.login(username='test_user2', password='456')
        valid_date_in_future  = datetime.date.today() + datetime.timedelta(weeks=2)
        resp = self.client.post(reverse('renew-book', kwargs={'pk': self.test_book_instance1.pk}),
                                {'renewal_date': valid_date_in_future})
        self.assertRedirects(resp, reverse('all-borrowed'))

    # def test_form_invalid_renewal_date_past(self):
    #     login = self.client.login(username='test_user2', password='456')
    #     date_in_past = datetime.date.today() - datetime.timedelta(weeks=1)
    #     resp = self.client.post(reverse('renew-book', kwargs={'pk': self.test_book_instance1.pk}),
    #                             {'renewal_date': date_in_past})
    #
    #     self.assertEqual(resp.status_code, 200)
    #     self.assertFormError(resp, 'form', 'renewal_date', 'Invalid date - renewal in past')

    # def test_form_invalid_renewal_date_future(self):
    #     login = self.client.login(username='test_user2', password='456')
    #     invalid_date_in_future = datetime.date.today() + datetime.timedelta(weeks=5)
    #     resp = self.client.post(reverse('renew-book', kwargs={'pk': self.test_book_instance1.pk}),
    #                             {'renewal_date': invalid_date_in_future})
    #
    #     self.assertEqual(resp.status_code, 200)
    #     self.assertFormError(resp, 'form', 'renewal_date', 'Invalid date - renewal more than 4 weeks ahead')
