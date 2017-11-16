import datetime
import math
import calendar
import sys
from django.utils import timezone
from .gen_cal import get_project_context
from .gen_cal import get_project_tasks
from .gen_cal import get_project_plan
from .gen_cal import get_projects
from .gen_cal import get_tasks
from .gen_cal import get_week_tasks_context, get_lines_tasks_context
from .gen_cal import get_date_selection
from .gen_cal import ProjectDates
from .gen_cal import SetCal
from .plan_function import calendar_context, project_calendar_context, dashboard_context, project_task_dates, week_start, week_end

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.urls import reverse
from django.views import generic
from django.template import loader
from django.shortcuts import redirect
from .models import Staff, Department, Project, Task, Stream


def index(request):
	try:
		cal_setting = request.POST['cal_setting']
	except KeyError:
		cal_setting = 'this_week'
	else:
		cal_setting = request.POST['cal_setting']

	context = {'today': datetime.date.today(), 
				'dashboard': dashboard_context(show_empty = True, group_dash = 'department'), 
				'alt_cal': calendar_context(start = cal_setting, days_in_line = 35, num_lines = 2, obj = False, obj_id = False, group = 'department', row = 'staff', show_empty = True), 
				'staff_list' : Department.objects.all(), 
				'project_list': Stream.objects.all(), 
				'cal_setting': cal_setting, 
				'project_cal': project_calendar_context(start = datetime.date.today().replace(month = 1, day = 1)),}
	return render(request, 'plan/index.html', context)

def project(request, project_id, time):
	#project_task_dates()
	try:
		project = Project.objects.get(pk=project_id)
	except (KeyError, Project.DoesNotExist):
		project = False
		return HttpResponse("Failed to find project with ID'%s'! Try again." % project_id)

	if project:
		try:
			cal_setting = request.POST['cal_setting']
		except KeyError:
			cal_setting = 'this_week'
		else:
			cal_setting = request.POST['cal_setting']
		
		context = {'project': project, 'today': datetime.date.today(), 
					'dashboard': dashboard_context(project = project.id, obj = project, obj_id = project.id, show_empty = False, group_dash = 'department'), 
					'alt_cal': calendar_context(start = cal_setting, days_in_line = 35, num_lines = 2, obj = False, obj_id = False, group = 'department', row = 'staff', show_empty = True, project = project.id), 
					'staff_list' : Department.objects.all(), 
					'project_list': Stream.objects.all(), 
					'cal_setting': cal_setting,
					'calendar': calendar_context(start = 'all', days_in_line = int((week_end(project.end()) - week_start(project.start())) / datetime.timedelta(days=1) + 1), num_lines = 1, obj = project, obj_id = project.id, group = 'department', row = 'task', show_empty = False, project = project),}
		return render(request, 'plan/project.html', context)

def task(request, task_id, time):
	task = Task.objects.get(pk=task_id)
	context = {'task': task, 
				'days': int((task.end_date - task.start_date + datetime.timedelta(days=1)) / datetime.timedelta(days=1)),
				'staff_list' : Department.objects.all(), 
				'project_list': Stream.objects.all(),
				'time': int(time), 
				'timestamp': timezone.now().timestamp(),
				'today': datetime.date.today(),
				}
	return render(request, 'plan/task.html', context)

def staff(request, staff_id):
	staff = Staff.objects.get(pk = staff_id)
	if len(Task.objects.filter(active=True, staff_id = staff_id)) > 0:
		s = SetCal(datetime.date.today())
		try:
			cal_setting = request.POST['cal_setting']
		except KeyError:
			cal_setting = 'this_week'
		else:
			cal_setting = request.POST['cal_setting']
		data = get_project_context(0, staff=staff_id, start=s.start(cal_setting))
		t = []
		for p in Project.objects.all():
			a = p.task_set.filter(staff_id = staff_id, active = True).count()
			b = p.task_set.filter(staff_id = staff_id, active = True)
			if a > 0:
				t.append({'project': p, 'task_count': a, 'tasks' : b,})
		context = {'today': datetime.date.today(), 
					'staff': staff,
					'project_cal': project_calendar_context(start = datetime.date.today().replace(month = 1, day = 1), staff = staff_id),
					'alt_cal': calendar_context(start = cal_setting, days_in_line = 35, num_lines = 2, obj = staff, obj_id = int(staff_id), group = 'stream', row = 'project', show_empty = True),
					'dashboard': dashboard_context(staff = staff.id, obj = staff, obj_id = staff.id, show_empty = False, group_dash = 'stream', row='project'),
					'staff_list' : Department.objects.all(), 
					'project_list': Stream.objects.all(), 
					'task_count' : t, 
					'lines': data['lines'], 
					'row_names': data['row_names'], 
					'rows': data['rows'], 
					'cal_setting': cal_setting,}
	else:
		context = {'today': datetime.date.today(), 'staff_list' : Department.objects.all(), 'project_list': Stream.objects.all(), 'staff': staff, }

	return render(request, 'plan/staff.html', context)

def create_project(request):
	context = {'staff_list' : Department.objects.all(), 
				'project_list': Stream.objects.all(), 
				'stream_list': Stream.objects.all(),
				'date': get_date_selection(),
				'edit': False,
				'today': datetime.date.today(),
				}
	return render(request, 'plan/create_project.html', context)

def edit_project(request, project_id):
	project = Project.objects.get(pk = project_id)
	selected = {'project': project, 
				'name': project.name,
				'stream': project.stream,
				'comment': project.comment,
				'start_date': project.start(),
				'end_date': project.end(),
				'task_num': project.tasks(),}

	context = {'project_list' : Stream.objects.all(), 
				'staff_list' : Department.objects.all(),
				'stream_list': Stream.objects.all(),
				'date': get_date_selection(),
				'selected': selected, 
				'edit': project.id, 
				'timestamp': timezone.now().timestamp(),
				'today': datetime.date.today(),
				}
	
	return render(request, 'plan/create_project.html', context)

