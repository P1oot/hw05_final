import shutil
import tempfile
from posts.forms import PostForm
from posts.models import Post, Group, Comment
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.new_group = Group.objects.create(
            title='Новая тестовая группа',
            slug='new-test-slug',
            description='Тестовое описание новой группы',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.auth,
            group=cls.group,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.auth)

    def small_gif_creation(self, name):
        """Создание картинки"""
        small_gif = (
             b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name=name+'.gif',
            content=small_gif,
            content_type='image/gif'
        )
        return uploaded

    def test_post_create(self):
        """Валидная форма создает запись в Post"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст 2',
            'group': self.group.id,
            'image': self.small_gif_creation('small_create'),
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст 2',
                group=self.group,
            ).exists()
        )
        self.assertTrue(
            Post.objects.filter(
                image='posts/small_create.gif'
            ).exists()
        )
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': self.post.author.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_post_edit(self):
        """Проверка изменениыя поста через форму"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Измененный текст',
            'group': self.new_group.id,
            'image': self.small_gif_creation('small_edit')
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                text='Измененный текст',
                group=self.new_group,
            ).exists()
        )
        self.assertTrue(
            Post.objects.filter(
                image='posts/small_edit.gif'
            ).exists()
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': self.post.id}))
        self.assertEqual(Post.objects.count(), posts_count)

    def test_post_comment(self):
        """Проверка добавления комментария"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый текст комментария',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Comment.objects.filter(
                text='Тестовый текст комментария',
            ).exists()
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': self.post.id}))
        self.assertEqual(Comment.objects.count(), comment_count + 1)
