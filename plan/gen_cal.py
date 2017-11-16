import datetime
import math
import calendar
from django.db.models import Count
from .models import Staff, Department, Project, Task, Stream

class SetCal:
	def __init__(self, t = datetime.date.today()):
		self.settings = ['this_week', 'this_month', 'last_month', 'all']
		today = t
		d = datetime.timedelta(days=1)
		self.day = d
		self.set_dates = [today - d*today.weekday(), today.replace(day=1) - d*today.replace(day=1).weekday(), today.replace(day=1, month=today.month-1) - d*today.replace(day=1, month=today.month-1).weekday(), False]

	def start(self, i):
		if i in self.settings:
			s = i
		else:
			s = self.settings[0]
		return self.set_dates[self.settings.index(s)]

	def day(self):
		return self.day

	def today(self):
		return datetime.date.today()

class Dates:
	def __init__(self, s, e):
		self.start = s
		self.end = e

		self.period_start = s - datetime.timedelta(days=s.weekday())
		self.period_end = e + datetime.timedelta(days=6 - e.weekday())

		day_delta = datetime.timedelta(days=1)

		self.lines = int(math.ceil((self.period_end - self.period_start + day_delta) / datetime.timedelta(days=35)))


	def dates(self, line=0):
		dates =[]
		
		if line != 0:
			s = self.period_start + datetime.timedelta(days= 35 * (line-1))
			period_end = s + datetime.timedelta(days=34)
		else:
			s = self.period_start
			period_end = self.period_end

		d = datetime.timedelta(days=1)

		while s <= period_end:
			dates.append(s)
			s = s + d
		
		return dates

	def days(self, line=0):
		days =[]
		d_symbol = ["M", "T", "W", "T", "F", "S", "S"]
		
		if line != 0:
			s = self.period_start + datetime.timedelta(days= 35 * (line-1))
			period_end = s + datetime.timedelta(days=34)
		else:
			s = self.period_start
			period_end = self.period_end

		d = datetime.timedelta(days=1)

		while s <= period_end:
			days.append(d_symbol[s.weekday()])
			s = s + d
		
		return days

	def line_end(self, line=0):
		if line != 0:
			s = self.period_start + datetime.timedelta(days= 35 * (line-1))
			period_end = s + datetime.timedelta(days=34)
		else:
			s = self.period_start
			period_end = self.period_end

		return period_end

	def line_start(self, line=0):
		if line != 0:
			s = self.period_start + datetime.timedelta(days= 35 * (line-1))
		else:
			s = self.period_start

		return s

	def week_days(self, days=7):
		dates = []
		d = datetime.timedelta(days=1)

		dates.append(self.period_start)
		for i in range(1, days):
			dates.append(self.period_start + i * d)

		return dates

	def month(self, days=7):
		if type(days) != int or days < 5: days = 7
		d = datetime.timedelta(days=1)
		end = self.period_start + (days - 1) * d
		months = []

		num_years = end.year - self.period_start.year

		if self.period_start.month == end.month:
			months.append({'date': self.period_start, 'num_days': days})

		elif self.period_start.month != end.month and self.period_start < end:
			if num_years == 0 :
				num_months = end.month - self.period_start.month + 1
			elif num_years > 0 :
				num_months = (12 - self.period_start.month + 1) + end.month + 12 * (num_years - 1)

			for m in range(0, num_months): 
				if m == 0:
					if self.period_start.month + 1 > 12 :
						num_days = int((self.period_start.replace(month = 1, year = self.period_start.year + 1, day = 1) - self.period_start) / d)
					else:
						num_days = int((self.period_start.replace(month = self.period_start.month + 1, day = 1) - self.period_start) / d)
					months.append({'date': self.period_start, 'num_days': num_days})
				elif m == num_months - 1:
					months.append({'date': end, 'num_days': end.day})
				else: 
					mon = (self.period_start.month + m) % 12
					year = math.floor((self.period_start.month + m) / 12) + self.period_start.year
					if mon == 0: 
						mon = 12
						year = year - 1
					months.append({'date': datetime.date(year=year, month = mon, day= 1), 'num_days': calendar.monthrange(year, mon)[1]})

		return months

