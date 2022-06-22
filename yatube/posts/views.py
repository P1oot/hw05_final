from django.shortcuts import render, get_object_or_404
from .models import Post, Group, User, Comment, Follow
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .forms import PostForm, CommentForm
from .func import make_paginator


def index(request):
    post_list = Post.objects.all()
    page_obj = make_paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.select_related('group').filter(group=group)
    page_obj = make_paginator(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = (Post.objects.select_related('author')
             .filter(author__username=username))
    page_obj = make_paginator(request, posts)
    if Follow.objects.filter(author=author).exists():
        following = True
    else:
        following = False
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = Post.objects.get(id=post_id)
    count = (Post.objects.select_related('author')
             .filter(author__username=post.author).count())
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post_id)
    context = {
        'count': count,
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            form.save()
            return redirect('posts:profile', username=str(request.user))
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = Post.objects.get(id=post_id)
    if post.author.username != request.user.username:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'is_edit': True,
        'post_id': post_id
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    authors = Follow.objects.filter(user=request.user)
    post_list = Post.objects.filter(author__id__in=authors)
    page_obj = make_paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    if request.user.is_authenticated:
        if request.user.username == username:
            return redirect('posts:profile', username=username)
        author = get_object_or_404(User, username=username)
        Follow.objects.create(user=request.user, author=author)
        return redirect('posts:profile', username=username)
    else:
        return redirect('users:sungup')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
