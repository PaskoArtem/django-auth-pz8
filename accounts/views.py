from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from .models import AcademicGroup, Course, Department, StudentProfile
from .forms import AcademicGroupForm, CourseForm, DepartmentForm


def is_methodist(user):
    return user.groups.filter(
        name='Методист'
    ).exists()


@login_required
def api_dashboard(request):
    return render(request, 'api_dashboard.html', {'is_methodist': is_methodist(request.user)})


@login_required
def profile(request):
    return render(
        request,
        'profile.html',
        {
            'is_methodist': is_methodist(request.user)
        }
    )


@login_required
def course_list(request):
    courses = Course.objects.select_related('department').all()

    return render(
        request,
        'course_list.html',
        {
            'courses': courses,
            'is_methodist': is_methodist(request.user),
        }
    )

@login_required
@user_passes_test(is_methodist)
def course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('course_list')
    else:
        form = CourseForm()

    return render(
        request,
        'object_form.html',
        {
            'form': form,
            'title': 'Добавление курса',
        }
    )

@login_required
@user_passes_test(is_methodist)
def course_update(request, pk):
    course = get_object_or_404(
        Course,
        pk=pk
    )

    if request.method == 'POST':
        form = CourseForm(
            request.POST,
            instance=course
        )

        if form.is_valid():
            form.save()
            return redirect('course_list')
    else:
        form = CourseForm(
            instance=course
        )

    return render(
        request,
        'object_form.html',
        {
            'form': form,
            'title': 'Изменение курса',
        }
    )

@login_required
@user_passes_test(is_methodist)
def course_delete(request, pk):
    course = get_object_or_404(
        Course,
        pk=pk
    )

    if request.method == 'POST':
        course.delete()
        return redirect('course_list')

    return render(
        request,
        'object_confirm_delete.html',
        {
            'object': course,
            'title': 'Удаление курса',
        }
    )

@login_required
def department_list(request):
    departments = Department.objects.all()

    return render(
        request,
        'department_list.html',
        {
            'departments': departments,
            'is_methodist': is_methodist(request.user),
        }
    )