def get_project(id):
	return Project.objects.get(pk=id)

def project_task_dates():
	pro = Project.objects.all()

	for p in pro:
		p.task_start_date = p.task_set.order_by('start_date')[0].start_date
		p.task_end_date = p.task_set.order_by('-end_date')[0].end_date
		p.save()

def get_projects(stream=False, current=False, date=False, active=True, tasks=False, sort='start', group=False):
	#tasks - projects that have at least 1 task + 
	#stream - projects are filtered by stream ID + 
	#date - filter projects whose end date is past or equal to date +
	#current - that are currently active + 
	#sort - how project to be sorted: start, end 
	#group - whether to group projects by stream or not
	project_task_dates()

	today = datetime.date.today()

	data = Project.objects.filter(active=active)

	#applying tasks filter
	if tasks:
		data = data.annotate(num_tasks=Count('task')).filter(num_tasks__gt = 0)

	#applying stream filter if it exists
	if stream:
		try:
			s = Stream.objects.get(id=stream)
			data = data.filter(stream_id = stream)
		except (KeyError):
			print ('Stream ID error while filtering projects in get_projects function')
	
	#applying current filter, that is only those projects that are currently active
	if current:
		s = SetCal(datetime.date.today())
		if current == 'this_week':
			data = data.filter(task_end_date__gte = s.start('this_week')).filter(task_start_date__lte = (s.start('this_week') + 6 * datetime.timedelta(days=1)))
			print (s.start('this_week'), s.start('this_week') + 6 * datetime.timedelta(days=1))
		elif current == 'next_week': 
			data = data.filter(task_start_date__gte = (s.start('this_week') + 7 * datetime.timedelta(days=1))).filter(task_start_date__lte = (s.start('this_week') + 13 * datetime.timedelta(days=1)))

	#applying date filter, that is only those projects which end after the date
	if date:
		if type(date) == datetime.date:
			data = data.filter(task_end_date__gte = date)
		else: print('date parameter of wrong type: ', type(date), 'should be datetime.date')

	#sorting
	if sort == 'start':
		data = data.order_by('task_start_date')
	elif sort == 'end':
		data = data.order_by('-task_end_date')

	#applying grouping
	if group:
		d = []
		strms = Stream.objects.all()
		for s in strms:
			d.append({'stream': s, 'projects': data.filter(stream_id = s.id)})
		data = d

	return data

def get_tasks(stream=False, current=False, deadline=False, active=True, sort='start', group=False, project = False, staff = False):
	project_task_dates()
	today = datetime.date.today()

	data = Task.objects.filter(active=active)

	#applying stream filter if it exists
	if stream:
		try:
			s = Stream.objects.get(id=stream)
			data = data.filter(project__stream_id = stream)
		except (KeyError):
			print ('Stream ID error while filtering projects in get_projects function')

	#applying project filter if it exists
	if project:
		try:
			s = Project.objects.get(id=project)
			data = data.filter(project_id = project)
		except (KeyError):
			print ('Stream ID error while filtering projects in get_projects function')

	#applying project filter if it exists
	if staff:
		try:
			s = Staff.objects.get(id=staff)
			data = data.filter(staff_id = staff)
		except (KeyError):
			print ('Stream ID error while filtering projects in get_projects function')

	#applying current filter, that is only those projects that are currently active
	if current:
		s = SetCal(datetime.date.today())
		if current == 'this_week':
			data = data.filter(end_date__gte = s.start('this_week')).filter(start_date__lte = (s.start('this_week') + 6 * datetime.timedelta(days=1)))
		elif current == 'next_week': 
			data = data.filter(start_date__gte = (s.start('this_week') + 7 * datetime.timedelta(days=1))).filter(start_date__lte = (s.start('this_week') + 13 * datetime.timedelta(days=1)))

	#dealine filter
	if deadline:
		s = SetCal(datetime.date.today())
		data = data.filter(end_date__gte = s.start('this_week')).filter(end_date__lte = (s.start('this_week') + 13 * datetime.timedelta(days=1)))

	#sorting
	if sort == 'start':
		data = data.order_by('start_date')
	elif sort == 'end':
		data = data.order_by('end_date')

	#applying grouping
	if group:
		d = []
		strms = Stream.objects.all()
		for s in strms:
			d.append({'stream': s, 'tasks': data.filter(project__stream_id = s.id)})
		data = d

	return data

