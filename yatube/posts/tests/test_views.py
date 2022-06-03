from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostPagesTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(
            username='test_author'
        )

        cls.not_author = User.objects.create_user(
            username='test_not_author'
        )

        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_description'
        )
        cls.post = Post.objects.create(
            text='test_post',
            group=cls.group,
            author=cls.author
        )
        cls.template_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', args=[cls.group.slug]):
                'posts/group_list.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': cls.post.pk}):
                'posts/create_post.html',
            reverse('posts:profile', args=[cls.author.username]):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': cls.post.pk}):
                'posts/post_detail.html',
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html'
        }
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
 
    def setUp(self):
        self.guest_client = Client()
        self.auth_author_client = Client()
        self.auth_author_client.force_login(self.author)
        self.authorized_not_author_client = Client()
        self.authorized_not_author_client.force_login(self.not_author)   


    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        for url, template in PostPagesTest.template_names.items():
            with self.subTest(template=template):
                response = self.auth_author_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_index_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        response_post = response.context.get('page_obj').object_list[0]
        self.assertEqual(response_post.author, PostPagesTest.author)
        self.assertEqual(response_post.group, PostPagesTest.group)
        self.assertEqual(response_post.text, PostPagesTest.post.text)

    def test_profile_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile', args=[PostPagesTest.author.username])
        )
        response_author = response.context.get('author')
        response_count = response.context.get('post_count')
        response_post = response.context.get('page_obj').object_list[0]
        self.assertEqual(response_post.author, PostPagesTest.author)
        self.assertEqual(response_post.group, PostPagesTest.group)
        self.assertEqual(response_post.text, PostPagesTest.post.text)
        self.assertEqual(PostPagesTest.author, response_author)
        self.assertEqual(1, response_count)

    def test_post_detail_shows_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTest.post.pk})
        )
        response_post = response.context.get('post')
        response_count = response.context.get('post_count')
        self.assertEqual(response_post.author, PostPagesTest.author)
        self.assertEqual(response_post.group, PostPagesTest.group)
        self.assertEqual(response_post.text, PostPagesTest.post.text)
        self.assertEqual(PostPagesTest.post, response_post)
        self.assertEqual(1, response_count)

    def test_post_create_shows_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.auth_author_client.get(
            reverse('posts:post_create')
        )
        for field, expected in PostPagesTest.form_fields.items():
            with self.subTest(field=field):
                form_field = response.context['form'].fields[field]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_shows_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.auth_author_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostPagesTest.post.pk}))

        for field, expected in PostPagesTest.form_fields.items():
            with self.subTest(field=field):
                form_field = response.context['form'].fields[field]
                self.assertIsInstance(form_field, expected)

    def test_group_list_shows_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.auth_author_client.get(
            reverse('posts:group_list', args=[PostPagesTest.group.slug])
        )
        response_post = response.context.get('page_obj').object_list[0]
        self.assertEqual(response_post.author, PostPagesTest.author)
        self.assertEqual(response_post.group, PostPagesTest.group)
        self.assertEqual(response_post.text, PostPagesTest.post.text)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_description'
        )
        for i in range(13):
            cls.post = Post.objects.create(
                text=f'test_post{i}',
                group=cls.group,
                author=cls.author
            )

        cls.templates = [
            reverse('posts:index'),
            reverse('posts:group_list', args=[cls.group.slug]),
            reverse('posts:profile', args=[cls.author.username])
        ]

    def test_first_page_contains_ten_records(self):
        """Paginator предоставляет ожидаемое количество постов
         на первую страницую."""
        for address in PaginatorViewsTest.templates:
            with self.subTest():
                response = self.client.get(address)
                self.assertEqual(len(response.context.get(
                    'page_obj'
                ).object_list), settings.ITEMS_COUNT)

    def test_second_page_contains_three_records(self):
        """Paginator предоставляет ожидаемое количество постов
         на вторую страницую."""
        for address in PaginatorViewsTest.templates:
            with self.subTest():
                response = self.client.get(address + '?page=2')
                self.assertEqual(len(response.context.get(
                    'page_obj'
                ).object_list), 3)
