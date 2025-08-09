import spacy
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np
import re
from typing import List, Dict, Tuple, Any

class NLPProcessor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.bert_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Technical skills patterns
        self.skill_patterns = {
            'programming_languages': [
                'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin',
                'typescript', 'go', 'rust', 'scala', 'r', 'matlab', 'perl', 'vb.net'
            ],
            'web_technologies': [
                'html', 'css', 'react', 'angular', 'vue', 'node.js', 'express', 'django',
                'flask', 'spring', 'asp.net', 'laravel', 'ruby on rails', 'jquery'
            ],
            'databases': [
                'mysql', 'postgresql', 'mongodb', 'sqlite', 'oracle', 'sql server',
                'redis', 'cassandra', 'elasticsearch', 'dynamodb'
            ],
            'cloud_platforms': [
                'aws', 'azure', 'gcp', 'google cloud', 'heroku', 'digitalocean',
                'docker', 'kubernetes', 'terraform'
            ],
            'tools': [
                'git', 'jenkins', 'jira', 'confluence', 'slack', 'figma', 'photoshop',
                'illustrator', 'tableau', 'power bi', 'excel'
            ]
        }
    
    def preprocess_text(self, text: str) -> str:
        """Advanced text preprocessing"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs and email addresses
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove special characters but keep important ones
        text = re.sub(r'[^\w\s\.\,\-\+\#]', ' ', text)
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords and lemmatize
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens 
                 if token not in self.stop_words and len(token) > 2]
        
        return ' '.join(tokens)
    
    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extract technical skills from text using NLP and patterns"""
        text_lower = text.lower()
        extracted_skills = {category: [] for category in self.skill_patterns.keys()}
        
        # Pattern-based extraction
        for category, skills in self.skill_patterns.items():
            for skill in skills:
                if skill in text_lower:
                    extracted_skills[category].append(skill)
        
        # NLP-based extraction for additional skills
        doc = self.nlp(text)
        additional_skills = []
        
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'PRODUCT', 'GPE'] and len(ent.text) > 2:
                # Check if it might be a technology
                skill_lower = ent.text.lower()
                if any(tech_word in skill_lower for tech_word in 
                      ['api', 'framework', 'library', 'platform', 'tool', 'language']):
                    additional_skills.append(ent.text)
        
        # Extract skills using noun phrases
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.lower().strip()
            if (len(chunk_text.split()) <= 3 and 
                chunk_text not in self.stop_words and
                any(char.isalpha() for char in chunk_text)):
                additional_skills.append(chunk_text)
        
        extracted_skills['other'] = list(set(additional_skills))
        
        return extracted_skills
    
    def calculate_tfidf_similarity(self, resume_text: str, jd_text: str) -> Dict[str, Any]:
        """Calculate TF-IDF based similarity"""
        # Preprocess texts
        resume_processed = self.preprocess_text(resume_text)
        jd_processed = self.preprocess_text(jd_text)
        
        # Calculate TF-IDF
        vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform([resume_processed, jd_processed])
        
        # Calculate similarity
        similarity_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        
        # Get feature names and scores
        feature_names = vectorizer.get_feature_names_out()
        resume_scores = tfidf_matrix[0].toarray()[0]
        jd_scores = tfidf_matrix[1].toarray()[0]
        
        # Find top matching terms
        matching_terms = []
        for i, (resume_score, jd_score) in enumerate(zip(resume_scores, jd_scores)):
            if resume_score > 0 and jd_score > 0:
                matching_terms.append({
                    'term': feature_names[i],
                    'resume_score': resume_score,
                    'jd_score': jd_score,
                    'combined_score': resume_score * jd_score
                })
        
        matching_terms.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return {
            'similarity_score': similarity_score,
            'matching_terms': matching_terms[:20],
            'vectorizer': vectorizer,
            'resume_vector': tfidf_matrix[0],
            'jd_vector': tfidf_matrix[1]
        }
    
    def calculate_bert_similarity(self, resume_text: str, jd_text: str) -> Dict[str, Any]:
        """Calculate BERT-based semantic similarity"""
        # Split texts into sentences for better embeddings
        resume_sentences = [sent.text for sent in self.nlp(resume_text).sents if len(sent.text.strip()) > 10]
        jd_sentences = [sent.text for sent in self.nlp(jd_text).sents if len(sent.text.strip()) > 10]
        
        # Generate embeddings
        resume_embeddings = self.bert_model.encode(resume_sentences)
        jd_embeddings = self.bert_model.encode(jd_sentences)
        
        # Calculate overall document similarity
        resume_doc_embedding = np.mean(resume_embeddings, axis=0)
        jd_doc_embedding = np.mean(jd_embeddings, axis=0)
        
        doc_similarity = cosine_similarity([resume_doc_embedding], [jd_doc_embedding])[0][0]
        
        # Calculate sentence-level similarities
        sentence_similarities = []
        for i, resume_sent in enumerate(resume_sentences):
            max_sim = 0
            best_match = ""
            for j, jd_sent in enumerate(jd_sentences):
                sim = cosine_similarity([resume_embeddings[i]], [jd_embeddings[j]])[0][0]
                if sim > max_sim:
                    max_sim = sim
                    best_match = jd_sent
            
            sentence_similarities.append({
                'resume_sentence': resume_sent,
                'best_match': best_match,
                'similarity': max_sim
            })
        
        return {
            'document_similarity': doc_similarity,
            'sentence_similarities': sentence_similarities,
            'resume_embeddings': resume_embeddings,
            'jd_embeddings': jd_embeddings
        }
    
    def extract_keywords(self, text: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """Extract important keywords using TF-IDF"""
        processed_text = self.preprocess_text(text)
        
        vectorizer = TfidfVectorizer(max_features=top_k*2, ngram_range=(1, 3))
        tfidf_matrix = vectorizer.fit_transform([processed_text])
        
        feature_names = vectorizer.get_feature_names_out()
        tfidf_scores = tfidf_matrix.toarray()[0]
        
        keywords = [{'keyword': feature_names[i], 'score': tfidf_scores[i]} 
                   for i in range(len(feature_names)) if tfidf_scores[i] > 0]
        
        keywords.sort(key=lambda x: x['score'], reverse=True)
        
        return keywords[:top_k]
    