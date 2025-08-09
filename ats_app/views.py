from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, FileResponse, JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
import os
import json
from datetime import datetime

from .forms import ResumeUploadForm, SettingsForm
from .models import ResumeAnalysis, UserProfile
from .utils.text_extractor import TextExtractor
from .utils.nlp_processor import NLPProcessor
from .utils.score_calculator import ATSScoreCalculator
from .utils.resume_updater import ResumeUpdater

def index(request):
    """Home page with upload form"""
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            return handle_resume_upload(request, form)
    else:
        form = ResumeUploadForm()
    
    # Get recent analyses for display
    recent_analyses = ResumeAnalysis.objects.all()[:5]
    
    return render(request, 'ats_app/index.html', {
        'form': form,
        'recent_analyses': recent_analyses
    })

def handle_resume_upload(request, form):
    """Process uploaded resume and job description"""
    try:
        # Save the form to get file path
        analysis = form.save(commit=False)
        if request.user.is_authenticated:
            analysis.user = request.user
        
        # Save to get file path
        analysis.ats_score = 0  # Temporary score
        analysis.analysis_results = {}  # Temporary empty results
        analysis.save()
        
        # Get file paths
        resume_path = analysis.resume_file.path
        job_description = analysis.job_description
        
        # Extract text from resume
        text_extractor = TextExtractor()
        
        if resume_path.lower().endswith('.pdf'):
            resume_data = text_extractor.extract_from_pdf(resume_path)
        else:  # .docx
            resume_data = text_extractor.extract_from_docx(resume_path)
        
        # Calculate ATS score
        score_calculator = ATSScoreCalculator()
        score_results = score_calculator.calculate_ats_score(resume_data, job_description)
        
        # Update analysis with results
        analysis.ats_score = score_results['total_score']
        analysis.analysis_results = score_results
        analysis.original_resume_path = resume_path
        analysis.save()
        
        # Update user stats
        if request.user.is_authenticated:
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.analyses_count += 1
            profile.save()
        
        return redirect('analysis_results', analysis_id=analysis.id)
        
    except Exception as e:
        messages.error(request, f'Error processing resume: {str(e)}')
        return redirect('index')

def analysis_results(request, analysis_id):
    """Display analysis results"""
    analysis = get_object_or_404(ResumeAnalysis, id=analysis_id)
    
    # Prepare data for visualization
    breakdown = analysis.analysis_results.get('breakdown', {})
    
    # Create data for charts
    score_data = {
        'labels': [],
        'scores': [],
        'colors': []
    }
    
    color_map = {
        'keyword_match': '#FF6384',
        'skill_match': '#36A2EB',
        'semantic_similarity': '#FFCE56',
        'experience_relevance': '#4BC0C0',
        'formatting_quality': '#9966FF'
    }
    
    for category, data in breakdown.items():
        score_data['labels'].append(category.replace('_', ' ').title())
        score_data['scores'].append(data.get('score', 0))
        score_data['colors'].append(color_map.get(category, '#999999'))
    
    context = {
        'analysis': analysis,
        'score_data': json.dumps(score_data),
        'breakdown': breakdown,
        'suggestions': analysis.get_suggestions(),
        'missing_skills': analysis.get_missing_skills()[:10],  # Show top 10
    }
    
    return render(request, 'ats_app/results.html', context)

def update_resume(request, analysis_id):
    """Update resume with missing skills and keywords"""
    analysis = get_object_or_404(ResumeAnalysis, id=analysis_id)
    
    try:
        # Get user's OpenAI API key if available
        openai_key = None
        if request.user.is_authenticated:
            profile = UserProfile.objects.filter(user=request.user).first()
            if profile:
                openai_key = profile.openai_api_key
        
        # Initialize resume updater
        resume_updater = ResumeUpdater(openai_api_key=openai_key)
        
        # Extract original resume data again for updating
        text_extractor = TextExtractor()
        original_path = analysis.original_resume_path
        
        if original_path.lower().endswith('.pdf'):
            # For PDF, we can't update directly, so we'll create a new DOCX
            resume_data = text_extractor.extract_from_pdf(original_path)
            # Create a new DOCX from extracted text
            output_filename = f"updated_resume_{analysis.id}.docx"
            output_path = os.path.join(settings.MEDIA_ROOT, 'outputs', output_filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Create new document with extracted content
            from docx import Document
            doc = Document()
            doc.add_paragraph(resume_data['text'])
            resume_data['document'] = doc
        else:
            resume_data = text_extractor.extract_from_docx(original_path)
            output_filename = f"updated_resume_{analysis.id}.docx"
            output_path = os.path.join(settings.MEDIA_ROOT, 'outputs', output_filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Get missing skills and keywords
        missing_skills = analysis.analysis_results.get('missing_skills', [])
        missing_keywords = analysis.analysis_results.get('missing_keywords', [])
        
        # Update resume
        update_results = resume_updater.update_resume(
            resume_data, missing_skills, missing_keywords, output_path
        )
        
        # Update analysis record
        analysis.updated_resume_path = output_path
        analysis.save()
        
        messages.success(request, 'Resume updated successfully!')
        return JsonResponse({
            'success': True,
            'message': 'Resume updated successfully',
            'download_url': f'/media/outputs/{output_filename}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating resume: {str(e)}'
        })

def download_resume(request, analysis_id):
    """Download updated resume"""
    analysis = get_object_or_404(ResumeAnalysis, id=analysis_id)
    
    if not analysis.updated_resume_path or not os.path.exists(analysis.updated_resume_path):
        messages.error(request, 'Updated resume not found. Please update the resume first.')
        return redirect('analysis_results', analysis_id=analysis_id)
    
    try:
        response = FileResponse(
            open(analysis.updated_resume_path, 'rb'),
            as_attachment=True,
            filename=f'updated_resume_{analysis_id}.docx'
        )
        return response
    except Exception as e:
        messages.error(request, f'Error downloading file: {str(e)}')
        return redirect('analysis_results', analysis_id=analysis_id)

@login_required
def user_analyses(request):
    """Display user's past analyses"""
    analyses = ResumeAnalysis.objects.filter(user=request.user)
    
    return render(request, 'ats_app/user_analyses.html', {
        'analyses': analyses
    })

@login_required
def settings(request):
    """User settings page"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = SettingsForm(request.POST)
        if form.is_valid():
            profile.openai_api_key = form.cleaned_data['openai_api_key']
            profile.save()
            messages.success(request, 'Settings updated successfully!')
            return redirect('settings')
    else:
        form = SettingsForm(initial={'openai_api_key': profile.openai_api_key})
    
    return render(request, 'ats_app/settings.html', {
        'form': form,
        'profile': profile
    })

def api_analyze(request):
    """API endpoint for resume analysis"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        # This is a simplified API version
        # In production, you'd want proper authentication and rate limiting
        
        resume_text = request.POST.get('resume_text', '')
        job_description = request.POST.get('job_description', '')
        
        if not resume_text or not job_description:
            return JsonResponse({'error': 'Both resume_text and job_description are required'}, status=400)
        
        # Simulate resume data structure
        resume_data = {
            'text': resume_text,
            'metadata': {}
        }
        
        # Calculate score
        score_calculator = ATSScoreCalculator()
        results = score_calculator.calculate_ats_score(resume_data, job_description)
        
        return JsonResponse({
            'success': True,
            'ats_score': results['total_score'],
            'breakdown': results['breakdown'],
            'suggestions': results['suggestions'],
            'missing_skills': results['missing_skills'][:10]
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)