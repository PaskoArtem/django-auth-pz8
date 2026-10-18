from django import forms
from .models import (
    AcademicGroup,
    Course,
    Department,
)


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name']

        labels = {
            'name': 'Название кафедры',
        }

        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
        }


class AcademicGroupForm(forms.ModelForm):
    class Meta:
        model = AcademicGroup
        fields = ['name', 'department']

        labels = {
            'name': 'Название группы',
            'department': 'Кафедра',
        }

        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control'}
            ),

            'department': forms.Select(
                attrs={'class': 'form-select'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['department'].empty_label = 'Выберите кафедру'


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'department']

        labels = {
            'title': 'Название курса',
            'description': 'Описание',
            'department': 'Кафедра',
        }

        widgets = {
            'title': forms.TextInput(
                attrs={'class': 'form-control'}
            ),

            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4
                }
            ),

            'department': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['department'].empty_label = 'Выберите кафедру'