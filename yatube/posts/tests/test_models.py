from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post, Comment, Follow

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth = User.objects.create_user(username='auth')
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.auth,
            text='Тестовый пост',
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.auth,
            text='Тестовый комментарий',
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.auth,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        field_str = {
            self.post: self.post.text[:15],
            self.group: self.group.title
        }
        for model, expected_str in field_str.items():
            with self.subTest(model=model):
                self.assertEqual(expected_str,
                                 str(model), 'Ошибка в методе __str__')

    def test_verbose_name_labels(self):
        """verbose_name полей post совпадает с ожидаемым."""
        field_verbose_names = {
            self.group._meta.get_field('title').verbose_name: 'Группа',
            self.group._meta.get_field('description').verbose_name: 'Описание',
            self.post._meta.get_field('text').verbose_name: 'Текст поста',
            self.post._meta.get_field('author').verbose_name: 'Автор',
            self.post._meta.get_field('group').verbose_name: 'Группа',
            self.post._meta.get_field('image').verbose_name: 'Картинка',
            self.comment._meta.get_field('post').verbose_name: 'Пост',
            self.comment._meta.get_field('author').verbose_name:
            'Автор комментария',
            self.comment._meta.get_field('text').verbose_name: 'Комментарий',
            self.follow._meta.get_field('user').verbose_name: 'follower',
            self.follow._meta.get_field('author').verbose_name: 'following',
        }
        for field, verbose_name in field_verbose_names.items():
            with self.subTest(verbose_name=verbose_name):
                self.assertEqual(field, verbose_name, 'Ошибка в verbose_name')

    def test_help_texts_labels(self):
        """help_text полей post совпадает с ожидаемым."""
        field_help_text = {
            self.group._meta.get_field('title').help_text: 'Название группы',
            self.group._meta.get_field('description').help_text:
            'Описание группы',
            self.post._meta.get_field('text').help_text: 'Текст нового поста',
            self.post._meta.get_field('author').help_text: 'Автор поста',
            self.post._meta.get_field('group').help_text:
            'Группа, к которой будет относиться пост',
            self.comment._meta.get_field('post').help_text:
            'Пост с комментарием',
            self.comment._meta.get_field('author').help_text:
            'Автор комментария',
            self.comment._meta.get_field('text').help_text:
            'Комментарий к посту',
            self.follow._meta.get_field('user').help_text: 'Фолловер',
            self.follow._meta.get_field('author').help_text: 'Избранный автор',
        }
        for field, help_text in field_help_text.items():
            with self.subTest(help_text=help_text):
                self.assertEqual(field, help_text, 'Ошибка в help_text')