@login_required
@user_passes_test(is_methodist)
def department_create(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('department_list')
    else:
        form = DepartmentForm()

    return render(
        request,
        'object_form.html',
        {
            'form': form,
            'title': 'Добавление факультета',
        }
    )

@login_required
@user_passes_test(is_methodist)
def department_update(request, pk):
    department = get_object_or_404(
        Department,
        pk=pk
    )

    if request.method == 'POST':
        form = DepartmentForm(
            request.POST,
            instance=department
        )

        if form.is_valid():
            form.save()
            return redirect('department_list')
    else:
        form = DepartmentForm(
            instance=department
        )

    return render(
        request,
        'object_form.html',
        {
            'form': form,
            'title': 'Изменение факультета',
        }
    )

@login_required
@user_passes_test(is_methodist)
def department_delete(request, pk):
    department = get_object_or_404(
        Department,
        pk=pk
    )

    if request.method == 'POST':
        department.delete()
        return redirect('department_list')

    return render(
        request,
        'object_confirm_delete.html',
        {
            'object': department,
            'title': 'Удаление факультета',
        }
    )

@login_required
def academic_group_list(request):
    academic_groups = AcademicGroup.objects.select_related(
        'department'
    ).all()

    return render(
        request,
        'academic_group_list.html',
        {
            'academic_groups': academic_groups,
            'is_methodist': is_methodist(request.user),
        }
    )

@login_required
@user_passes_test(is_methodist)
def academic_group_create(request):
    if request.method == 'POST':
        form = AcademicGroupForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('academic_group_list')
    else:
        form = AcademicGroupForm()

    return render(
        request,
        'object_form.html',
        {
            'form': form,
            'title': 'Добавление учебной группы',
        }
    )

@login_required
@user_passes_test(is_methodist)
def academic_group_update(request, pk):
    academic_group = get_object_or_404(
        AcademicGroup,
        pk=pk
    )

    if request.method == 'POST':
        form = AcademicGroupForm(
            request.POST,
            instance=academic_group
        )

        if form.is_valid():
            form.save()
            return redirect('academic_group_list')
    else:
        form = AcademicGroupForm(
            instance=academic_group
        )

    return render(
        request,
        'object_form.html',
        {
            'form': form,
            'title': 'Изменение учебной группы',
        }
    )

@login_required
@user_passes_test(is_methodist)
def academic_group_delete(request, pk):
    academic_group = get_object_or_404(
        AcademicGroup,
        pk=pk
    )

    if request.method == 'POST':
        academic_group.delete()
        return redirect('academic_group_list')

    return render(
        request,
        'object_confirm_delete.html',
        {
            'object': academic_group,
            'title': 'Удаление учебной группы',
        }
    )

@login_required
def dashboard(request):
    selected_department = request.GET.get('department')

    departments = Department.objects.all()

    if selected_department:
        departments = departments.filter(id=selected_department)

    selected_department_obj = None

    if selected_department:
        selected_department_obj = Department.objects.filter(
            id=selected_department
        ).first()

    students_by_department = []

    for department in departments:
        students_by_department.append({
            'name': department.name,
            'count': department.students.count(),
        })

    groups_by_department = []

    for department in departments:
        groups_by_department.append({
            'name': department.name,
            'count': department.groups.count(),
        })

    courses_by_department = []

    for department in departments:
        courses_by_department.append({
            'name': department.name,
            'count': department.courses.count(),
        })

    if selected_department_obj:
        departments_count = 1
        groups_count = selected_department_obj.groups.count()
        courses_count = selected_department_obj.courses.count()
        students_count = selected_department_obj.students.count()
    else:
        departments_count = Department.objects.count()
        groups_count = AcademicGroup.objects.count()
        courses_count = Course.objects.count()
        students_count = StudentProfile.objects.count()


    context = {
        'departments_count': departments_count,
        'groups_count': groups_count,
        'courses_count': courses_count,
        'students_count': students_count,
        'students_by_department': students_by_department,
        'groups_by_department': groups_by_department,
        'selected_department': selected_department,
        'departments': Department.objects.all(),
        'courses_by_department': courses_by_department,
    }

    return render(
        request,
        'dashboard/dashboard.html',
        context
    )

@login_required
def groups_dashboard(request):
    selected_department = request.GET.get('department')

    departments = Department.objects.all()

    groups = AcademicGroup.objects.select_related('department').all()

    if selected_department:
        groups = groups.filter(department_id=selected_department)

    groups_data = []

    for group in groups:
        groups_data.append({
            'name': group.name,
            'department': group.department.name,
            'students_count': group.students.count(),
        })

    context = {
        'groups_count': groups.count(),
        'groups_data': groups_data,
        'departments': departments,
        'selected_department': selected_department,
    }

    return render(
        request,
        'dashboard/groups.html',
        context
    )

@login_required
def courses_dashboard(request):
    selected_department = request.GET.get('department')
    search_query = request.GET.get('search', '').strip()
    sort_order = request.GET.get('sort', 'students_desc')

    departments = Department.objects.all()

    courses = Course.objects.select_related('department').annotate(
        students_count=Count('students')
    )

    if selected_department:
        courses = courses.filter(department_id=selected_department)

    if search_query:
        courses = courses.filter(title__icontains=search_query)

    if sort_order == 'students_asc':
        courses = courses.order_by('students_count', 'title')
    elif sort_order == 'title':
        courses = courses.order_by('title')
    else:
        courses = courses.order_by('-students_count', 'title')

    courses_data = []

    for course in courses:
        courses_data.append({
            'title': course.title,
            'department': course.department.name,
            'students_count': course.students_count,
        })

    context = {
        'courses_count': courses.count(),
        'courses_data': courses_data,
        'departments': departments,
        'selected_department': selected_department,
        'search_query': search_query,
        'sort_order': sort_order,
    }

    return render(
        request,
        'dashboard/courses.html',
        context
    )