def create_task(request, project_id, staff_id):
	p_id = int(project_id)
	s_id = int(staff_id)

	s = SetCal(datetime.date.today())
	try:
		cal_setting = request.POST['cal_setting']
	except KeyError:
		cal_setting = 'this_week'
	else:
		cal_setting = request.POST['cal_setting']

	if request.GET.get('comment', False) : comment = request.GET.get('comment', False)
	else: comment = False

	if request.GET.get('name', False) : name = request.GET.get('name', False)
	else: name = False

	if request.GET.get('sday', False) and request.GET.get('smonth', False) and request.GET.get('syear', False): 
		start_date = {'day': False, 'month': False, 'year': False}
		try: start_date['day'] = int(request.GET.get('sday', False))
		except ValueError: start_date['day'] = False
		try: start_date['month'] = int(request.GET.get('smonth', False))
		except ValueError: start_date['month'] = False
		try: start_date['year'] = int(request.GET.get('syear', False))
		except ValueError: start_date['year'] = False
		if start_date['year']:
			if not start_date['year'] >= datetime.date.today().year: start_date['year'] = False
		if start_date['month']:
			if not (start_date['month'] >= 1 and start_date['month'] <= 12): start_date['month'] = False
		if start_date['day'] and start_date['day'] > 0 and start_date['day'] < 32:
			if start_date['month'] and start_date['year'] and not (start_date['day'] <= calendar.monthrange(start_date['year'], start_date['month'])[1]):
				start_date['day'] = calendar.monthrange(start_date['year'], start_date['month'])[1]
		else: start_date['day'] = False
	else: start_date = {'day': False, 'month': False, 'year': False}

	if request.GET.get('eday', False) and request.GET.get('emonth', False) and request.GET.get('eyear', False): 
		end_date = {'day': False, 'month': False, 'year': False}
		try: end_date['day'] = int(request.GET.get('eday', False))
		except ValueError: end_date['day'] = False
		try: end_date['month'] = int(request.GET.get('emonth', False))
		except ValueError: end_date['month'] = False
		try: end_date['year'] = int(request.GET.get('eyear', False))
		except ValueError: end_date['year'] = False
		if end_date['year']:
			if not end_date['year'] >= datetime.date.today().year: end_date['year'] = False
		if end_date['month']:
			if not (end_date['month'] >= 1 and end_date['month'] <= 12): end_date['month'] = False
		if end_date['day'] and end_date['day'] > 0 and end_date['day'] < 32:
			if end_date['month'] and end_date['year'] and not (end_date['day'] <= calendar.monthrange(end_date['year'], end_date['month'])[1]):
				end_date['day'] = calendar.monthrange(end_date['year'], end_date['month'])[1]
		else: end_date['day'] = False
	else: end_date = {'day': False, 'month': False, 'year': False}

	selected = {'project': False, 
				'staff': False, 
				'project_lines': False, 
				'staff_lines' : False,
				'name': name, 'comment': comment,
				'start_date': start_date,
				'end_date': end_date,
				}
	if p_id > 0:
		selected['project'] = Project.objects.filter(pk = p_id)[0]
		if selected['project'].task_set.filter(active=True).count() > 0:
			selected['project_lines'] = get_project_context(p_id, start=s.start(cal_setting))
			selected['project_lines_new'] = calendar_context(start = 'all', days_in_line = 35, num_lines = False, obj = selected['project'], obj_id = p_id, group = 'department', row = 'staff', show_empty = True, project = p_id)
	if s_id > 0:
		selected['staff'] = Staff.objects.filter(pk = s_id)[0]
		if selected['staff'].task_set.filter(active=True).count() > 0:
			selected['staff_lines_new'] = calendar_context(start = cal_setting, days_in_line = 35, num_lines = 2, obj = Staff.objects.filter(pk = s_id)[0], obj_id = int(s_id), group = 'stream', row = 'project', show_empty = True)

	context = {'today': datetime.date.today(),
				'staff_list' : Department.objects.all(), 
				'project_list': Stream.objects.all(),
				'project_select' : Project.objects.filter(active=True), 
				'staff_select' : Staff.objects.filter(active=True), 
				'date': get_date_selection(), 
				'selected': selected, 
				'edit': False, 
				'cal_setting': cal_setting,
				'today': datetime.date.today(),
				}
	
	return render(request, 'plan/create_task.html', context)

