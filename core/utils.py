import os
import random
import string
import json
import requests
from bs4 import BeautifulSoup
import PyPDF2
from django.core.mail import send_mail
from django.conf import settings
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_otp():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def send_otp_email(email, otp):
    subject = "Your OTP for Quiz Generator"
    message = f"Your Verification Code is: {otp}"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

def extract_text_from_pdf(file_obj):
    try:
        # Check if it's actually a text file
        if file_obj.name.endswith('.txt'):
            return file_obj.read().decode('utf-8')
            
        reader = PyPDF2.PdfReader(file_obj)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from file: {e}")
        return ""

def extract_text_from_url(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.get_text(separator=' ', strip=True)
    except Exception as e:
        return ""

def generate_quiz_from_ai(text, num_questions, difficulty, question_types):
    prompt = f"""
    Generate a quiz with {num_questions} questions based on the following text.
    Difficulty: {difficulty}.
    Question types allowed: {', '.join(question_types)}.
    Output MUST be valid JSON in the following format exactly:
    [
        {{
            "text": "Question text here?",
            "question_type": "MCQ", // or "TF"
            "options": [
                {{"text": "Option A", "is_correct": true}},
                {{"text": "Option B", "is_correct": false}}
            ],
            "explanation": "Explanation for the correct answer."
        }}
    ]
    Return ONLY JSON, no markdown formatting.
    Text: {text}
    """
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        return json.loads(response_text)
    except Exception as e:
        print(f"AI generation failed: {e}")
        return None
