from django.contrib.auth.decorators import login_required
from .models import Comment, Follow, Post, Group
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from .forms import CommentForm, PostForm
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
User = get_user_model()


@cache_page(20)
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page})


@login_required
def follow_index(request):
    if (Follow.objects.filter(user=request.user).count()):
        user = get_object_or_404(User, username=request.user)
        authors = Follow.objects.filter(user=user).distinct()
        post_list = []
        for author in authors:
            for post in Post.objects.filter(author=author.author).all():
                post_list.append(post)
            # print(f'{Post.objects.get(author=author.author)}!!!')
        print(f'{post_list[0]}!!!')
        paginator = Paginator(post_list, settings.POSTS_PER_PAGE)
        page_number = request.GET.get('page')
        page = paginator.get_page(page_number)
        return render(request, 'index.html', {'page': page})
    return redirect('posts:index')


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {'group': group,
                                          'posts': posts,
                                          'page': page})


def profile(request, username):
    following = False
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    if (not request.user.is_anonymous):
        user = request.user
        if (Follow.objects.filter(user=user).filter(author=author).exists()):
            following = True
    paginator = Paginator(posts, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'author': author,
        'page': page,
        'posts': posts,
        'following': following
    }

    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    user = post.author
    comments = Comment.objects.filter(post=post)
    form = CommentForm()
    return render(request, 'post.html', {'post': post,
                                         'author': user,
                                         'comments': comments,
                                         'form': form})


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    user = get_object_or_404(User, username=request.user.username)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = user
        form.save()
        return redirect('posts:index')
    return render(request, 'form.html', {'form': form,
                                         'edit': False})


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    user = post.author
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if request.user == post.author:
        if form.has_changed() and form.is_valid():
            form.save()
            return redirect('posts:post', user.username, post.pk)
        return render(request, 'form.html', {'form': form,
                                             'post': post,
                                             'author': user,
                                             'edit': True})
    return redirect('posts:post', user.username, post.pk)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    user = request.user
    form = CommentForm(request.POST or None)
    if form.is_valid():
        new_comment = form.save(commit=False)
        new_comment.author = user
        new_comment.post = post
        form.save()
    return redirect('posts:post', username, post_id)


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if (Follow.objects.filter(user=user).filter(author=author).exists()
            or user.username == request.user.username):
        print('not followed')
        return redirect('posts:index')
    print('followed')
    Follow.objects.create(
        user=user,
        author=author
    )
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if (Follow.objects.filter(user=user).filter(author=author).exists()):
        link = get_object_or_404(Follow, user=user, author=author)
        link.delete()
    return redirect('posts:index')
