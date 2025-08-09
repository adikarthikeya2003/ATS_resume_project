from django.db import models
from django.contrib.auth.models import User
import json

class ResumeAnalysis(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    resume_file = models.FileField(upload_to='uploads/resumes/')
    job_description = models.TextField()
    
    # Analysis results
    ats_score = models.FloatField()
    analysis_results = models.JSONField()  # Store detailed results
    
    # File paths
    original_resume_path = models.CharField(max_length=500)
    updated_resume_path = models.CharField(max_length=500, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Analysis {self.id} - Score: {self.ats_score}"
    
    def get_suggestions(self):
        """Get improvement suggestions from analysis results"""
        return self.analysis_results.get('suggestions', [])
    
    def get_missing_skills(self):
        """Get missing skills from analysis"""
        return self.analysis_results.get('missing_skills', [])

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    analyses_count = models.IntegerField(default=0)
    premium_user = models.BooleanField(default=False)
    openai_api_key = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return f"{self.user.username} Profile"