from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
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

    def test_post_labels(self):
        """verbose_name полей post совпадает с ожидаемым."""
        field_verbose_names = {
            self.post._meta.get_field('text').verbose_name: 'Текст поста',
            self.post._meta.get_field('group').verbose_name: 'Группа',
            self.post._meta.get_field('image').verbose_name: 'Картинка',
        }
        for field, verbose_name in field_verbose_names.items():
            with self.subTest(verbose_name=verbose_name):
                self.assertEqual(field, verbose_name, 'Ошибка в verbose_name')

    def test_post_help_texts(self):
        """help_text полей post совпадает с ожидаемым."""
        field_help_text = {
            self.post._meta.get_field('text').help_text: 'Текст нового поста',
            self.post._meta.get_field('group').help_text:
            'Группа, к которой будет относиться пост',
        }
        for field, help_text in field_help_text.items():
            with self.subTest(help_text=help_text):
                self.assertEqual(field, help_text, 'Ошибка в help_text')