def get_staff(active=True, group=False, project = False, staff = False):
	data = Staff.objects.filter(active=active)

	#applying project filter if it exists
	if project:
		try:
			s = Project.objects.get(id=project)
			data = data.filter(task__project_id = project)
		except (KeyError):
			print ('Stream ID error while filtering projects in get_projects function')

	#applying project filter if it exists
	if staff:
		try:
			s = Staff.objects.get(id=staff)
			data = data.filter(staff_id = staff)
		except (KeyError):
			print ('Stream ID error while filtering projects in get_projects function')

	#applying grouping filter
	if group:
		d = []
		deps = Department.objects.all()
		for dep in deps:
			dd = data.filter(dep_id = dep.id)
			if len(dd) > 0 :
				d.append({'department': dep, 'staff': dd})
		data = d

	return data

holidays = [
			[datetime.date(2017, 1, 1), 0, True], [datetime.date(2017, 1, 8), 0, False],
			[datetime.date(2017, 1, 14), 0, True], [datetime.date(2017, 1, 15), 0, False],
			[datetime.date(2017, 1, 21), 0, True], [datetime.date(2017, 1, 22), 0, False],
			[datetime.date(2017, 1, 28), 0, True], [datetime.date(2017, 1, 29), 0, False],
			[datetime.date(2017, 2, 4), 0, True], [datetime.date(2017, 2, 5), 0, False],
			[datetime.date(2017, 2, 11), 0, True], [datetime.date(2017, 2, 12), 0, False],
			[datetime.date(2017, 2, 18), 0, True], [datetime.date(2017, 2, 19), 0, False],
			[datetime.date(2017, 2, 23), 0, True], [datetime.date(2017, 2, 26), 0, False],
			[datetime.date(2017, 3, 4), 0, True], [datetime.date(2017, 3, 5), 0, False],
			#[datetime.date(2017, 3, 8), 0, True], [datetime.date(2017, 3, 8), 0, False],
			[datetime.date(2017, 3, 11), 0, True], [datetime.date(2017, 3, 12), 0, False],
			[datetime.date(2017, 3, 18), 0, True], [datetime.date(2017, 3, 19), 0, False],
			[datetime.date(2017, 3, 25), 0, True], [datetime.date(2017, 3, 26), 0, False],
			[datetime.date(2017, 4, 1), 0, True], [datetime.date(2017, 4, 2), 0, False],
			[datetime.date(2017, 4, 8), 0, True], [datetime.date(2017, 4, 9), 0, False],
			[datetime.date(2017, 4, 15), 0, True], [datetime.date(2017, 4, 16), 0, False],
			[datetime.date(2017, 4, 22), 0, True], [datetime.date(2017, 4, 23), 0, False],
			[datetime.date(2017, 4, 29), 0, True], [datetime.date(2017, 5, 1), 0, False],
			[datetime.date(2017, 5, 6), 0, True], [datetime.date(2017, 5, 9), 0, False],
			[datetime.date(2017, 5, 13), 0, True], [datetime.date(2017, 5, 14), 0, False],
			[datetime.date(2017, 5, 20), 0, True], [datetime.date(2017, 5, 21), 0, False],
			[datetime.date(2017, 5, 27), 0, True], [datetime.date(2017, 5, 28), 0, False],
			[datetime.date(2017, 6, 3), 0, True], [datetime.date(2017, 6, 4), 0, False],
			[datetime.date(2017, 6, 10), 0, True], [datetime.date(2017, 6, 12), 0, False],
			[datetime.date(2017, 6, 17), 0, True], [datetime.date(2017, 6, 18), 0, False],
			[datetime.date(2017, 6, 24), 0, True], [datetime.date(2017, 6, 25), 0, False],
			[datetime.date(2017, 7, 1), 0, True], [datetime.date(2017, 7, 2), 0, False],
			[datetime.date(2017, 7, 8), 0, True], [datetime.date(2017, 7, 9), 0, False],
			[datetime.date(2017, 7, 15), 0, True], [datetime.date(2017, 7, 16), 0, False],
			[datetime.date(2017, 7, 22), 0, True], [datetime.date(2017, 7, 23), 0, False],
			[datetime.date(2017, 7, 29), 0, True], [datetime.date(2017, 7, 30), 0, False],
			[datetime.date(2017, 8, 5), 0, True], [datetime.date(2017, 8, 6), 0, False],
			[datetime.date(2017, 8, 12), 0, True], [datetime.date(2017, 8, 13), 0, False],
			[datetime.date(2017, 8, 19), 0, True], [datetime.date(2017, 8, 20), 0, False],
			[datetime.date(2017, 8, 26), 0, True], [datetime.date(2017, 8, 27), 0, False],
			[datetime.date(2017, 9, 2), 0, True], [datetime.date(2017, 9, 3), 0, False],
			[datetime.date(2017, 9, 9), 0, True], [datetime.date(2017, 9, 10), 0, False],
			[datetime.date(2017, 9, 16), 0, True], [datetime.date(2017, 9, 17), 0, False],
			[datetime.date(2017, 9, 23), 0, True], [datetime.date(2017, 9, 24), 0, False],
			[datetime.date(2017, 9, 30), 0, True], [datetime.date(2017, 10, 1), 0, False],
			[datetime.date(2017, 10, 7), 0, True], [datetime.date(2017, 10, 8), 0, False],
			[datetime.date(2017, 10, 14), 0, True], [datetime.date(2017, 10, 15), 0, False],
			[datetime.date(2017, 10, 21), 0, True], [datetime.date(2017, 10, 22), 0, False],
			[datetime.date(2017, 10, 28), 0, True], [datetime.date(2017, 10, 29), 0, False],
			[datetime.date(2017, 11, 4), 0, True], [datetime.date(2017, 11, 6), 0, False],
			[datetime.date(2017, 11, 11), 0, True], [datetime.date(2017, 11, 12), 0, False],
			[datetime.date(2017, 11, 18), 0, True], [datetime.date(2017, 11, 19), 0, False],
			[datetime.date(2017, 11, 25), 0, True], [datetime.date(2017, 11, 26), 0, False],
			[datetime.date(2017, 12, 2), 0, True], [datetime.date(2017, 12, 3), 0, False],
			[datetime.date(2017, 12, 9), 0, True], [datetime.date(2017, 12, 10), 0, False],
			[datetime.date(2017, 12, 16), 0, True], [datetime.date(2017, 12, 17), 0, False],
			[datetime.date(2017, 12, 23), 0, True], [datetime.date(2017, 12, 24), 0, False],
			[datetime.date(2017, 12, 30), 0, True], [datetime.date(2017, 12, 31), 0, False],
			[datetime.date(2018, 1, 1), 0, True], [datetime.date(2018, 1, 8), 0, False],
			[datetime.date(2018, 1, 13), 0, True], [datetime.date(2018, 1, 14), 0, False],
			[datetime.date(2018, 1, 20), 0, True], [datetime.date(2018, 1, 21), 0, False],
			[datetime.date(2018, 1, 27), 0, True], [datetime.date(2018, 1, 28), 0, False],
			[datetime.date(2018, 2, 3), 0, True], [datetime.date(2018, 2, 4), 0, False],
			[datetime.date(2018, 2, 10), 0, True], [datetime.date(2018, 2, 11), 0, False],
			[datetime.date(2018, 2, 17), 0, True], [datetime.date(2018, 2, 18), 0, False],
			[datetime.date(2018, 2, 23), 0, True], [datetime.date(2018, 2, 25), 0, False],
			[datetime.date(2018, 3, 3), 0, True], [datetime.date(2018, 3, 4), 0, False],
			[datetime.date(2018, 3, 9), 0, True], [datetime.date(2018, 3, 11), 0, False],
			[datetime.date(2018, 3, 17), 0, True], [datetime.date(2018, 3, 18), 0, False],
			[datetime.date(2018, 3, 23), 0, True], [datetime.date(2018, 3, 25), 0, False],
			]