def edit_task(request, task_id, project_id, staff_id):
	task = Task.objects.get(pk = task_id)
	s = SetCal(datetime.date.today())
	try:
		cal_setting = request.POST['cal_setting']
	except KeyError:
		cal_setting = 'this_week'
	else:
		cal_setting = request.POST['cal_setting']

	if request.GET.get('comment', False) : comment = request.GET.get('comment', False)
	else: comment = task.comment

	if request.GET.get('name', False) : name = request.GET.get('name', False)
	else: name = task.name

	if request.GET.get('sday', False) and request.GET.get('smonth', False) and request.GET.get('syear', False): 
		start_date = {'day': False, 'month': False, 'year': False}
		try: start_date['day'] = int(request.GET.get('sday', False))
		except ValueError: start_date['day'] = task.start_date.day
		try: start_date['month'] = int(request.GET.get('smonth', False))
		except ValueError: start_date['month'] = task.start_date.month
		try: start_date['year'] = int(request.GET.get('syear', False))
		except ValueError: start_date['year'] = task.start_date.year
		if start_date['year']:
			if not start_date['year'] >= datetime.date.today().year: start_date['year'] = task.start_date.year
		if start_date['month']:
			if not (start_date['month'] >= 1 and start_date['month'] <= 12): start_date['month'] = task.start_date.month
		if start_date['day'] and start_date['day'] > 0 and start_date['day'] < 32:
			if start_date['month'] and start_date['year'] and not (start_date['day'] <= calendar.monthrange(start_date['year'], start_date['month'])[1]):
				start_date['day'] = calendar.monthrange(start_date['year'], start_date['month'])[1]
		else: start_date['day'] = task.start_date.day
	else: start_date = task.start_date

	if request.GET.get('eday', False) and request.GET.get('emonth', False) and request.GET.get('eyear', False): 
		end_date = {'day': False, 'month': False, 'year': False}
		try: end_date['day'] = int(request.GET.get('eday', False))
		except ValueError: end_date['day'] = task.end_date.day
		try: end_date['month'] = int(request.GET.get('emonth', False))
		except ValueError: end_date['month'] = task.end_date.month
		try: end_date['year'] = int(request.GET.get('eyear', False))
		except ValueError: end_date['year'] = task.end_date.year
		if end_date['year']:
			if not end_date['year'] >= datetime.date.today().year: end_date['year'] = task.end_date.year
		if end_date['month']:
			if not (end_date['month'] >= 1 and end_date['month'] <= 12): end_date['month'] = task.end_date.month
		if end_date['day'] and end_date['day'] > 0 and end_date['day'] < 32:
			if end_date['month'] and end_date['year'] and not (end_date['day'] <= calendar.monthrange(end_date['year'], end_date['month'])[1]):
				end_date['day'] = calendar.monthrange(end_date['year'], end_date['month'])[1]
		else: end_date['day'] = task.end_date.day
	else: end_date = task.end_date

	selected = {'project': task.project, 'staff': task.staff, 
				'project_lines_new': calendar_context(start = s.start(cal_setting), days_in_line = 35, num_lines = 2, obj = False, obj_id = False, group = 'department', row = 'staff', show_empty = True, project = task.project.id),
				'staff_lines_new' : calendar_context(start = s.start(cal_setting), days_in_line = 35, num_lines = 2, obj = task.staff, obj_id = int(task.staff.id), group = 'stream', row = 'project', show_empty = True),
				'name': name, 'comment': comment, 'task': task,
				'start_date': start_date,
				'end_date': end_date,
				}
	p_id = int(project_id)
	s_id = int(staff_id)
	if p_id and p_id > 0:
		selected['project'] = Project.objects.filter(pk = p_id)[0]
		if len(Task.objects.filter(active=1, project_id = p_id)) > 0:
			selected['project_lines_new'] = calendar_context(start = 'all', days_in_line = 35, num_lines = False, obj = selected['project'], obj_id = p_id, group = 'department', row = 'staff', show_empty = True, project = p_id)
		else: selected['project_lines_new'] = False
	if s_id and s_id > 0:
		selected['staff'] = Staff.objects.filter(pk = s_id)[0]
		if len(Task.objects.filter(active=1, staff_id = s_id)) > 0:
			selected['staff_lines_new'] = calendar_context(start = s.start(cal_setting), days_in_line = 35, num_lines = 2, obj = Staff.objects.filter(pk = s_id)[0], obj_id = int(s_id), group = 'stream', row = 'project', show_empty = True)
		else: selected['staff_lines_new'] = False

	context = {'staff_list' : Department.objects.all(), 
				'project_list': Stream.objects.all(),
				'project_select' : Project.objects.filter(active=True), 
				'staff_select' : Staff.objects.filter(active=True), 
				'date': get_date_selection(), 
				'selected': selected, 
				'edit': True, 
				'timestamp': timezone.now().timestamp(), 
				'cal_setting': cal_setting,
				'today': datetime.date.today(),
				}
	
	return render(request, 'plan/create_task.html', context)

