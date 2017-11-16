import datetime
import math
import calendar
import numpy as np
from django.db.models import Count
from .models import Staff, Department, Project, Task, Stream, Holiday

#function that sets project start and end dates based on available project tasks
def project_task_dates():
    for p in Project.objects.all():
        if len(Task.objects.filter(project = p)) > 0:
            p.task_start_date = p.task_set.order_by('start_date')[0].start_date
            p.task_end_date = p.task_set.order_by('-end_date')[0].end_date
            p.start_date = p.task_start_date
            p.end_date = p.task_end_date
            p.save()

#function that finds the date of first day of the week given particular day
def week_start(day):
    if type(day) != datetime.date : day = datetime.date.today()
    d = datetime.timedelta(days = 1)
    return day - d * day.weekday()

#function that finds the date of last day of the week given particular day
def week_end(day):
    if type(day) != datetime.date : day = datetime.date.today()
    d = datetime.timedelta(days = 1)
    return day + d * (6 - day.weekday())

#function that finds the date of first day of the first week of the month given particular day
def month_start(day):
    if type(day) != datetime.date : day = datetime.date.today()
    return week_start(day.replace(day = 1))

#function that finds the date of first day of the first week of the previous month given particular day
def last_month_start(day):
    if type(day) != datetime.date : day = datetime.date.today()
    return week_start(day.replace(day = 1, month=day.month - 1))

#function that finds the date of first day of the first week of the previous month given particular day
def year_start(day):
    if type(day) != datetime.date : day = datetime.date.today()
    return week_start(day.replace(day = 1, month = 1))