class ProjectDates:
	def __init__(self, i):
		self.project = i
		self.id = self.project.id
		self.name = self.project.name
		if len(self.project.task_set.all()) > 0:
			self.start_date = self.project.task_set.order_by('start_date')[0].start_date
			self.end_date = self.project.task_set.order_by('-end_date')[0].end_date
		else:
			self.start_date = 'n/a'
			self.end_date = 'n/a'


class CalendarRow:
	def __init__(self, l):
		self.list = l

	def row(self, id, start, end, type = 'staff'):
		if type == 'staff':
			task_list = self.list.filter(staff_id = id)
		elif type == 'project':
			task_list = self.list.filter(project_id = id)
		s = start
		e = end

		day = datetime.timedelta(days=1)

		p = []
		for t in task_list:
			p.append([t.start_date, t.id, True])
			p.append([t.end_date, t.id, False])

		for h in holidays:
			p.append(h)

		dates = sorted(list(set([[row[i] for row in p] for i in range(3)][0])))

		m = []
		m.append(dates)
		m = [[row[i] for row in m] for i in range(len(dates))]
		for i in m:
			i.append([])
			i.append([])

		for j in p:
			i = dates.index(j[0])
			if j[2]:
				m[i][1].append(j[1])
			elif not j[2]:
				m[i][2].append(j[1])

		final = []
		c_tasks = []
		for i in range(0, len(m)-1):
			if len(m[i][2]) > 0 and len(m[i][1]) == 0:
				for a in m[i][2]:
					c_tasks.remove(a)
				if len(c_tasks) > 0:
					final.append([m[i][0] + day, [], []])
					for a in c_tasks:
						final[len(final)-1][2].append(a)

					if len(m[i+1][1]) > 0:
						if m[i+1][0] - day >= final[len(final)-1][0]:
							final[len(final)-1][1] = m[i+1][0] - day
						else:
							final[len(final)-1][1] = final[len(final)-1][0]
					else:
						final[len(final)-1][1] = m[i+1][0]

			elif len(m[i][1]) > 0:
				final.append([m[i][0], [], []])
				for a in m[i][1]:
					c_tasks.append(a)
				for a in c_tasks:
					final[len(final)-1][2].append(a)

				if len(m[i][2]) > 0:
					final[len(final)-1][1] = m[i][0]
					for a in m[i][2]:
						c_tasks.remove(a)

					if not (m[i+1][0] == m[i][0] + day and len(m[i+1][1]) > 0):
						final.append([m[i][0] + day, [], []])
						for a in c_tasks:
							final[len(final)-1][2].append(a)

						if len(m[i+1][1]) > 0:
							if m[i+1][0] - day >= final[len(final)-1][0]:
								final[len(final)-1][1] = m[i+1][0] - day
							else:
								final[len(final)-1][1] = final[len(final)-1][0]

						else:
							final[len(final)-1][1] = m[i+1][0]

				else:
					if len(m[i+1][1]) > 0:
						if m[i+1][0] - day >= final[len(final)-1][0]:
							final[len(final)-1][1] = m[i+1][0] - day
						else:
							final[len(final)-1][1] = final[len(final)-1][0]

					else:
						final[len(final)-1][1] = m[i+1][0]

		for f in final:
			f.append(int(math.ceil((f[1] - f[0] + day) / day)))

		row = []
		for i in range(0, int(math.ceil((e - s + day) / day))):
			row.append([])
		for f in final:
			i = int((f[0] - s) / day)
			c = int((e - f[1]) / day)
			b = int((e - f[0]) / day)
			if i < 0:
				j = int((f[1] - s) / day)
				if j >= 0 and c >= 0:
					row[0] = {'days': j+1, 'multi': False, 'tasks': [],}
					if 0 not in f[2]:
						if len(f[2]) > 1:
							row[0]['multi'] = len(f[2])
						for t in f[2]:
							row[0]['tasks'].append(task_list.filter(id=t)[0])
					else:
						row[0]['tasks'].append(0)
				elif j >= 0 and c < 0:
					row[0] = {'days': 35, 'multi': False, 'tasks': [],}
					if 0 not in f[2]:
						if len(f[2]) > 1:
							row[0]['multi'] = len(f[2])
						for t in f[2]:
							row[0]['tasks'].append(task_list.filter(id=t)[0])
					else:
						row[0]['tasks'].append(0)
			elif c < 0 and b >= 0:
				row[i] = {'days': f[3] + c, 'multi': False, 'tasks': [],}
				if 0 not in f[2]:
					if len(f[2]) > 1:
						row[i]['multi'] = len(f[2])
					for t in f[2]:
						row[i]['tasks'].append(task_list.filter(id=t)[0])
				else:
					row[i]['tasks'].append(0)
			elif b >= 0:
				row[i] = {'days': f[3], 'multi': False, 'tasks': [],}
				if 0 not in f[2]:
					if len(f[2]) > 1:
						row[i]['multi'] = len(f[2])
					for t in f[2]:
						row[i]['tasks'].append(task_list.filter(id=t)[0])
				else:
					row[i]['tasks'].append(0)

		for i in range(0, len(row)):
			if i < len(row):
				if row[i]:
					if row[i]['days'] > 1:
						del row[i+1:i+row[i]['days']]
			else: break

		return row