def submit_project(request):
	errors = {'error': False, 'project': False, 'name': False, 'comment': False, 'start_date': False, 'end_date': False, 'stream': False, 'edit': False, 'timestamp': False, 'database': False}

	try: i = int(request.POST['edit'])
	except ValueError:
		i = False
		errors['error'] = True
		errors['edit'] = ['Oops! Something went wrong in transfering data from the form. Please re-enter the project create/edit page. 201']
	except:
		i = False
		errors['error'] = True
		errors['edit'] = ['Oops! Something went wrong in transfering data from the form. Please re-enter the project create/edit page. 202']

	#checking validity of edit & project data
	if i and i > 0:
		try: project = Project.objects.get(id = i)
		except (KeyError, Project.DoesNotExist):
			project = False
			errors['error'] = True
			errors['database'] = ['Oops! Something went wrong. The project you would like to update does not exist. 212']
		except:
			project = False
			errors['error'] = True
			errors['database'] = ['Oops! Something went wrong. Cannot identify the project you are trying to edit. Please try again. 216']
	else: project = False

	#checking validity of name data
	if type(request.POST['name']) == str: 
		if len(request.POST['name']) >= 3 and len(request.POST['name']) <= 200:
			name = request.POST['name']
		elif len(request.POST['name']) < 3:
			name = False
			errors['error'] = True
			errors['name'] = ['Name of project must be at least 3 characters long']
		elif len(request.POST['name']) > 200:
			name = False
			errors['error'] = True
			errors['name'] = ['Name of project must be no more than 200 characters long']
	elif type(request.POST['name']) != str:
		name = False
		errors['error'] = True
		errors['name'] = ['Oops! Something went wrong and name data was not in string format. Please re-enter the project create/edit page. 203']
	else:
		name = False
		errors['error'] = True
		errors['name'] = ['Oops! Something went wrong and name data is missing. Please re-enter the project create/edit page. 217']

	#checking validity of comment data
	if type(request.POST['comment']) == str: 
		if len(request.POST['comment']) <= 500 and len(request.POST['comment']) > 0:
			comment = request.POST['comment']
		elif len(request.POST['comment']) == 0:
			comment = None
		else:
			comment = False
			errors['error'] = True
			errors['comment'] = ['Comment of project must be no more than 500 characters long']
	elif request.POST['comment']:
		comment = False
		errors['error'] = True
		errors['comment'] = ['Oops! Something went wrong and comment data was not in string format. Please re-enter the project create/edit page. 203']
	else:
		comment = None

	#checking validity of stream data
	if request.POST['stream']:
		try: s = int(request.POST['stream'])
		except ValueError:
			s = False
			errors['error'] = True
			errors['stream'] = ['Oops! Something went wrong and stream data was not a number. Please re-enter the project create/edit page. 207']
		except:
			s = False
			errors['error'] = True
			errors['stream'] = ['Oops! Something went wrong and stream data was not a number. Please re-enter the project create/edit page. 208']
		if s:
			try: stream = Stream.objects.get(id = s)
			except (KeyError, Stream.DoesNotExist):
				stream = False
				errors['error'] = True
				errors['stream'] = ['The stream to which you would like to assign the project does not exist.']
			except:
				stream = False
				errors['error'] = True
				errors['stream'] = ['Oops! Something went wrong when trying to locate the relevant stream. 209']
		else: 
			stream = False
			errors['error'] = True
			errors['stream'] = ['Please select the stream.']
	else:
		s = False
		stream = False
		errors['error'] = True
		errors['stream'] = ['Oops! Something went wrong and stream data is missing. Please re-enter the project create/edit page. 220']

	#checking validity of start date
	#firstly if it is creation of a new project -> the dates are compulsory to be their OR if it is editing the project 
	if (type(i) == int and i == 0) or (type(i) == int and project and not project.tasks()):
		if request.POST['start_date_year'] and request.POST['start_date_month'] and request.POST['start_date_day']: 
			start_date = {'day': False, 'month': False, 'year': False}
			try: start_date['day'] = int(request.POST['start_date_day'])
			except ValueError: 
				start_date['day'] = False
				errors['error'] = True
				if not errors['start_date'] : errors['start_date'] = []
				errors['start_date'].append('Start date day data is not a number')
			except:
				start_date['day'] = False
				errors['error'] = True
				if not errors['start_date'] : errors['start_date'] = []
				errors['start_date'].append('Start date day data could not be converted to integer')
			if start_date['day'] and (start_date['day'] > 31 or start_date['day'] < 1):
				start_date['day'] = False
				errors['error'] = True
				if not errors['start_date'] : errors['start_date'] = []
				errors['start_date'].append('Start date day must be in the range between 1 and 31 inclusive')

			try: start_date['month'] = int(request.POST['start_date_month'])
			except ValueError: 
				start_date['month'] = False
				errors['error'] = True
				if not errors['start_date'] : errors['start_date'] = []
				errors['start_date'].append('Start date month data is not a number')
			except:
				start_date['month'] = False
				errors['error'] = True
				if not errors['start_date'] : errors['start_date'] = []
				errors['start_date'].append('Start date month data could not be converted to integer')
			if start_date['month'] and (start_date['month'] > 12 or start_date['month'] < 1):
				start_date['month'] = False
				errors['error'] = True
				if not errors['start_date'] : errors['start_date'] = []
				errors['start_date'].append('Start date month must be in the range between 1 and 12 inclusive')

			try: start_date['year'] = int(request.POST['start_date_year'])
			except ValueError: 
				start_date['year'] = False
				errors['error'] = True
				if not errors['start_date'] : errors['start_date'] = []
				errors['start_date'].append('Start date year data is not a number')
			except:
				start_date['year'] = False
				errors['error'] = True
				if not errors['start_date'] : errors['start_date'] = []
				errors['start_date'].append('Start date year data could not be converted to integer')
			if start_date['year'] and (datetime.date.today().year - start_date['year'] > 1):
				start_date['year'] = False
				errors['error'] = True
				if not errors['start_date'] : errors['start_date'] = []
				errors['start_date'].append('Start date year can be at most 1 year behind today')

			if start_date['year'] and start_date['month'] and start_date['day'] and start_date['day'] > calendar.monthrange(start_date['year'], start_date['month'])[1]:
				start_date['day'] = False
				errors['error'] = True
				if not errors['start_date'] : errors['start_date'] = []
				errors['start_date'].append('Start date day is out of range for given month and year, max number of days is: ' + str(calendar.monthrange(start_date['year'], start_date['month'])[1]))

			if start_date['year'] and start_date['month'] and start_date['day'] and errors['start_date'] == False:
				try: S_date = datetime.date(start_date['year'], start_date['month'], start_date['day'])
				except: 
					S_date = False
					errors['error'] = True
					if not errors['start_date'] : errors['start_date'] = []
					errors['start_date'].append('Oops! Something went wrong. Unable to create start date from data provided. Please try again. 214')
			else: S_date = False
		else:
			S_date = False
			start_date = {'day': False, 'month': False, 'year': False}
			errors['error'] = True
			if not errors['start_date'] : errors['start_date'] = []
			errors['start_date'].append('Oops! Something went wrong and some of start date data is missing. Please re-enter the project create/edit page. 221')

		#checking validity of end date
		if request.POST['end_date_year'] and request.POST['end_date_month'] and request.POST['end_date_day']: 
			end_date = {'day': False, 'month': False, 'year': False}
			try: end_date['day'] = int(request.POST['end_date_day'])
			except ValueError: 
				end_date['day'] = False
				errors['error'] = True
				if not errors['end_date'] : errors['end_date'] = []
				errors['end_date'].append('End date day data is not a number')
			except:
				end_date['day'] = False
				errors['error'] = True
				if not errors['end_date'] : errors['end_date'] = []
				errors['end_date'].append('End date day data could not be converted to integer')
			if end_date['day'] and (end_date['day'] > 31 or end_date['day'] < 1):
				end_date['day'] = False
				errors['error'] = True
				if not errors['end_date'] : errors['end_date'] = []
				errors['end_date'].append('End date day must be in the range between 1 and 31 inclusive')

			try: end_date['month'] = int(request.POST['end_date_month'])
			except ValueError: 
				end_date['month'] = False
				errors['error'] = True
				if not errors['end_date'] : errors['end_date'] = []
				errors['end_date'].append('End date month data is not a number')
			except:
				end_date['month'] = False
				errors['error'] = True
				if not errors['end_date'] : errors['end_date'] = []
				errors['end_date'].append('End date month data could not be converted to integer')
			if end_date['month'] and (end_date['month'] > 12 or end_date['month'] < 1):
				end_date['month'] = False
				errors['error'] = True
				if not errors['end_date'] : errors['end_date'] = []
				errors['end_date'].append('End date month must be in the range between 1 and 12 inclusive')

			try: end_date['year'] = int(request.POST['end_date_year'])
			except ValueError: 
				end_date['year'] = False
				errors['error'] = True
				if not errors['end_date'] : errors['end_date'] = []
				errors['end_date'].append('End date year data is not a number')
			except:
				end_date['year'] = False
				errors['error'] = True
				if not errors['end_date'] : errors['end_date'] = []
				errors['end_date'].append('End date year data could not be converted to integer')
			if end_date['year'] and (datetime.date.today().year - end_date['year'] > 1):
				end_date['year'] = False
				errors['error'] = True
				if not errors['end_date'] : errors['end_date'] = []
				errors['end_date'].append('End date year can be at most 1 year behind today')

			if end_date['year'] and end_date['month'] and end_date['day'] and end_date['day'] > calendar.monthrange(end_date['year'], end_date['month'])[1]:
				end_date['day'] = False
				errors['error'] = True
				if not errors['end_date'] : errors['end_date'] = []
				errors['end_date'].append('End date day is out of range for given month and year, max number of days is: ' + str(calendar.monthrange(end_date['year'], end_date['month'])[1]))

			if end_date['year'] and end_date['month'] and end_date['day'] and errors['end_date'] == False:
				try: E_date = datetime.date(end_date['year'], end_date['month'], end_date['day'])
				except: 
					E_date = False
					errors['error'] = True
					if not errors['end_date'] : errors['end_date'] = []
					errors['end_date'].append('Oops! Something went wrong. Unable to create end date from data provided. Please try again. 215')
			else: E_date = False

			if E_date and S_date and E_date < S_date:
				E_date = False
				end_date = {'day': False, 'month': False, 'year': False}
				errors['error'] = True
				if not errors['end_date'] : errors['end_date'] = []
				errors['end_date'].append('End date must be greater or equal to start date')
		else:
			E_date = False
			end_date = {'day': False, 'month': False, 'year': False}
			errors['error'] = True
			if not errors['end_date'] : errors['end_date'] = []
			errors['end_date'].append('Oops! Something went wrong and some of start date data is missing. Please re-enter the task create/edit page. 222')
	else:
		S_date = False
		E_date = False
		start_date = {'day': False, 'month': False, 'year': False}
		end_date = {'day': False, 'month': False, 'year': False}

	#checking timestamp value validity
	if project:
		if request.POST['timestamp']:
			try: time = float(request.POST['timestamp'])
			except:
				time = False
				errors['error'] = True
				errors['timestamp'] = ['Oops! Something went wrong with timing of request. Please re-enter the page. 210']
		else:
			time = False
			errors['error'] = True
			errors['timestamp'] = ['Oops! Something went wrong and timing of requst data is missing. Please re-enter the page. 223']

	if not errors['error']:
		if i == 0:
			try: 
				project = Project.objects.create(name = name, stream_id = stream.id, start_date = S_date, end_date = E_date, comment = comment)
				return HttpResponseRedirect(reverse('plan:project', args=(project.id, 0)))
			except:
				print("Unexpected error:", sys.exc_info()[0])
				project = False
				errors['error'] = True
				errors['database'] = ['Oops! Something went wrong. New project was not created, please reload and try again. 211']
		elif type(project) == Project:
			try:
				if time > project.update.timestamp():
					project.name = name
					project.stream_id = stream.id
					project.comment = comment
					if not project.tasks():
						project.start_date = S_date
						project.end_date = E_date
					project.update = timezone.now()
					project.save()
					return HttpResponseRedirect(reverse('plan:project', args=(project.id, 0)))
				else:
					project = False
					errors['error'] = True
					errors['timestamp'] = ['The project has been updated while you were updating it. Your data was not saved.']
			except:
				print("Unexpected error:", sys.exc_info()[0])
				project = False
				errors['error'] = True
				errors['database'] = ['Oops! Something went wrong when trying to update the project. 213']
	
	if errors['error']:
		selected = {'project': False, 'stream': False, 'name': False, 'comment': False, 'start_date': False, 'end_date': False, 'task_num': False,}

		if not errors['project'] and project: 
			selected['project'] = project
			selected['task_num'] = project.tasks()

		if not errors['stream'] and stream: selected['stream'] = stream
		elif not stream and project: selected['stream'] = project.stream

		if not errors['name'] and name: selected['name'] = name
		elif not name and project: selected['name'] = project.name

		if not errors['comment']: selected['comment'] = comment
		elif not comment and project: selected['comment'] = project.comment

		if S_date and not errors['start_date']: selected['start_date'] = S_date
		elif type(i) == int:
			selected['start_date'] = start_date
			if not start_date['day'] and project and not project.tasks(): selected['start_date']['day'] = project.start_date.day
			if not start_date['month'] and project and not project.tasks(): selected['start_date']['month'] = project.start_date.month
			if not start_date['year'] and project and not project.tasks(): selected['start_date']['year'] = project.start_date.year

		if E_date and not errors['end_date']: selected['end_date'] = E_date
		elif type(i) == int:
			selected['end_date'] = end_date
			if not end_date['day'] and project and not project.tasks(): selected['end_date']['day'] = project.end_date.day
			if not end_date['month'] and project and not project.tasks(): selected['end_date']['month'] = project.end_date.month
			if not end_date['year'] and project and not project.tasks(): selected['end_date']['year'] = project.end_date.year

		errors_names = {'name': 'Title', 'comment': 'Comment', 'start_date': 'Start Date', 'end_date': 'End Date', 'project': 'Project', 'stream': 'Stream', 'edit': 'Edit/Create', 'timestamp': 'Request Timing', 'database': 'Database'}
		keys = list(errors.keys())
		keys.remove('error')
		errors['texts'] = []
		for k in keys:
			errors['texts'].append({'location': errors_names[k],'text': errors[k]})

		if i and i == 0: edit = False
		elif i and i > 0: edit = i
		else: edit = False
		
		context = {'project_list' : Stream.objects.all(),
				'staff_list' : Department.objects.all(),
				'stream_list' : Stream.objects.all(), 
				'date': get_date_selection(), 
				'selected': selected, 
				'edit': edit, 
				'timestamp': timezone.now().timestamp(), 
				'cal_setting': 'this_week',
				'today': datetime.date.today(),
				'errors': errors,
				}
		return render(request, 'plan/create_project.html', context)