#class that defines dates and all that is linked with them
class Dates:
    def __init__(self, start = 'this_week', days_in_line = False, num_lines = False, obj = False, obj_id = False):
        today = datetime.date.today()
        today_line = 1
        day_delta = datetime.timedelta(days=1)

        if start not in ['this_week', 'this_month', 'last_month', 'all'] : 
            print('Dates class parameter of start should have either of the following values: this_week, this_month, last_month, all')
            start = 'this_week'

        if type(days_in_line) != int:
            print ('Dates class parameter of days_in_line must be of int class')
            days_in_line = 35
        elif days_in_line <= 7:
            print ('Dates class parameter of days_in_line must be greater or equal to 7')
            days_in_line = 7

        if type(num_lines) != int:
            print ('Dates class parameter of num_lines must be of int class')
            num_lines = 1
        elif num_lines < 1:
            print ('Dates class parameter of num_lines must be greater or equal to 1')
            num_lines = 1
        elif num_lines > 1000:
            print ('Dates class parameter of num_lines must be less or equal to 1000')
            num_lines = 1000

        item = False
        if obj and type(obj) in [Task, Project, Staff] and type(obj_id) == int:
            if type(obj) == Task:
                try:
                    item = Task.objects.get(id=obj_id)
                except (KeyError):
                    print ('Task ID error in Dates class')
                    item = False
            elif type(obj) == Project:
                try:
                    item = Project.objects.get(id=obj_id)
                except (KeyError):
                    print ('Project ID error in Dates class')
                    item = False
            elif type(obj) == Staff:
                try:
                    item = Staff.objects.get(id=obj_id)
                except (KeyError):
                    print ('Staff ID error in Dates class')
                    item = False
        elif obj != False: 
            print ('Dates class parameter of obj must be of either class Task, Project, Staff or bool')
            item = False

        if start == 'this_week':
            self.start = week_start(today)
        elif start == 'this_month':
            self.start = month_start(today)
        elif start == 'last_month':
            self.start = last_month_start(today)
        elif start == 'all':
            if not item :
                self.start = week_start(Task.objects.order_by('start_date')[0].start_date)
                num_lines = int(math.ceil((week_end(Task.objects.order_by('-end_date')[0].end_date) - week_start(Task.objects.order_by('start_date')[0].start_date) + day_delta) / datetime.timedelta(days = days_in_line)))
                today_line = int(math.ceil((today - self.start + day_delta) / datetime.timedelta(days = days_in_line)))
            elif type(item) == Task :
                self.start = week_start(item.start_date)
                num_lines = int(math.ceil((week_end(item.end_date) - week_start(item.start_date) + day_delta) / datetime.timedelta(days = days_in_line)))
            elif type(item) == Project :
                self.start = week_start(item.start())
                num_lines = int(math.ceil((week_end(item.end()) - week_start(item.start()) + day_delta) / datetime.timedelta(days = days_in_line)))
                today_line = int(math.ceil((today - self.start + day_delta) / datetime.timedelta(days = days_in_line)))
            elif type(item) == Staff :
                self.start = week_start(item.task_set.order_by('start_date')[0].start_date)
                num_lines = int(math.ceil((week_end(item.task_set.order_by('-end_date')[0].end_date) - week_start(item.task_set.order_by('start_date')[0].start_date) + day_delta) / datetime.timedelta(days = days_in_line)))
                today_line = int(math.ceil((today - self.start + day_delta) / datetime.timedelta(days = days_in_line)))

        self.days_in_line = days_in_line
        self.num_lines = num_lines
        self.item = item
        self.today_line = today_line
        self.today = today

    def week_days(self, line):
        if type(line) != int or line < 1 : line = 1
        dates = []
        d = datetime.timedelta(days=1)

        line_start = self.start + self.days_in_line * (line - 1) * d

        for i in range(0, self.days_in_line):
            dates.append(line_start + i * d)

        return dates

    def month(self, line):
        if type(line) != int or line < 1 : line = 1
        d = datetime.timedelta(days=1)
        line_start = self.start + self.days_in_line * (line - 1) * d
        line_end = line_start + (self.days_in_line - 1) * d
        months = []

        num_years = line_end.year - line_start.year

        if line_start.month == line_end.month:
            months.append({'date': line_start, 'num_days': self.days_in_line})

        elif line_start.month != line_end.month and line_start < line_end:
            if num_years == 0 :
                num_months = line_end.month - line_start.month + 1
            elif num_years > 0 :
                num_months = (12 - line_start.month + 1) + line_end.month + 12 * (num_years - 1)

            for m in range(0, num_months): 
                if m == 0:
                    if line_start.month + 1 > 12 :
                        num_days = int((line_start.replace(month = 1, year = line_start.year + 1, day = 1) - line_start) / d)
                    else:
                        num_days = int((line_start.replace(month = line_start.month + 1, day = 1) - line_start) / d)
                    months.append({'date': line_start, 'num_days': num_days})
                elif m == num_months - 1:
                    months.append({'date': line_end, 'num_days': line_end.day})
                else: 
                    mon = (line_start.month + m) % 12
                    year = math.floor((line_start.month + m) / 12) + line_start.year
                    if mon == 0: 
                        mon = 12
                        year = year - 1
                    months.append({'date': datetime.date(year=year, month = mon, day= 1), 'num_days': calendar.monthrange(year, mon)[1]})

        return months

#function that creates matrix of zeros of rows equal to number of days in the period and columns equal to number of tasks in question plus holidays plus vacation
def zero_matrix(start, end, tasks):
    return np.zeros((int((end-start) / datetime.timedelta(days=1) + 1),len(tasks)+1), dtype=np.int)

#function that returns list of holiday objects that occur within given timeframe
def get_holidays(start, end):
    return Holiday.objects.filter(date__gte = start).filter(date__lte = end)

#function that can return interable list of indices of when holidays occur from given start and end dates
def weekend_indices(start, end, holidays):
    d = datetime.timedelta(days=1)
    length = int((end - start) / d)
    start_week_day = start.weekday()
    indices = []
    if start_week_day == 5:
        indices.append(0)
        indices.append(1)
    elif start_week_day == 6:
        indices.append(0)
    else:
        indices.append(5 - start_week_day)
        indices.append(6 - start_week_day)
    
    while indices[-1] < length:
        indices.append(indices[-1] + 6)
        indices.append(indices[-1] + 1)

    if indices[-1] > length:
        indices.pop()	

    if len(holidays) > 0:
        for h in holidays:
            if h.holiday: 
                indices.append(int((h.date - start) / d))
            else:
                try:
                    indices.remove(int((h.date - start) / d))
                except: print('was not able to remove index of unusual working day: ', h.date)

    return sorted(list(set(indices)))

