from django import forms
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group

User = get_user_model()


class PostVievsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_without_posts = Group.objects.create(
            title='Тестовая группа без постов',
            slug='test-slug-2',
            description='Тестовое описание',
        )
        small_gif = (
             b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.auth,
            group=cls.group,
            image=uploaded
        )

    def setUp(self):
        self.post_author = Client()
        self.post_author.force_login(self.auth)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.post.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.post.author.username}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.post_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def auth_text_group_test(self, obj):
        """Проверка шаблонов с контекстом модели Post"""
        context_objects = {
            obj.author.username: self.post.author.username,
            obj.text: self.post.text,
            obj.group.slug: self.post.group.slug,
            obj.id: self.post.id,
            obj.image: self.post.image,
        }
        for obj, value in context_objects.items():
            with self.subTest(obj=obj):
                self.assertEqual(obj, value)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.post_author.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.auth_text_group_test(first_object)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = (self.post_author.get(reverse('posts:group_list',
                    kwargs={'slug': self.post.group.slug})))
        first_object = response.context['page_obj'][0]
        self.auth_text_group_test(first_object)
        self.assertEqual(response.context.get('group').title,
                         self.group.title)
        self.assertEqual(response.context.get('group').description,
                         self.group.description)
        response_without_posts = (self.post_author.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group_without_posts.slug})
        ))
        self.assertEqual(len(response_without_posts.context['page_obj']), 0)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (self.post_author.get(reverse('posts:profile',
                    kwargs={'username': self.post.author.username})))
        first_object = response.context['page_obj'][0]
        self.auth_text_group_test(first_object)
        self.assertEqual(response.context.get('author').username,
                         self.post.author.username)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.post_author.
                    get(reverse('posts:post_detail',
                        kwargs={'post_id': self.post.id})))
        obj = response.context.get('post')
        self.auth_text_group_test(obj)
        self.assertEqual(response.context.get('count'), 1)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.post_author.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = (self.post_author.
                    get(reverse('posts:post_edit',
                                kwargs={'post_id': self.post.id})))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        context_value = {
            'is_edit': True,
            'post_id': self.post.id,
        }
        for name, value in context_value.items():
            with self.subTest(name=name):
                context = response.context.get(name)
                self.assertEqual(context, value)

    def test_following(self):
        self.authorized_client_1 = Client()
        self.authorized_client_2 = Client()
        self.user_1 = User.objects.create_user(username='user_1')
        self.user_2 = User.objects.create_user(username='user_2')
        self.authorized_client_1.force_login(self.user_1)
        self.authorized_client_2.force_login(self.user_2)
        self.authorized_client_1.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.post.author.username}
        ))
        response_1 = self.authorized_client_1.get(
            reverse('posts:follow_index')
        )
        response_2 = self.authorized_client_2.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(len(response_1.context['page_obj']), 1)
        self.assertEqual(len(response_2.context['page_obj']), 0)
        self.authorized_client_1.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.post.author.username}
        ))
        response_1 = self.authorized_client_1.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(len(response_1.context['page_obj']), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for _ in range(13):
            Post.objects.create(
                text='Тестовый текст',
                author=cls.auth,
                group=cls.group,
            )

    def template_name_creation(self):
        """Создание словаря с шаблонами"""
        return {
            reverse('posts:index'): 'index',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'group_list',
            reverse('posts:profile', kwargs={'username': self.auth.username}):
            'profile',
        }

    def test_first_page_contains_ten_records(self):
        """Количество постов на первой странице равно 10"""
        template_name = self.template_name_creation()
        for template, page_name in template_name.items():
            with self.subTest(page_name):
                response = self.client.get(template)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """Количество постов на второй странице равно 3"""
        template_name = self.template_name_creation()
        for template, page_name in template_name.items():
            with self.subTest(page_name):
                response = self.client.get(template + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)