def delete_project(request):
	i = int(request.POST['edit'])
	d = int(request.POST['delete'])
	name = request.POST['name']
	time = float(request.POST['timestamp'])
	if i == d and d > 0:
		try:
			p = Project.objects.get(pk=d)
		except (KeyError, Project.DoesNotExist):
			return HttpResponse("Failed to find project '%s'! Try again." % name)
		else:
			if time > p.update.timestamp():
				p.delete()
				return HttpResponseRedirect(reverse('plan:index'))
			else:
				return HttpResponseRedirect(reverse('plan:project', args=(p.id, 1)))
	else:
		return HttpResponse("Something went wrong during update to '%s'! Try again." % name)
		

def submit_task(request):
	errors = {'error': False, 'name': False, 'comment': False, 'start_date': False, 'end_date': False, 'project': False, 'staff': False, 'edit': False, 'timestamp': False, 'database': False}

	try: i = int(request.POST['edit'])
	except ValueError:
		i = False
		errors['error'] = True
		errors['edit'] = ['Oops! Something went wrong in transfering data from the form. Please re-enter the task create/edit page. 101']
	except:
		i = False
		errors['error'] = True
		errors['edit'] = ['Oops! Something went wrong in transfering data from the form. Please re-enter the task create/edit page. 102']

	#checking validity of edit & task data
	if i and i > 0:
		try: task = Task.objects.get(id = i)
		except (KeyError, Task.DoesNotExist):
			task = False
			errors['error'] = True
			errors['database'] = ['Oops! Something went wrong. The task you would like to update does not exist. 112']
		except:
			task = False
			errors['error'] = True
			errors['database'] = ['Oops! Something went wrong. Cannot identify the task you are trying to edit. Please try again. 116']
	else: task = False
	
	#checking validity of name data
	if request.POST['name'] and type(request.POST['name']) == str: 
		if len(request.POST['name']) >= 3 and len(request.POST['name']) <= 200:
			name = request.POST['name']
		elif len(request.POST['name']) < 3:
			name = False
			errors['error'] = True
			errors['name'] = ['Name of task must be at least 3 characters long']
		elif len(request.POST['name']) > 200:
			name = False
			errors['error'] = True
			errors['name'] = ['Name of task must be no more than 200 characters long']
	elif request.POST['name']:
		name = False
		errors['error'] = True
		errors['name'] = ['Oops! Something went wrong and name data was not in string format. Please re-enter the task create/edit page. 103']
	else:
		name = False
		errors['error'] = True
		errors['name'] = ['Oops! Something went wrong and name data is missing. Please re-enter the task create/edit page. 117']

	#checking validity of comment data
	if request.POST['comment'] and type(request.POST['comment']) == str: 
		if len(request.POST['comment']) <= 500:
			comment = request.POST['comment']
		else:
			comment = False
			errors['error'] = True
			errors['comment'] = ['Comment of task must be no more than 500 characters long']
	elif request.POST['comment']:
		comment = False
		errors['error'] = True
		errors['comment'] = ['Oops! Something went wrong and comment data was not in string format. Please re-enter the task create/edit page. 103']
	else:
		comment = None

	#checking validity of project data
	if request.POST['project']:
		try: p = int(request.POST['project'])
		except ValueError:
			p = False
			errors['error'] = True
			errors['project'] = ['Oops! Something went wrong and project data was not a number. Please re-enter the task create/edit page. 104']
		except:
			p = False
			errors['error'] = True
			errors['project'] = ['Oops! Something went wrong and project data was not a number. Please re-enter the task create/edit page. 105']
		if p:
			try: project = Project.objects.get(id = p)
			except (KeyError, Project.DoesNotExist):
				project = False
				errors['error'] = True
				errors['project'] = ['The project to which you would like to assign the task does not exist.']
			except:
				project = False
				errors['error'] = True
				errors['project'] = ['Oops! Something went wrong when trying to locate the relevant project. 106']
		else: 
			project = False
			errors['error'] = True
			errors['project'] = ['Please select the project.']
	else:
		p = False
		project = False
		errors['error'] = True
		errors['project'] = ['Oops! Something went wrong and project data is missing. Please re-enter the task create/edit page. 119']
	
	#checking validity of staff data
	if request.POST['staff']:
		try: s = int(request.POST['staff'])
		except ValueError:
			s = False
			errors['error'] = True
			errors['staff'] = ['Oops! Something went wrong and staff data was not a number. Please re-enter the task create/edit page. 107']
		except:
			s = False
			errors['error'] = True
			errors['staff'] = ['Oops! Something went wrong and staff data was not a number. Please re-enter the task create/edit page. 108']
		if s:
			try: staff = Staff.objects.get(id = s)
			except (KeyError, Staff.DoesNotExist):
				staff = False
				errors['error'] = True
				errors['staff'] = ['The staff to which you would like to assign the task does not exist.']
			except:
				staff = False
				errors['error'] = True
				errors['staff'] = ['Oops! Something went wrong when trying to locate the relevant staff. 109']
		else: 
			staff = False
			errors['error'] = True
			errors['staff'] = ['Please select the staff.']
	else:
		s = False
		staff = False
		errors['error'] = True
		errors['staff'] = ['Oops! Something went wrong and staff data is missing. Please re-enter the task create/edit page. 120']

	#checking validity of start date
	if request.POST['start_date_year'] and request.POST['start_date_month'] and request.POST['start_date_day']: 
		start_date = {'day': False, 'month': False, 'year': False}
		try: start_date['day'] = int(request.POST['start_date_day'])
		except ValueError: 
			start_date['day'] = False
			errors['error'] = True
			if not errors['start_date'] : errors['start_date'] = []
			errors['start_date'].append('Start date day data is not a number')
		except:
			start_date['day'] = False
			errors['error'] = True
			if not errors['start_date'] : errors['start_date'] = []
			errors['start_date'].append('Start date day data could not be converted to integer')
		if start_date['day'] and (start_date['day'] > 31 or start_date['day'] < 1):
			start_date['day'] = False
			errors['error'] = True
			if not errors['start_date'] : errors['start_date'] = []
			errors['start_date'].append('Start date day must be in the range between 1 and 31 inclusive')

		try: start_date['month'] = int(request.POST['start_date_month'])
		except ValueError: 
			start_date['month'] = False
			errors['error'] = True
			if not errors['start_date'] : errors['start_date'] = []
			errors['start_date'].append('Start date month data is not a number')
		except:
			start_date['month'] = False
			errors['error'] = True
			if not errors['start_date'] : errors['start_date'] = []
			errors['start_date'].append('Start date month data could not be converted to integer')
		if start_date['month'] and (start_date['month'] > 12 or start_date['month'] < 1):
			start_date['month'] = False
			errors['error'] = True
			if not errors['start_date'] : errors['start_date'] = []
			errors['start_date'].append('Start date month must be in the range between 1 and 12 inclusive')

		try: start_date['year'] = int(request.POST['start_date_year'])
		except ValueError: 
			start_date['year'] = False
			errors['error'] = True
			if not errors['start_date'] : errors['start_date'] = []
			errors['start_date'].append('Start date year data is not a number')
		except:
			start_date['year'] = False
			errors['error'] = True
			if not errors['start_date'] : errors['start_date'] = []
			errors['start_date'].append('Start date year data could not be converted to integer')
		if start_date['year'] and (datetime.date.today().year - start_date['year'] > 1):
			start_date['year'] = False
			errors['error'] = True
			if not errors['start_date'] : errors['start_date'] = []
			errors['start_date'].append('Start date year can be at most 1 year behind today')

		if start_date['year'] and start_date['month'] and start_date['day'] and start_date['day'] > calendar.monthrange(start_date['year'], start_date['month'])[1]:
			start_date['day'] = False
			errors['error'] = True
			if not errors['start_date'] : errors['start_date'] = []
			errors['start_date'].append('Start date day is out of range for given month and year, max number of days is: ' + str(calendar.monthrange(start_date['year'], start_date['month'])[1]))

		if start_date['year'] and start_date['month'] and start_date['day'] and errors['start_date'] == False:
			try: S_date = datetime.date(start_date['year'], start_date['month'], start_date['day'])
			except: 
				S_date = False
				errors['error'] = True
				if not errors['start_date'] : errors['start_date'] = []
				errors['start_date'].append('Oops! Something went wrong. Unable to create start date from data provided. Please try again. 114')
		else: S_date = False
	else:
		S_date = False
		errors['error'] = True
		if not errors['start_date'] : errors['start_date'] = []
		errors['start_date'].append('Oops! Something went wrong and some of start date data is missing. Please re-enter the task create/edit page. 121')


	#checking validity of end date
	if request.POST['end_date_year'] and request.POST['end_date_month'] and request.POST['end_date_day']: 
		end_date = {'day': False, 'month': False, 'year': False}
		try: end_date['day'] = int(request.POST['end_date_day'])
		except ValueError: 
			end_date['day'] = False
			errors['error'] = True
			if not errors['end_date'] : errors['end_date'] = []
			errors['end_date'].append('End date day data is not a number')
		except:
			end_date['day'] = False
			errors['error'] = True
			if not errors['end_date'] : errors['end_date'] = []
			errors['end_date'].append('End date day data could not be converted to integer')
		if end_date['day'] and (end_date['day'] > 31 or end_date['day'] < 1):
			end_date['day'] = False
			errors['error'] = True
			if not errors['end_date'] : errors['end_date'] = []
			errors['end_date'].append('End date day must be in the range between 1 and 31 inclusive')

		try: end_date['month'] = int(request.POST['end_date_month'])
		except ValueError: 
			end_date['month'] = False
			errors['error'] = True
			if not errors['end_date'] : errors['end_date'] = []
			errors['end_date'].append('End date month data is not a number')
		except:
			end_date['month'] = False
			errors['error'] = True
			if not errors['end_date'] : errors['end_date'] = []
			errors['end_date'].append('End date month data could not be converted to integer')
		if end_date['month'] and (end_date['month'] > 12 or end_date['month'] < 1):
			end_date['month'] = False
			errors['error'] = True
			if not errors['end_date'] : errors['end_date'] = []
			errors['end_date'].append('End date month must be in the range between 1 and 12 inclusive')

		try: end_date['year'] = int(request.POST['end_date_year'])
		except ValueError: 
			end_date['year'] = False
			errors['error'] = True
			if not errors['end_date'] : errors['end_date'] = []
			errors['end_date'].append('End date year data is not a number')
		except:
			end_date['year'] = False
			errors['error'] = True
			if not errors['end_date'] : errors['end_date'] = []
			errors['end_date'].append('End date year data could not be converted to integer')
		if end_date['year'] and (datetime.date.today().year - end_date['year'] > 1):
			end_date['year'] = False
			errors['error'] = True
			if not errors['end_date'] : errors['end_date'] = []
			errors['end_date'].append('End date year can be at most 1 year behind today')

		if end_date['year'] and end_date['month'] and end_date['day'] and end_date['day'] > calendar.monthrange(end_date['year'], end_date['month'])[1]:
			end_date['day'] = False
			errors['error'] = True
			if not errors['end_date'] : errors['end_date'] = []
			errors['end_date'].append('End date day is out of range for given month and year, max number of days is: ' + str(calendar.monthrange(end_date['year'], end_date['month'])[1]))

		if end_date['year'] and end_date['month'] and end_date['day'] and errors['end_date'] == False:
			try: E_date = datetime.date(end_date['year'], end_date['month'], end_date['day'])
			except: 
				E_date = False
				errors['error'] = True
				if not errors['end_date'] : errors['end_date'] = []
				errors['end_date'].append('Oops! Something went wrong. Unable to create end date from data provided. Please try again. 115')
		else: E_date = False

		if E_date and S_date and E_date < S_date:
			E_date = False
			end_date = {'day': False, 'month': False, 'year': False}
			errors['error'] = True
			if not errors['end_date'] : errors['end_date'] = []
			errors['end_date'].append('End date must be greater or equal to start date')
	else:
		E_date = False
		errors['error'] = True
		if not errors['end_date'] : errors['end_date'] = []
		errors['end_date'].append('Oops! Something went wrong and some of start date data is missing. Please re-enter the task create/edit page. 122')

	#checking timestamp value validity
	if task:
		if request.POST['timestamp']:
			try: time = float(request.POST['timestamp'])
			except:
				time = False
				errors['error'] = True
				errors['timestamp'] = ['Oops! Something went wrong with timing of request. Please re-enter the page. 110']
		else:
			time = False
			errors['error'] = True
			errors['timestamp'] = ['Oops! Something went wrong and timing of requst data is missing. Please re-enter the page. 123']
	
	if not errors['error']:
		if i == 0:
			try: 
				task = Task.objects.create(name = name, staff_id = staff.id, project_id = project.id , start_date = S_date, end_date = E_date, comment = comment)
				return HttpResponseRedirect(reverse('plan:task', args=(task.id, 0)))
			except:
				task = False
				errors['error'] = True
				errors['database'] = ['Oops! Something went wrong. New task was not created, please reload and try again. 111']
		elif type(task) == Task:
			try:
				if time > task.update.timestamp():
					task.name = name
					task.project_id = project.id
					task.staff_id = staff.id
					task.start_date = S_date
					task.end_date = E_date
					task.comment = comment
					task.update = timezone.now()
					task.save()
					return HttpResponseRedirect(reverse('plan:task', args=(task.id, 0)))
				else:
					task = False
					errors['error'] = True
					errors['timestamp'] = ['The task has been updated while you were updating it. Your data was not saved.']
			except:
				print("Unexpected error:", sys.exc_info()[0])
				task = False
				errors['error'] = True
				errors['database'] = ['Oops! Something went wrong when trying to update the task. 113']
	
	if errors['error']:
		selected = {'project': False, 'staff': False, 'project_lines_new': False, 'staff_lines_new': False,'name': False, 'comment': False, 'task': False,'start_date': False, 'end_date': False,}
		
		if not errors['project'] and project: selected['project'] = project
		elif not project and task: selected['project'] = task.project

		if not errors['staff'] and staff: selected['staff'] = staff
		elif not staff and task: selected['staff'] = task.staff

		if selected['project']:
			selected['project_lines_new'] = calendar_context(start = 'this_week', days_in_line = 35, num_lines = 2, obj = False, obj_id = False, group = 'department', row = 'staff', show_empty = True, project = selected['project'].id)
		if selected['staff']:
			selected['staff_lines_new'] = calendar_context(start = 'this_week', days_in_line = 35, num_lines = 2, obj = selected['staff'], obj_id = int(selected['staff'].id), group = 'stream', row = 'project', show_empty = True)

		if not errors['name'] and name: selected['name'] = name
		elif not name and task: selected['name'] = task.name

		if not errors['comment'] and comment: selected['comment'] = comment
		elif not comment and task: selected['comment'] = task.comment

		if not errors['database'] and task: selected['task'] = task

		if S_date and not errors['start_date']: selected['start_date'] = S_date
		else:
			selected['start_date'] = start_date
			if not start_date['day'] and task: selected['start_date']['day'] = task.start_date.day
			if not start_date['month'] and task: selected['start_date']['month'] = task.start_date.month
			if not start_date['year'] and task: selected['start_date']['year'] = task.start_date.year

		if E_date and not errors['end_date']: selected['end_date'] = E_date
		else:
			selected['end_date'] = end_date
			if not end_date['day'] and task: selected['end_date']['day'] = task.end_date.day
			if not end_date['month'] and task: selected['end_date']['month'] = task.end_date.month
			if not end_date['year'] and task: selected['end_date']['year'] = task.end_date.year

		errors_names = {'name': 'Title', 'comment': 'Comment', 'start_date': 'Start Date', 'end_date': 'End Date', 'project': 'Project', 'staff': 'Staff', 'edit': 'Edit/Create', 'timestamp': 'Request Timing', 'database': 'Database'}
		keys = list(errors.keys())
		keys.remove('error')
		errors['texts'] = []
		for k in keys:
			errors['texts'].append({'location': errors_names[k],'text': errors[k]})

		context = {'project_list' : Stream.objects.all(), 
				'staff_list' : Department.objects.all(),
				'project_select' : Project.objects.filter(active=True), 
				'staff_select' : Staff.objects.filter(active=True), 
				'date': get_date_selection(), 
				'selected': selected, 
				'edit': i, 
				'timestamp': timezone.now().timestamp(), 
				'cal_setting': 'this_week',
				'today': datetime.date.today(),
				'errors': errors,
				}
		return render(request, 'plan/create_task.html', context)