#function that populates days of week column with data about vacation days both calendar and extra
def weekdays_matrix(start, end, m):
    for ind in weekend_indices(start, end, get_holidays(start, end)):	
        m.T[0][ind] = 1
    return m

#function that populates task columns with numbers that where first number is index of task + 1 and 2 zeros plus number of index number of zeros  
def taskdays_matrix(start, end, tasks, m):
    d = datetime.timedelta(days=1)
    for ind, task in enumerate(tasks):
        num = int(str(ind+1) + (ind+2)*'0')
        if task.start_date >= start: st = int((task.start_date - start) / d)
        else: st = 0
        if task.end_date <= end: en = int((task.end_date - start) / d + 1)
        else: en = int((end - start) / d + 1)
        m.T[ind+1][st:en] = num
    return m

#function that populates sum columnn by summing task and weekdays & vacation columns
def sum_matrix(m):
    m = np.insert(m, len(m[0]), [sum(x) for x in m], axis = 1)
    return m

#function that returns unique values of sum column
def unique_values(m):
    return set(m.T[len(m[0])-1])

#function that identifies sets of adjacent unique values (groups of tasks)
def group_values(matrix, values):
    groups = []
    for v in values:
        indices = sorted(list(np.argwhere(matrix.T[len(matrix[0])-1] == v).flatten()))
        if indices[-1]-indices[0] + 1 == len(indices):
            groups.append({'value': v, 'days': len(indices), 'start': indices[0]})
        else:
            separates = np.argwhere(np.array([indices[i]-indices[i-1] for i in range(1, len(indices))]) > 1).flatten()
            separates = separates + 1
            separates = np.insert(separates, [0], [0])
            separates = np.insert(separates, [len(separates)], [len(indices)])
            #кол-во групп - длина + 1 -> len(separates)
            #начало каждой группы: в separates у меня индекс индексов новой группы за исключением первой. 
            #days - separates[ind+1] - separates[ind], за исключением первой: separate[0]+1; и последней: len(indices) - (separate[-1] + 1)
            #start - первая группа: indices[0], последняя: indices[separate[-1]+1], другая: indices[separate[ind]+1]
            for g in range(len(separates)-1):
                groups.append({'value': v, 'days': separates[g+1] - separates[g], 'start': indices[separates[g]]})
    groups = sorted(groups, key = lambda groups_entry: groups_entry['start'])
    return groups

#function that parses unique values into tasks data and prepares necessary data format for calendar lines
def parser_for_row_entries(groups, tasks):
    entries = []
    #entry = {'fill': False, 'multi': False, 'objects': [], 'num_days': 1,}
    for g in groups:
        #empty calendar cells
        if g['value'] == 0:
            if g['days'] > 0:
                for d in range(0, g['days']):
                    entries.append({'fill': False, 'multi': False, 'objects': [], 'num_days': 1,})
        #weekend or holiday
        elif divmod(g['value'], 10)[1] == 1:
            entries.append({'fill': True, 'multi': False, 'objects': [0], 'num_days': g['days'],})
        #tasks
        elif len(str(g['value'])) > 2:
            entry = {'fill': True, 'multi': False, 'objects': [], 'num_days': g['days'],}
            for t in reversed(str(g['value'])[:-2]):
                if int(t) > 0:
                    entry['objects'].append(tasks[int(t)-1])
            if len(entry['objects']) > 1:
                entry['multi'] = len(entry['objects'])	
            entries.append(entry)
    return entries

