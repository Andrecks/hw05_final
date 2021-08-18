from django.urls import path

from . import views


app_name = "posts"

urlpatterns = [
    path("", views.index, name="index"),
    # лента подписок
    path("follow/", views.follow_index, name="follow_index"),
    path("new/", views.new_post, name="new_post"),
    path("<str:username>/", views.profile, name="profile"),
    path("<str:username>/follow/", views.profile_follow,
         name="profile_follow"),  # подписка на юзера
    path("<str:username>/unfollow/", views.profile_unfollow,
         name="profile_unfollow"),  # отписка от юзера

    path("group/<str:slug>/", views.group_posts, name="group_posts"),
    # Профайл пользователя
    # Просмотр записи
    path("<str:username>/<int:post_id>/", views.post_view, name="post"),
    path("<str:username>/<int:post_id>/edit/",
         views.post_edit, name="post_edit"),
    path("<str:username>/<int:post_id>/comment", views.add_comment,
         name="add_comment"),
    path("<str:username>/<int:post_id>/delete/",
         views.post_delete, name="post_delete"),
]
