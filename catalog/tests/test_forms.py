from django.test import TestCase
from catalog.forms import RenewBookForm
import datetime


class RenewBookFormTest(TestCase):

    def test_renew_label(self):
        form = RenewBookForm()
        renewal_field_label = form.fields['renewal_date'].label
        self.assertTrue(renewal_field_label is None or renewal_field_label == 'renewal date')

    def test_renew_label_help(self):
        form = RenewBookForm()
        self.assertEqual(form.fields['renewal_date'].help_text, 'Enter a date between now and 4 weeks (default 3).')

    # WTF

    # def test_renew_form_in_past(self):
    #     date = datetime.date.today() - datetime.timedelta(days=3)
    #     form_data = {'renewal_date': date}
    #     form = RenewBookForm(data=form_data)
    #     print(form.is_valid())
    #     self.assertFalse(form.is_valid())

    # def test_renew_form_in_future(self):
    #     date = datetime.date.today() + datetime.timedelta(weeks=4) + datetime.timedelta(days=3)
    #     form_data = {'renewal_date': date}
    #     form = RenewBookForm(data=form_data)
    #     self.assertFalse(form.is_valid())

    def test_renew_form_in_today(self):
        date = datetime.date.today()
        form_data = {'renewal_date': date}
        form = RenewBookForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_renew_form_max(self):
        date = datetime.date.today() + datetime.timedelta(weeks=4)
        form_data = {'renewal_date': date}
        form = RenewBookForm(data=form_data)
        self.assertTrue(form.is_valid())