def get_project_context(id, staff=False, start=False, week=False):
	setup = {'lines_num' : 0, 'rows': 0, 'row_names': 0, 'lines': [], 'project': 0, 'project_start': 0, 'project_end': 0, 'tasks_list': 0,}
	if id == 0:
		if staff:
			tasks_list = Task.objects.filter(active=1, staff_id = staff)
			if start:
				d = Dates(start, tasks_list.order_by('-end_date')[0].end_date)
			else: 
				d = Dates(tasks_list.order_by('start_date')[0].start_date, tasks_list.order_by('-end_date')[0].end_date)
			setup['lines_num'] = d.lines
		else:
			tasks_list = Task.objects.filter(active=1)
			if start:
				d = Dates(start, tasks_list.order_by('-end_date')[0].end_date)
				setup['lines_num'] = 2
			else:
				d = Dates(tasks_list.order_by('start_date')[0].start_date, tasks_list.order_by('-end_date')[0].end_date)
				setup['lines_num'] = d.lines
	else:
		project = Project.objects.get(pk=id)
		tasks_list = project.task_set.filter(active=1)
		setup['project'] = project
		setup['project_start'] = project.task_set.order_by('start_date')[0].start_date
		setup['project_end'] = project.task_set.order_by('-end_date')[0].end_date

		if start:
			d = Dates(start, setup['project_end'])
		else:
			d = Dates(setup['project_start'], setup['project_end'])
		setup['lines_num'] = d.lines
	
	setup['tasks_list'] = tasks_list

	#ROW NAMES & ROWS
	names = []
	row_IDs = [] 
	if staff:
		for task in tasks_list:
			names.append(task.project.name)
		setup['row_names'] = sorted(list(set(names)))
		for s in setup['row_names']:
			row_IDs.append(Project.objects.get(name=s).id)
		setup['rows'] = (len(setup['row_names'])+2)*22
		names.clear()
		names.append(setup['row_names'])
		names.append(row_IDs)
		setup['row_names'] = [[row[i] for row in names] for i in range(len(row_IDs))]

	else:
		for task in tasks_list:
			names.append(task.staff.name)
		setup['row_names'] = sorted(list(set(names)))
		for s in setup['row_names']:
			row_IDs.append(Staff.objects.get(name=s).id)
		setup['rows'] = (len(setup['row_names'])+2)*22
		setup['row_id'] = row_IDs
		names.clear()
		names.append(setup['row_names'])
		names.append(row_IDs)
		setup['row_names'] = [[row[i] for row in names] for i in range(len(row_IDs))]

	#LINES
	lines = []
	cal = CalendarRow(tasks_list)

	#getting tasks calendar data
	for i in range(0, setup['lines_num']):
		l = {'dates': d.dates(i+1), 'days': d.days(i+1), 'rows': []}
		for s in row_IDs:
			if staff:
				l['rows'].append(cal.row(s, min(l['dates']), max(l['dates']), type='project'))
			else:
				l['rows'].append(cal.row(s, min(l['dates']), max(l['dates'])))
		g = []
		for i in l['dates']:
			g.append([i, i.weekday()])

		l['dates'] = g

		setup['lines'].append(l)

	return setup