#function that creates all rows within a section of calendar (like department or stream or none), row object either: 'staff', 'task', 'project'
def section_rows(tasks, start, end, obj='staff', show_empty = True, group = False):
    if obj not in ['staff', 'task', 'project'] : obj = 'staff'
    rows = []
    if obj == 'staff':
        if show_empty:
            if group:
                if type(group) == Stream: staffs = Staff.objects.filter(task__project__stream = group).distinct().order_by('name')
                elif type(group) == Department: staffs = Staff.objects.filter(dep = group).order_by('name')
            else : staffs = Staff.objects.all().order_by('name')
        else : staffs = Staff.objects.filter(task__in=tasks).distinct().order_by('name')
        for staff in staffs:
            row = {'object': staff, 'entries': []}	
            matrix = sum_matrix(taskdays_matrix(start, end, tasks.filter(staff = staff), weekdays_matrix(start, end, zero_matrix(start, end, tasks.filter(staff = staff)))))
            row['entries'] = parser_for_row_entries(groups=group_values(matrix=matrix, values=unique_values(matrix)), tasks=tasks.filter(staff = staff))
            rows.append(row)
    elif obj == 'task':
        for task in tasks:
            row = {'object': task, 'entries': []}	
            matrix = sum_matrix(taskdays_matrix(start, end, [task], weekdays_matrix(start, end, zero_matrix(start, end, [task]))))
            row['entries'] = parser_for_row_entries(groups=group_values(matrix=matrix, values=unique_values(matrix)), tasks=[task])
            rows.append(row)
    elif obj == 'project':
        for project in Project.objects.filter(task__in=tasks).distinct().order_by('name'):          
            #for task in tasks.filter(project = project):
            row = {'object': project, 'entries': []}	
            matrix = sum_matrix(taskdays_matrix(start, end, tasks.filter(project = project), weekdays_matrix(start, end, zero_matrix(start, end, tasks.filter(project = project)))))
            row['entries'] = parser_for_row_entries(groups=group_values(matrix=matrix, values=unique_values(matrix)), tasks=tasks.filter(project = project))
            rows.append(row)
    return rows

#function that creates all sections and all respective rows of obejcts for calendar, group either 'department', 'stream' or False and object has to be specified either: 'staff', 'task', 'project'
#show_empty parameter basically tells us whether to show an empty section title in the calendar or not
def sections(group = False, show_empty = True, tasks=False, start=False, end=False, obj='staff'):
    if group not in ['stream', 'department', False]: group = False
    if obj not in ['staff', 'task', 'project'] : obj = 'staff'
    if type(show_empty) != bool: show_empty = True
    cal = []
    if group == 'stream':
        if show_empty : streams = Stream.objects.all()
        else : streams = Stream.objects.filter(project__task__in=tasks).distinct().order_by('id')
        for stream in streams:
            cal.append({'section': stream, 'rows': section_rows(tasks=tasks.filter(project__stream = stream), start=start, end=end, obj=obj, group = stream)})
    elif group == 'department':
        if show_empty : departments = Department.objects.all()
        else : departments = Department.objects.filter(staff__task__in=tasks).distinct().order_by('id') 
        for dep in departments:
            cal.append({'section': dep, 'rows': section_rows(tasks=tasks.filter(staff__dep = dep), start=start, end=end, obj=obj, group = dep)})
    elif not group:
        cal.append({'section': False, 'rows': section_rows(tasks=tasks, start=start, end=end, obj=obj, group = False)})
    return cal

#так давайте не терять нить. и делать все-таки все по уму, потому , что так не только правильнее, но так и получается гораздо лучше
#итого у меня уже есть функции, которые генерят календарь. у меня нет +1) функции, которая бы фильтровала tasks по датам и по другим параметрам (staff, project, department), 
#+ 2) функции, которая бы выдавала даты календаря, 3) функция, которая бы объединяла все данные в одном месте и выдавала бы их обратно


