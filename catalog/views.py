from django.shortcuts import render
from .models import Book, Author, BookInstance, Genre
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from .forms import RenewBookForm
import datetime
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth.decorators import permission_required
from django.views.generic.edit import CreateView, UpdateView, DeleteView


def index(request):
    num_books = Book.objects.all().count()
    num_authors = Author.objects.count()
    num_instance = BookInstance.objects.all().count()
    num_instance_available = BookInstance.objects.filter(status__exact='a').count()

    num_genres = Genre.objects.all().count()
    num_books_title = Book.objects.filter(title__isnull=False).count()

    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    return render(request, 'index.html', context={'num_books': num_books,
                                                  'num_authors': num_authors,
                                                  'num_instance': num_instance,
                                                  'num_instance_available': num_instance_available,
                                                  'num_genres': num_genres,
                                                  'num_books_title': num_books_title,
                                                  'num_visits': num_visits})


class BookListView(generic.ListView):
    model = Book
    paginate_by = 10


class BookDetailView(generic.DetailView):
    model = Book


class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10
    ordering = ['last_name']


class AuthorDetailView(generic.DetailView):
    model = Author


class LoanedListView(LoginRequiredMixin, generic.ListView):
    model = BookInstance
    template_name = 'catalog/loaned_list.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')


class AllLoanedListView(PermissionRequiredMixin, generic.ListView):
    model = BookInstance
    permission_required = 'catalog.can_mark_returned'
    template_name = 'catalog/all_loaned_list.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')


@permission_required('catalog.can_mark_returned')
def renew_book(request, pk):
    inst = get_object_or_404(BookInstance, pk=pk)

    if request.POST:
        form = RenewBookForm(request.POST)

        if form.is_valid():
            inst.due_back = form.cleaned_data['renewal_date']
            inst.save()

            return HttpResponseRedirect(reverse('all-borrowed'))
    else:
        proposed = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed})

    return render(request, 'catalog/book_renew.html', {'form': form, 'bookinst': inst})


class AuthorCreate(PermissionRequiredMixin, CreateView):
    model = Author
    fields = '__all__'
    initial = {'date_of_death': '2003-05-26'}
    permission_required = 'catalog.can_mark_returned'


class AuthorUpdate(PermissionRequiredMixin, UpdateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    permission_required = 'catalog.can_mark_returned'


class AuthorDelete(PermissionRequiredMixin, DeleteView):
    model = Author
    success_url = reverse_lazy('authors')
    permission_required = 'catalog.can_mark_returned'


class BookCreate(PermissionRequiredMixin, CreateView):
    model = Book
    fields = '__all__'
    permission_required = 'catalog.can_mark_returned'


class BookUpdate(PermissionRequiredMixin, UpdateView):
    model = Book
    fields = '__all__'
    permission_required = 'catalog.can_mark_returned'


class BookDelete(PermissionRequiredMixin, DeleteView):
    model = Book
    success_url = reverse_lazy('books')
    permission_required = 'catalog.can_mark_returned'
