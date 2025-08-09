import numpy as np
from typing import Dict, List, Any, Tuple
from .nlp_processor import NLPProcessor

class ATSScoreCalculator:
    def __init__(self):
        self.nlp_processor = NLPProcessor()
        
        # Scoring weights
        self.weights = {
            'keyword_match': 0.30,
            'skill_match': 0.25,
            'semantic_similarity': 0.20,
            'experience_relevance': 0.15,
            'formatting_quality': 0.10
        }
    
    def calculate_ats_score(self, resume_data: Dict[str, Any], jd_text: str) -> Dict[str, Any]:
        """Calculate comprehensive ATS score"""
        resume_text = resume_data['text']
        
        # 1. Keyword Matching Score
        keyword_score_data = self._calculate_keyword_score(resume_text, jd_text)
        
        # 2. Skills Matching Score
        skill_score_data = self._calculate_skill_score(resume_text, jd_text)
        
        # 3. Semantic Similarity Score
        semantic_score_data = self._calculate_semantic_score(resume_text, jd_text)
        
        # 4. Experience Relevance Score
        experience_score_data = self._calculate_experience_score(
            resume_data.get('structured_content', {}), jd_text
        )
        
        # 5. Formatting Quality Score
        formatting_score_data = self._calculate_formatting_score(resume_data)
        
        # Calculate weighted total score
        total_score = (
            keyword_score_data['score'] * self.weights['keyword_match'] +
            skill_score_data['score'] * self.weights['skill_match'] +
            semantic_score_data['score'] * self.weights['semantic_similarity'] +
            experience_score_data['score'] * self.weights['experience_relevance'] +
            formatting_score_data['score'] * self.weights['formatting_quality']
        )
        
        # Generate improvement suggestions
        suggestions = self._generate_suggestions(
            keyword_score_data, skill_score_data, semantic_score_data,
            experience_score_data, formatting_score_data
        )
        
        return {
            'total_score': round(total_score, 1),
            'breakdown': {
                'keyword_match': keyword_score_data,
                'skill_match': skill_score_data,
                'semantic_similarity': semantic_score_data,
                'experience_relevance': experience_score_data,
                'formatting_quality': formatting_score_data
            },
            'suggestions': suggestions,
            'missing_skills': skill_score_data.get('missing_skills', []),
            'missing_keywords': keyword_score_data.get('missing_keywords', [])
        }
    
    def _calculate_keyword_score(self, resume_text: str, jd_text: str) -> Dict[str, Any]:
        """Calculate keyword matching score"""
        # Extract keywords from job description
        jd_keywords = self.nlp_processor.extract_keywords(jd_text, top_k=30)
        resume_keywords = self.nlp_processor.extract_keywords(resume_text, top_k=50)
        
        # Create keyword sets for comparison
        jd_keyword_set = {kw['keyword'].lower() for kw in jd_keywords}
        resume_keyword_set = {kw['keyword'].lower() for kw in resume_keywords}
        
        # Calculate matches
        matched_keywords = jd_keyword_set.intersection(resume_keyword_set)
        missing_keywords = jd_keyword_set - resume_keyword_set
        
        # Calculate score based on match percentage
        if len(jd_keyword_set) > 0:
            match_percentage = len(matched_keywords) / len(jd_keyword_set)
            score = min(match_percentage * 100, 100)
        else:
            score = 0
        
        return {
            'score': score,
            'matched_keywords': list(matched_keywords),
            'missing_keywords': list(missing_keywords),
            'total_jd_keywords': len(jd_keyword_set),
            'matched_count': len(matched_keywords)
        }
    
    def _calculate_skill_score(self, resume_text: str, jd_text: str) -> Dict[str, Any]:
        """Calculate skills matching score"""
        resume_skills = self.nlp_processor.extract_skills(resume_text)
        jd_skills = self.nlp_processor.extract_skills(jd_text)
        
        # Flatten skill lists
        resume_all_skills = set()
        jd_all_skills = set()
        
        for category, skills in resume_skills.items():
            resume_all_skills.update([skill.lower() for skill in skills])
        
        for category, skills in jd_skills.items():
            jd_all_skills.update([skill.lower() for skill in skills])
        
        # Calculate matches
        matched_skills = resume_all_skills.intersection(jd_all_skills)
        missing_skills = jd_all_skills - resume_all_skills
        
        # Calculate score
        if len(jd_all_skills) > 0:
            match_percentage = len(matched_skills) / len(jd_all_skills)
            score = min(match_percentage * 100, 100)
        else:
            score = 50  # Default score if no skills detected
        
        return {
            'score': score,
            'matched_skills': list(matched_skills),
            'missing_skills': list(missing_skills),
            'resume_skills_by_category': resume_skills,
            'jd_skills_by_category': jd_skills,
            'total_jd_skills': len(jd_all_skills),
            'matched_count': len(matched_skills)
        }
    
    def _calculate_semantic_score(self, resume_text: str, jd_text: str) -> Dict[str, Any]:
        """Calculate semantic similarity score"""
        # TF-IDF similarity
        tfidf_result = self.nlp_processor.calculate_tfidf_similarity(resume_text, jd_text)
        
        # BERT similarity
        bert_result = self.nlp_processor.calculate_bert_similarity(resume_text, jd_text)
        
        # Combine both similarities
        tfidf_score = tfidf_result['similarity_score'] * 100
        bert_score = bert_result['document_similarity'] * 100
        
        # Weighted average (BERT given higher weight for semantic understanding)
        combined_score = (tfidf_score * 0.4 + bert_score * 0.6)
        
        return {
            'score': combined_score,
            'tfidf_similarity': tfidf_score,
            'bert_similarity': bert_score,
            'top_matching_terms': tfidf_result['matching_terms'][:10]
        }
    
    def _calculate_experience_score(self, structured_content: Dict[str, Any], jd_text: str) -> Dict[str, Any]:
        """Calculate experience relevance score"""
        if not structured_content or 'paragraphs' not in structured_content:
            return {'score': 30, 'details': 'Unable to analyze experience structure'}
        
        paragraphs = structured_content['paragraphs']
        experience_paragraphs = []
        
        # Identify experience-related paragraphs
        experience_keywords = ['experience', 'worked', 'developed', 'managed', 'led', 'responsible', 'achieved']
        
        for para in paragraphs:
            para_text = para['text'].lower()
            if any(keyword in para_text for keyword in experience_keywords):
                experience_paragraphs.append(para['text'])
        
        if not experience_paragraphs:
            return {'score': 20, 'details': 'No clear experience section found'}
        
        # Calculate semantic similarity of experience with JD
        experience_text = ' '.join(experience_paragraphs)
        similarity = self.nlp_processor.calculate_bert_similarity(experience_text, jd_text)
        
        score = similarity['document_similarity'] * 100
        
        return {
            'score': score,
            'experience_paragraphs_count': len(experience_paragraphs),
            'relevance_score': similarity['document_similarity']
        }
    
    def _calculate_formatting_score(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate formatting quality score"""
        score = 100
        issues = []
        
        metadata = resume_data.get('metadata', {})
        
        # Check for formatting issues from extraction
        if 'formatting_issues' in metadata and metadata['formatting_issues']:
            score -= len(metadata['formatting_issues']) * 10
            issues.extend(metadata['formatting_issues'])
        
        # Check document length
        text_length = len(resume_data['text'])
        if text_length < 500:
            score -= 20
            issues.append("Resume appears too short")
        elif text_length > 5000:
            score -= 10
            issues.append("Resume might be too long")
        
        # Check for structured content
        if 'structured_content' in resume_data:
            structured = resume_data['structured_content']
            if len(structured.get('paragraphs', [])) < 3:
                score -= 15
                issues.append("Lacks proper paragraph structure")
        
        score = max(score, 0)
        
        return {
            'score': score,
            'issues': issues,
            'metadata': metadata
        }
    
    def _generate_suggestions(self, keyword_data: Dict, skill_data: Dict, 
                            semantic_data: Dict, experience_data: Dict, 
                            formatting_data: Dict) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        # Keyword suggestions
        if keyword_data['score'] < 60:
            missing_kw = keyword_data.get('missing_keywords', [])
            if missing_kw:
                suggestions.append(f"Add these important keywords: {', '.join(list(missing_kw)[:5])}")
        
        # Skill suggestions
        if skill_data['score'] < 70:
            missing_skills = skill_data.get('missing_skills', [])
            if missing_skills:
                suggestions.append(f"Consider adding these skills: {', '.join(list(missing_skills)[:5])}")
        
        # Semantic suggestions
        if semantic_data['score'] < 50:
            suggestions.append("Improve content relevance by using more job-specific language")
        
        # Experience suggestions
        if experience_data['score'] < 60:
            suggestions.append("Highlight more relevant work experience and achievements")
        
        # Formatting suggestions
        if formatting_data['score'] < 80:
            for issue in formatting_data.get('issues', []):
                suggestions.append(f"Fix formatting: {issue}")
        
        if not suggestions:
            suggestions.append("Great job! Your resume shows good alignment with the job requirements.")
        
        return suggestions