#function that retreives tasks and filters them by dates & by other inputs
def get_tasks(current = False, start = False, end = False, start_in = False, end_after = False, deadline = False, staff = False, project = False, task = False, department = False, stream = False,  active = True, sort = 'start'):
    today = datetime.date.today()
    #retreiving tasks && applying 'active' filter if parameter is wrong default to True
    if type(active) == bool : data = Task.objects.filter(active=active)
    else : data = Task.objects.filter(active=True)

    #applying current filter, that is only those projects that are active today
    if current and not start and not end:
        data = data.filter(end_date__gte = today).filter(start_date__lte = today)

    #applying start_in filter, that is finding tasks that start in a particular period of time given by dates
    if start_in and not start and not end:
        if type(start_in['start']) == datetime.date and type(start_in['end']) == datetime.date :
            data = data.filter(start_date__gte = start_in['start']).filter(start_date__lte = start_in['end'])
        else: print('start_in parameters must be of datetime.date type')

    #applying start & end filter
    if type(start) == datetime.date and type(end) == datetime.date :
        if end >= start :
            data = data.filter(end_date__gte = start).filter(start_date__lte = end)
        else: print('End date must be after Start date')

    #applying end_after filter -> projects that end after particular date
    if type(end_after) == datetime.date :
        data = data.filter(end_date__gte = end_after)

    #deadline filter: what tasks finish 10 days from deadline date
    if type(deadline) == datetime.date and not current and not start and not end:
        data = data.filter(end_date__gte = deadline).filter(end_date__lte = deadline + 10 * datetime.timedelta(days=1))

    #applying stream filter if it exists
    if stream and type(stream) == int:
        try:
            s = Stream.objects.get(id=stream)
            data = data.filter(project__stream_id = stream).distinct()
        except (KeyError):
            print ('Stream ID error in get_tasks function')

    #applying project filter if it exists
    if project and type(project) == int:
        try:
            s = Project.objects.get(id=project)
            data = data.filter(project_id = project)
        except (KeyError):
            print ('Project ID error in get_tasks function')

    #applying staff filter if it exists
    if staff and type(staff) == int:
        try:
            s = Staff.objects.get(id=staff)
            data = data.filter(staff_id = staff)
        except (KeyError):
            print ('Staff ID error in get_tasks function')

    #applying department filter if it exists
    if department and type(department) == int:
        try:
            s = Department.objects.get(id=department)
            data = data.filter(staff__dep_id = department).distinct()
        except (KeyError):
            print ('Department ID error in get_tasks function')

    #applying task filter if it exists
    if task and type(task) == int:
        try:
            s = Task.objects.get(id=task)
            data = data.filter(id = task)
        except (KeyError):
            print ('Task ID error in get_tasks function')

    #sorting
    if sort == 'start':
        data = data.order_by('start_date')
    elif sort == 'end':
        data = data.order_by('end_date')

    return data

# function that collects necessary data for task calendars of varipous length and filters
def calendar_context(start = 'this_week', days_in_line = False, num_lines = False, obj = False, obj_id = False, group = False, row = 'staff', show_empty = True, project = False, staff = False):
    context = []
    dates = Dates(start = start, days_in_line = days_in_line, num_lines = num_lines, obj = obj, obj_id = obj_id)
    for l in range(1, dates.num_lines + 1):
        line = {'header': {'month': 0, 'dates': 0}, 'dimensions': {'height': 0, 'width': 0, 'today_line': dates.today_line}, 'calendar': 0}
        line['header']['month'] = dates.month(l)
        line['header']['dates'] = dates.week_days(l)
        if not dates.item:
            tasks = get_tasks(start = dates.week_days(l)[0], end = dates.week_days(l)[-1], staff = False, project = project, task = False)
        else:
            if type(dates.item) == Staff:
                tasks = get_tasks(start = dates.week_days(l)[0], end = dates.week_days(l)[-1], staff = dates.item.id, project = project, task = False)
            elif type(dates.item) == Project:
                tasks = get_tasks(start = dates.week_days(l)[0], end = dates.week_days(l)[-1], staff = False, project = dates.item.id, task = False)
            elif type(dates.item) == Task:
                tasks = get_tasks(start = dates.week_days(l)[0], end = dates.week_days(l)[-1], staff = False, project = False, task = dates.item.id)
        line['calendar'] = sections(group = group, show_empty = show_empty, tasks=tasks, start=dates.week_days(l)[0], end=dates.week_days(l)[-1], obj=row)
        line['dimensions']['width'] = len(line['header']['dates']) * 31.42
        line['dimensions']['height'] = sum([len(x['rows']) for x in line['calendar']]) * 28.0 + len(line['calendar']) * 22.0 + 57.0
        context.append(line)

    return context



#FUNCTIONALITY FOR CREATING HIGH OVERVIEW PROJECTS CALENDAR

