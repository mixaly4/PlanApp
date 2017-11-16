from django.conf.urls import url
from . import views

app_name = 'plan'
urlpatterns = [
	# regex, view, kwargs, name
	url(r'^$', views.index, name='index'),
	url(r'^project/(?P<project_id>[0-9]+)/(?P<time>[0-9]+)/$', views.project, name='project'),
	url(r'^create/project/$', views.create_project, name='create_project'),
	url(r'^submit/project/$', views.submit_project, name='submit_project'),
	url(r'^edit/project/(?P<project_id>[0-9]+)/$', views.edit_project, name='edit_project'),
	url(r'^delete/project/$', views.delete_project, name='delete_project'),
	url(r'^task/(?P<task_id>[0-9]+)/(?P<time>[0-1]+)/$', views.task, name='task'),
	url(r'^create/task/project/(?P<project_id>[0-9]+)/staff/(?P<staff_id>[0-9]+)/$', views.create_task, name='create_task'),
	url(r'^edit/task/(?P<task_id>[0-9]+)/project/(?P<project_id>[0-9]+)/staff/(?P<staff_id>[0-9]+)/$', views.edit_task, name='edit_task'),
	url(r'^delete/task/$', views.delete_task, name='delete_task'),
	url(r'^submit/task/$', views.submit_task, name='submit_task'),
	url(r'^staff/(?P<staff_id>[0-9]+)/$', views.staff, name='staff'),
	url(r'^calendar/all/$', views.calendar_page, name='calendar'),
	url(r'^calendar/project/(?P<project_id>[0-9]+)/$', views.calendar_project, name='calendar_project'),
	url(r'^calendar/staff/(?P<staff_id>[0-9]+)/$', views.calendar_staff, name='calendar_staff'),
]