import datetime

from django.db import models
from django.utils import timezone

class Department(models.Model):
	name = models.CharField(max_length=200)
	def __str__(self):
		return self.name

	def staff(self):
		staff = Staff.objects.filter(dep = self).filter(active = True)
		return staff

class Stream(models.Model):
	name = models.CharField(max_length=200)
	def __str__(self):
		return self.name

	def projects(self):
		projects = Project.objects.filter(stream = self)
		return projects

class Staff(models.Model):
	name = models.CharField(max_length=200)
	dep = models.ForeignKey(Department, db_index=True, on_delete=models.CASCADE)
	active = models.BooleanField(db_index=True, default = True)

	def __str__(self):
		return self.name

	def projects(self):
		today = datetime.date.today()
		projects = Project.objects.filter(task__staff = self).filter(task_start_date__lte = today).filter(task_end_date__gte = today)
		return {'project': projects, 'num_projects': len(projects)}

class Project(models.Model):
	name = models.CharField(max_length=200)
	stream = models.ForeignKey(Stream, db_index=True, on_delete=models.SET_NULL, null = True)
	dates = models.BooleanField(default = False) #False means that actual tasks are needed to calculate start & end dates. True will take default values if they exist.
	task_start_date = models.DateField(null = True)
	task_end_date = models.DateField(null = True)
	start_date = models.DateField(null = True)
	end_date = models.DateField(null = True)
	active = models.BooleanField(db_index=True, default = True)
	comment = models.CharField(max_length=500, null=True) #let us comment the project and what it is supposed to achieve
	update = models.DateTimeField(default = timezone.now())

	def __str__(self):
		return self.name

	def start(self):
		if self.task_start_date:
			s = self.task_start_date
		else : s = self.start_date
		return s

	def tasks(self):
		if len(Task.objects.filter(project_id = self.id).filter(active = True)) > 0: return len(Task.objects.filter(project_id = self.id).filter(active = True))
		else: return False

	def end(self):
		if self.task_end_date:
			e = self.task_end_date
		else : e = self.end_date
		return e

	def days(self):
		if self.task_start_date and self.task_end_date:
			days = ((self.task_end_date - self.task_start_date) / datetime.timedelta(days = 1) + 1)
		else : days = ((self.end_date - self.start_date) / datetime.timedelta(days = 1) + 1)
		return int(days)

	def weeks(self):
		if self.task_start_date and self.task_end_date:
			weeks = round(((self.task_end_date - self.task_start_date) / datetime.timedelta(days = 1) + 1.0) / 7.0, 1)
		else: weeks = round(((self.end_date - self.start_date) / datetime.timedelta(days = 1) + 1.0) / 7.0, 1)
		return weeks

class Task(models.Model):
	name = models.CharField(max_length=200)
	staff = models.ForeignKey(Staff, db_index=True, on_delete=models.SET_NULL, null=True)
	worker = models.CharField(max_length=200, null=True) #this is in case the task is performed not by staff, but by someone outside of the company, e.g. certification
	project = models.ForeignKey(Project, db_index=True, on_delete=models.CASCADE)
	start_date = models.DateField(db_index=True)
	end_date = models.DateField(db_index=True)
	done = models.DecimalField(default = 0, max_digits=5, decimal_places=2, null=True) #to store percent of completion of the task.
	comment = models.CharField(max_length=500, null=True)
	active = models.BooleanField(db_index=True, default = True)
	update = models.DateTimeField(default = timezone.now())

	def __str__(self):
		return "%s by %s " % (self.name, self.staff)

	def start(self):
		return self.start_date

	def end(self):
		return self.end_date

	def days(self):
		return int((self.end_date - self.start_date) / datetime.timedelta(days = 1) + 1)

	def weeks(self):
		return round(((self.end_date - self.start_date) / datetime.timedelta(days = 1) + 1.0) / 7.0, 1)

class Holiday(models.Model):
	date = models.DateField(db_index=True)
	holiday = models.BooleanField(default = True)
	def __str__(self):
		return str(self.date)

# Create your models here.