#function that retreives project and filters them by dates & by other inputs
def get_projects(current = False, start = False, end = False, start_in = False, end_after = False, deadline = False, staff = False, project = False, task = False, department = False, stream = False,  active = True, sort = 'start'):
    today = datetime.date.today()
    #updating start and end dates of project based on the available tasks
    #project_task_dates()

    #retreiving projects && applying 'active' filter if parameter is wrong default to True
    if type(active) == bool : data = Project.objects.filter(active=active)
    else : data = Project.objects.filter(active=True)

    #applying current filter, that is only those projects that are active today
    if current and not start and not end:
        data = data.filter(end_date__gte = today).filter(start_date__lte = today)

    #applying start_in filter, that is finding projects that start in a particular period of time given by dates
    if start_in and not start and not end:
        if type(start_in['start']) == datetime.date and type(start_in['end']) == datetime.date:
            data = data.filter(start_date__gte = start_in['start']).filter(start_date__lte = start_in['end'])
        else: print('start_in parameters must be of type datetime.date')

    #applying start & end filter
    if type(start) == datetime.date and type(end) == datetime.date :
        if end >= start :
            data = data.filter(end_date__gte = start).filter(start_date__lte = end)
        else: print('End date must be after Start date in get_projects function')

    #applying end_after filter -> projects that end after particular date
    if type(end_after) == datetime.date :
        data = data.filter(end_date__gte = end_after)

    #deadline filter: what projects finish 9 days from deadline date
    if type(deadline) == datetime.date and not current and not start and not end:
        data = data.filter(end_date__gte = deadline).filter(end_date__lte = deadline + 9 * datetime.timedelta(days=1))

    #applying stream filter if it exists
    if stream and type(stream) == int:
        try:
            s = Stream.objects.get(id=stream)
            data = data.filter(stream_id = stream)
        except (KeyError):
            print ('Stream ID error in get_projects function')

    #applying project filter if it exists
    if project and type(project) == int:
        try:
            s = Project.objects.get(id=project)
            data = data.filter(id = project)
        except (KeyError):
            print ('Project ID error in get_projects function')

    #applying staff filter if it exists
    if staff and type(staff) == int:
        try:
            s = Staff.objects.get(id=staff)
            data = data.filter(task__staff_id = staff).distinct()
        except (KeyError):
            print ('Staff ID error in get_projects function')

    #applying department filter if it exists
    if department and type(department) == int:
        try:
            s = Department.objects.get(id=department)
            data = data.filter(task__staff__dep_id = department).distinct()
        except (KeyError):
            print ('Department ID error in get_projects function')

    #applying task filter if it exists
    if task and type(task) == int:
        try:
            s = Task.objects.get(id=task)
            data = data.filter(task__id = task)
        except (KeyError):
            print ('Task ID error in get_tasks function')

    #sorting
    if sort == 'start':
        data = data.order_by('start_date')
    elif sort == 'end':
        data = data.order_by('end_date')

    return data

#function that creates dot product of project matrix and adds a bottom row with project number for easier identification later
def matrix_mult(m):
    return np.insert(np.dot(m.T, m), len(m.T), range(0, len(m.T)), axis = 0)

#function that will find series of non-overlapping projects
def project_line(m):
    indices = [0]
    projects = [m.T[0][len(m) - 1]]
    while m[indices[-1]][np.argmin(m[indices[-1]])] == 0:
        t = np.argmin(m[indices[-1]])
        indices.append(t + indices[-1])
        projects.append(m.T[t][len(m) - 1])
        m = np.delete(m, range(0, t), axis = 1)
    return {'projects': projects, 'indices': indices}

#function that distributes ids of projects to respective lines
def fill_project_lines(m):
    #m = matrix_mult(m)
    #print('MATRIX: ', m)
    lines = []
    lines.append(project_line(m)['projects'])
    m = np.delete(m, lines[-1], axis=1)
    m = np.delete(m, lines[-1], axis=0)
    while len(m.T) > 0 :
        r = project_line(m)
        lines.append(r['projects'])
        m = np.delete(m, r['indices'], axis=1)
        m = np.delete(m, r['indices'], axis=0)
    return lines

w_len = 31.5
d_len = 4.5
y_len = 1638

#function that fills all the lines of a section
def fill_section_rows(projects, start):
    if type(start) != datetime.date : start = datetime.date.today().replace(month = 1, day = 1)
    if len(projects) > 0:
        st = projects.order_by('start_date')[0].start()
        en = projects.order_by('-end_date')[0].end()
        matrix = matrix_mult(np.delete(taskdays_matrix(st, en, projects, zero_matrix(st, en, projects)),[0], axis=1))
        rows = []
        for line in fill_project_lines(matrix):
            row = []
            for i in line:
                row.append({'object': projects[int(i)], 'days': projects[int(i)].days() * d_len, 'offset': ((projects[int(i)].start() - start) / datetime.timedelta(days = 1)) * d_len, 'weeks': projects[int(i)].weeks()})
            rows.append(row)
        return rows
    else: return []