def get_project_tasks(id):
	setup = {'days_num' : 0, 'rows': 0, 'row_names': [], 'lines': [], 'project': 0, 'project_start': 0, 'project_end': 0, 'tasks_list': 0,}
	project = Project.objects.get(pk=id)
	tasks = project.task_set.order_by('start_date')
	
	setup['project_start'] = project.task_set.order_by('start_date')[0].start_date
	setup['project_end'] = project.task_set.order_by('-end_date')[0].end_date

	setup['tasks_list'] = tasks
	setup['project'] = project

	d = Dates(setup['project_start'], setup['project_end'])

	setup['rows'] = (len(tasks)+2)*22+30

	for t in tasks:
		setup['row_names'].append({'task_name': t.name, 'task_id': t.id, 'task_staff': t.staff.name, 'task_staff_id': t.staff.id,})

	l = {'dates': d.dates(), 'days': d.days(), 'rows': []}

	for t in tasks:		
		cal = CalendarRow(tasks.filter(id = t.id))
		l['rows'].append(cal.row(id, min(l['dates']), max(l['dates']), type='project'))

	g = []
	for i in l['dates']:
		g.append([i, i.weekday()])

	l['dates'] = g

	setup['lines'].append(l)
	setup['days_num'] = len(g) * 32.41

	return setup

