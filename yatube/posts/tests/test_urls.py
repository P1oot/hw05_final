from django.core.cache import cache
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus
from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.auth,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.auth_of_post = Client()
        self.user = User.objects.create_user(username='user')
        self.authorized_client.force_login(self.user)
        self.auth_of_post.force_login(self.auth)
        cache.clear()

    def test_urls_exists_at_desired_location(self):
        """Страницы '/', '/group/test-slug/', '/profile/user/',
        '/posts/{self.post.id}/', доступны неавторизованному пользователю,
        '/unexissting_page/': 404"""
        template_answer = {
            '/': HTTPStatus.OK,
            f'/group/{self.post.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.post.author.username}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            '/unexissting_page/': HTTPStatus.NOT_FOUND,
        }
        for template, answer in template_answer.items():
            with self.subTest(template=template):
                response = self.guest_client.get(template)
                self.assertEqual(response.status_code, answer)

    def test_post_edit_url_exists_at_desired_location_author(self):
        """Страница /posts/post_id/edit/ доступна автору поста."""
        response = self.auth_of_post.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_exists_at_desired_location_authorized(self):
        """Страница /create/ доступна авторизованному
        пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirect_not_author_on_post_detail(self):
        """Страница по адресу /posts/post_id/edit/ перенаправит не автора
        поста на страницу информации о посте."""
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/', follow=True
        )
        self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_add_comment_url_redirect_authorized_client_on_post_detail(self):
        """Страница по адресу /posts/post_id/comment/ перенаправит комментатора
        на страницу информации о посте."""
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/comment/', follow=True
        )
        self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_prifile_follow_url_redirect_authorized_client_on_post_detail(
        self
    ):
        """Страница по адресу /posts/post_id/follow/ подписавшегося
        на страницу информации о посте."""
        response = self.authorized_client.get(
            f'/profile/{self.post.author.username}/follow/',
            follow=True
        )
        self.assertRedirects(
            response,
            f'/profile/{self.post.author.username}/'
        )

    def test_prifile_unfollow_url_redirect_authorized_client_on_post_detail(
        self
    ):
        """Страница по адресу /posts/post_id/unfollow/ отписавшегося
        на страницу информации о посте."""
        response = self.authorized_client.get(
            f'/profile/{self.post.author.username}/unfollow/',
            follow=True
        )
        self.assertRedirects(
            response,
            f'/profile/{self.post.author.username}/'
        )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_names_templates = {
            '/': 'posts/index.html',
            f'/group/{self.post.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.post.author.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in url_names_templates.items():
            with self.subTest(address=address):
                response = self.auth_of_post.get(address)
                self.assertTemplateUsed(response, template)

    def test_index_cache(self):
        """Проверка работы кеширования на странице index"""
        object_to_delete = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=self.group,
        )
        response = self.authorized_client.get(reverse('posts:index'))
        page_content = response.content
        object_to_delete.delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(page_content, response.content)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(page_content, response.content)