#function that gets project calendar data per section
def fill_project_sections(end_after = False, group = 'stream', staff = False):
    if type(end_after) != datetime.date : end_after = datetime.date.today().replace(month = 1, day = 1)
    if not staff:
        projects = get_projects(end_after = end_after)
    else:
        try:
            st = Staff.objects.get(id = int(staff))
            projects = get_tasks(staff = int(staff), end_after = end_after)
        except (KeyError):
            print('Staff ID error in fill_project_sections function')
            projects = get_projects(end_after = end_after)
            staff = False
        if staff : 
            projects = get_tasks(staff = int(staff), end_after = end_after)

    cal = []
    if group:
        if group == 'stream':
            for s in Stream.objects.all():
                if not staff:
                    cal.append({'object': s, 'rows': fill_section_rows(projects = projects.filter(stream = s), start = end_after)})
                else:
                    cal.append({'object': s, 'rows': fill_section_rows(projects = projects.filter(project__stream = s), start = end_after)})
        elif group == 'department':
            for dep in Department.objects.all():
                if not staff:
                    cal.append({'object': dep, 'rows': fill_section_rows(projects = projects.filter(task__staff__dep = dep).distinct(), start = end_after)})
                else:
                    cal.append({'object': dep, 'rows': fill_section_rows(projects = projects.filter(staff__dep = dep), start = end_after)})
    else:
        cal.append({'object': False, 'rows': fill_section_rows(projects = projects, start = end_after)})
    return cal

#function that fills data for project calendar header
def fill_month_header(start, months = 18):
    if type(start) != datetime.date : 
        start = datetime.date.today().replace(month = 1, day = 1)
    else:
        start = start.replace(day = 1)
    
    if type(months) != int : months = 18
    elif months < 2 : months = 18

    d = datetime.timedelta(days=1)
    header = {'month': [], 'week': [], 'offset': {'calendar': int(((datetime.date.today() - start) / d - 30) * d_len), 'weeks': 0, 'today': ((datetime.date.today() - start) / d + 1) * d_len}}

    header['month'].append({'date': start, 'days': calendar.monthrange(start.year, start.month)[1]})
    for m in range(1, months):
        t_day = header['month'][-1]['date'] + d * header['month'][-1]['days']
        header['month'].append({'date': t_day, 'days': calendar.monthrange(t_day.year, t_day.month)[1]})

    header['week'].append(start.isocalendar()[1])
    header['offset']['weeks'] = start.weekday() / 7.0 * w_len
    num_weeks = int(round(((header['month'][-1]['date'].replace(day = header['month'][-1]['days']) - start) / d + 1.0) / 7.0, 0))
    for w in range(1, num_weeks):
        header['week'].append((start + w * 7 * d).isocalendar()[1])
    return header


#function that puts together all necessary parts together
def project_calendar_context(start = False, group = 'stream', months = 18, staff = False):
    if type(start) != datetime.date : 
        start = datetime.date.today().replace(month = 1, day = 1)
    else:
        start = start.replace(day = 1)

    d = datetime.timedelta(days = 1)

    if group not in ['stream', 'department', False]: group = 'stream'

    if type(months) != int or months < 2: months = 18

    context = {'dimensions': {'width': 0, 'height': 0}, 'header': fill_month_header(start = start, months = months), 'calendar': fill_project_sections(end_after = start, group = group, staff = staff)}
    context['dimensions']['width'] = (context['header']['month'][-1]['date'] + d * context['header']['month'][-1]['days'] - start) / d * d_len
    context['dimensions']['height'] = 56 + len(context['calendar']) * 28 + sum([len(section['rows']) for section in context['calendar']]) * 28

    return context