w_len = 31.5
d_len = 4.5
y_len = 1638

def get_project_plan():
	setup = {'days_num' : y_len, 'rows': 0, 'row_names': [], 'range': range(1,53),}

	projects = Project.objects.all()
	setup['rows'] = (len(projects)+2)*22+30

	year_start = datetime.date(2017,1,1)
	d = datetime.timedelta(days=1)
	w = datetime.timedelta(days=7)

	for p in projects:
		if p.task_set.count() > 0:
			s = p.task_set.order_by('start_date')[0].start_date
			e = p.task_set.order_by('-end_date')[0].end_date
			o = round(((s - year_start)/d)*d_len,2) #in pixels
			l = round(((e - s)/d)*d_len,2) #in pixels
			w = round(((e - s)/d)/7.0,1) #number float
		else:
			s = 0
			e = 0
			o = 0
			l = 0
			w = 0
		setup['row_names'].append({'project_name': p.name, 'project_id': p.id, 'start_date': s, 'end_date': e, 'length': l, 'offset': o, 'weeks': w,})

	return setup



def get_date_selection():
	d = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31]
	y = [2017, 2018, 2019]
	m = [{'num': 1, 'str': 'Jan',}, 
	{'num': 2, 'str': 'Feb',},
	{'num': 3, 'str': 'Mar',},
	{'num': 4, 'str': 'Apr',},
	{'num': 5, 'str': 'May',},
	{'num': 6, 'str': 'Jun',},
	{'num': 7, 'str': 'Jul',},
	{'num': 8, 'str': 'Aug',},
	{'num': 9, 'str': 'Sep',},
	{'num': 10, 'str': 'Oct',},
	{'num': 11, 'str': 'Nov',},
	{'num': 12, 'str': 'Dec',},]

	date = {'dates': d, 'months': m, 'years': y}
	return date


