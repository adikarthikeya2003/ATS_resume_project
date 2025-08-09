from django import forms
from .models import ResumeAnalysis

class ResumeUploadForm(forms.ModelForm):
    resume_file = forms.FileField(
        label='Upload Resume',
        help_text='Upload your resume in PDF or DOCX format (max 10MB)',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.docx'
        })
    )
    
    job_description = forms.CharField(
        label='Job Description',
        help_text='Paste the complete job description here',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'Paste the job description here...'
        })
    )
    
    class Meta:
        model = ResumeAnalysis
        fields = ['resume_file', 'job_description']
    
    def clean_resume_file(self):
        resume_file = self.cleaned_data.get('resume_file')
        
        if resume_file:
            # Check file size (10MB limit)
            if resume_file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('File size must be under 10MB')
            
            # Check file extension
            allowed_extensions = ['.pdf', '.docx']
            file_extension = resume_file.name.lower().split('.')[-1]
            if f'.{file_extension}' not in allowed_extensions:
                raise forms.ValidationError('Only PDF and DOCX files are allowed')
        
        return resume_file
    
    def clean_job_description(self):
        jd = self.cleaned_data.get('job_description')
        
        if len(jd.strip()) < 50:
            raise forms.ValidationError('Job description must be at least 50 characters long')
        
        return jd.strip()

class SettingsForm(forms.Form):
    openai_api_key = forms.CharField(
        label='OpenAI API Key (Optional)',
        required=False,
        help_text='Enter your OpenAI API key for AI-powered resume improvements',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'sk-...'
        })
    )