#function that creates all necessary content for dashboards
#!!!! IT SHOULD BE MODIFIED TO INCLUDE DATA FOR DASHBOARD FOR STAFF & PROJECTS
def dashboard_context(project = False, staff = False, obj = False, obj_id = False, show_empty = True, group_dash = 'stream', row='staff'):
    today = datetime.date.today()
    d = datetime.timedelta(days = 1)
    if group_dash not in ['stream', 'department', False] : group_dash = 'stream'

    context = {'height': 0, 'tasks': 0, 'projects_this_week': 0, 'projects_next_week': 0, 'deadlines': 0, 'upcoming': 0,}
    context['tasks'] = calendar_context(start = 'this_week', days_in_line = 7, num_lines = 1, obj = obj, obj_id = obj_id, group = group_dash, row = row, show_empty = show_empty)
    
    this_week = []
    next_week = []
    deadlines = []
    upcoming = []

    if group_dash == 'stream':
        for stream in Stream.objects.all():
            if not project and not staff:
                this_week.append({'stream': stream, 'projects': get_projects(start = week_start(today), end = week_end(today), stream = stream.id)})
                next_week.append({'stream': stream, 'projects': get_projects(start_in = {'start': week_start(week_start(today + 7 * d)), 'end': week_end(week_start(today + 7 * d))}, stream = stream.id)})
            elif project:
                this_week.append({'stream': stream, 'projects': get_tasks(project = project, stream = stream.id)})
            elif staff:
                this_week.append({'stream': stream, 'projects': get_tasks(start = week_start(today), end = week_end(today), staff = staff, stream = stream.id)})
                next_week.append({'stream': stream, 'projects': get_tasks(start_in = {'start': week_start(week_start(today + 7 * d)), 'end': week_end(week_start(today + 7 * d))}, staff = staff, stream = stream.id)})
            deadlines.append({'stream': stream, 'tasks': get_tasks(project = project, staff = staff, deadline = week_start(today), sort='end', stream = stream.id)})
            upcoming.append({'stream': stream, 'tasks': get_tasks(project = project, staff = staff, start_in = {'start': today, 'end': today + 9 * d}, sort='start', stream = stream.id)})

    elif group_dash == 'department':
        for dep in Department.objects.all():
            if not project and not staff:
                this_week.append({'stream': dep, 'projects': get_projects(start = week_start(today), end = week_end(today), department = dep.id)})
                next_week.append({'stream': dep, 'projects': get_projects(start_in = {'start': week_start(week_start(today + 7 * d)), 'end': week_end(week_start(today + 7 * d))}, department = dep.id)})
            elif project:
                this_week.append({'stream': dep, 'projects': get_tasks(project = project, department = dep.id)})
            elif staff:
                this_week.append({'stream': dep, 'projects': get_tasks(start = week_start(today), end = week_end(today),staff = staff, department = dep.id)})
                next_week.append({'stream': dep, 'projects': get_tasks(start_in = {'start': week_start(week_start(today + 7 * d)), 'end': week_end(week_start(today + 7 * d))}, staff = staff, department = dep.id)})
            deadlines.append({'stream': dep, 'tasks': get_tasks(project = project, staff = staff, deadline = week_start(today), sort='end', department = dep.id)})
            upcoming.append({'stream': dep, 'tasks': get_tasks(project = project, staff = staff, start_in = {'start': today, 'end': today + 9 * d}, sort='start', department = dep.id)})

    context['projects_this_week'] = this_week
    context['projects_next_week'] = next_week
    context['deadlines'] = deadlines
    context['upcoming'] = upcoming
    if not project:
        context['height'] = max(context['tasks'][0]['dimensions']['height'], 
            62 + len(context['projects_this_week']) * 22 * 2 + (sum([len(section['projects']) for section in context['projects_this_week']]) + sum([len(section['projects']) for section in context['projects_next_week']])) * 28, 
            86 + len(context['deadlines']) * 22 + sum([len(section['tasks']) for section in context['deadlines']]) * 42 + len(context['upcoming']) * 22 + sum([len(section['tasks']) for section in context['upcoming']]) * 42) + 10
    elif project:
        context['height'] = max(context['tasks'][0]['dimensions']['height'], 
            22 + len(context['projects_this_week']) * 22 + sum([len(section['projects']) for section in context['projects_this_week']]) * 28, 
            86 + len(context['deadlines']) * 22 + sum([len(section['tasks']) for section in context['deadlines']]) * 42 + len(context['upcoming']) * 22 + sum([len(section['tasks']) for section in context['upcoming']]) * 42) + 10

    return context






