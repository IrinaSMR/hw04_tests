from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

NEW_TEXT = 'Новый пост'
UPDATED_TEXT = 'Обновленный текст'


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Irina')
        cls.group = Group.objects.create(
            title=('Название тестовой группы'),
            slug='night',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            group=cls.group,
            author=cls.user,
            text='Текст тестового поста'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'group': PostFormTests.group.id,
            'text': NEW_TEXT
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:profile', args=[PostFormTests.user]))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=PostFormTests.group.id,
                text=NEW_TEXT).exists())

    def test_post_edit(self):
        form_data = {
            'group': self.group.id,
            'text': UPDATED_TEXT,
        }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data, follow=True)
        result = Post.objects.get(id=self.post.id)
        self.assertEqual(result.text, UPDATED_TEXT)