def get_week_tasks_context(start = False, day = False, project=False, staff=False, row=False):
	if start and type(start) == datetime.date : s = start
	else : s = datetime.date.today()

	if day and type(day) == int : days = day
	else : days = 7

	context = {'width': 0, 'height': 0, 'header': {'month': [], 'dates': []}, 'calendar': [],}
	d = Dates(s, s)

	context['header']['dates'] = d.week_days(days = days)
	context['header']['month'] = d.month(days = days)

	r_len = 0

	#row is Staff
	if row == False or row == 'staff' :
		staffs = get_staff(group=True, project=project)
		cal = CalendarRow(get_tasks(project=project, staff=staff))

		for dep in staffs:
			calendar = {'section': dep['department'], 'rows': []}
			for s in dep['staff']:
				row = {'object': s, 'entries': []}
				entry = {'fill': False, 'multi': False, 'objects': [], 'num_days': 1,}
				for ent in cal.row(s.id, min(context['header']['dates']), max(context['header']['dates'])):
					if len(ent) > 0:
						entry = {'fill': True, 'multi': ent['multi'], 'objects': ent['tasks'], 'num_days': ent['days'],}
					else:
						entry = {'fill': False, 'multi': False, 'objects': [], 'num_days': 1,}
					row['entries'].append(entry)
				calendar['rows'].append(row)
			r_len += len(calendar['rows'])
			context['calendar'].append(calendar)

	#row is Task
	elif row == 'task' :
		staffs = get_staff(group=True, project=project)
		tasks = get_tasks(project=project, staff=staff)

		for dep in staffs:
			calendar = {'section': dep['department'], 'rows': []}
			for task in tasks.filter(staff__dep = dep['department']):
				cal = CalendarRow(tasks.filter(id=task.id))
				row = {'object': task, 'entries': []}
				entry = {'fill': False, 'multi': False, 'objects': [], 'num_days': 1,}
				for ent in cal.row(task.staff_id, min(context['header']['dates']), max(context['header']['dates'])):
					if len(ent) > 0:
						entry = {'fill': True, 'multi': ent['multi'], 'objects': ent['tasks'], 'num_days': ent['days'],}
					else:
						entry = {'fill': False, 'multi': False, 'objects': [], 'num_days': 1,}
					row['entries'].append(entry)
				calendar['rows'].append(row)
			r_len += len(calendar['rows'])
			context['calendar'].append(calendar)


	context['height'] = 57 + len(context['calendar']) * 22 + r_len * 28
	context['width'] = 31.42 * day

	return context

def get_lines_tasks_context(setting = False, lines = 4, project = False, staff = False, row=False):
	#setting should be in a string form of either 'this_week', 'this_month', 'next_month', 'all'
	context = []
	set_date = SetCal()
	d = datetime.timedelta(days=1)

	if setting in ['this_week', 'this_month', 'last_month', 'all'] : start = set_date.start(setting)
	else : start = set_date.start('this_week')

	if type(lines) != int or lines < 2 : lines = 2

	for l in range(0, lines) :
		context.append(get_week_tasks_context(start = start + l * 35 * d, day = 35, project = project, staff = staff, row = row))

	return context