def delete_task(request):
	i = int(request.POST['edit'])
	d = int(request.POST['delete'])
	name = request.POST['name']
	time = float(request.POST['timestamp'])
	if i == d and d > 0:
		try:
			t = Task.objects.get(pk=d)
		except (KeyError, Task.DoesNotExist):
			return HttpResponse("Failed to find task '%s'! Try again." % name)
		else:
			if time > t.update.timestamp():
				p = t.project_id
				t.delete()
				return HttpResponseRedirect(reverse('plan:project', args=(p, 0)))
			else:
				return HttpResponseRedirect(reverse('plan:task', args=(d, 1)))
	else:
		return HttpResponse("Something went wrong during update to '%s'! Try again." % name)

def calendar_page(request):
	context = {'today': datetime.date.today(), 
				'alt_cal': calendar_context(start = 'all', days_in_line = 35, num_lines = False, obj = False, obj_id = False, group = 'department', row = 'staff', show_empty = True), 
				'staff_list' : Department.objects.all(), 
				'project_list': Stream.objects.all(), 
				}
	return render(request, 'plan/calendar.html', context)

def calendar_project(request, project_id):
	try:
		project = Project.objects.get(pk=project_id)
	except (KeyError, Project.DoesNotExist):
		project = False
		return HttpResponse("Failed to find project with ID'%s'! Try again." % project_id)
	context = {'today': datetime.date.today(), 
				'alt_cal': calendar_context(start = 'all', days_in_line = 35, num_lines = False, obj = project, obj_id = int(project_id), group = 'department', row = 'staff', show_empty = True, project = project.id), 
				'staff_list' : Department.objects.all(), 
				'project_list': Stream.objects.all(), 
				'project': project,
				}
	return render(request, 'plan/calendar.html', context)

def calendar_staff(request, staff_id):
	staff = Staff.objects.get(pk = staff_id)
	context = {'today': datetime.date.today(), 
				'alt_cal': calendar_context(start = 'all', days_in_line = 35, num_lines = False, obj = staff, obj_id = int(staff_id), group = 'stream', row = 'project', show_empty = True),
				'staff_list' : Department.objects.all(), 
				'project_list': Stream.objects.all(), 
				'staff': staff,
				}
	return render(request, 'plan/calendar.html', context)

		
