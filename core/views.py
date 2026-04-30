from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, OTPVerification, Quiz, Question, Option, QuizSession, UserAnswer
from .forms import CustomUserCreationForm, OTPVerificationForm, QuizGenerationForm
from django.contrib.auth.forms import AuthenticationForm
from .utils import generate_otp, send_otp_email, extract_text_from_pdf, extract_text_from_url, generate_quiz_from_ai
import json

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False # Require OTP verification to become active/usable
            user.save()
            
            otp_code = generate_otp()
            OTPVerification.objects.create(user=user, otp=otp_code)
            send_otp_email(user.email, otp_code)
            
            request.session['verification_user_id'] = user.id
            messages.success(request, "Registration successful. Please check your email for the OTP.")
            return redirect('verify_otp')
    else:
        form = CustomUserCreationForm()
    return render(request, 'auth/register.html', {'form': form})

def verify_otp_view(request):
    user_id = request.session.get('verification_user_id')
    if not user_id:
        return redirect('register')
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            submitted_otp = form.cleaned_data.get('otp')
            try:
                otp_record = OTPVerification.objects.get(user=user)
                if otp_record.otp == submitted_otp:
                    user.is_email_verified = True
                    user.is_active = True
                    user.save()
                    otp_record.delete()
                    del request.session['verification_user_id']
                    
                    login(request, user)
                    messages.success(request, "Email verified successfully! You are now logged in.")
                    return redirect('home')
                else:
                    messages.error(request, "Invalid OTP.")
            except OTPVerification.DoesNotExist:
                messages.error(request, "OTP record not found.")
    else:
        form = OTPVerificationForm()
    
    return render(request, 'auth/verify_otp.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_email_verified:
                # Resend OTP
                otp_code = generate_otp()
                OTPVerification.objects.update_or_create(user=user, defaults={'otp': otp_code})
                send_otp_email(user.email, otp_code)
                request.session['verification_user_id'] = user.id
                messages.warning(request, "Please verify your email. A new OTP has been sent.")
                return redirect('verify_otp')
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def home_view(request):
    quizzes = Quiz.objects.filter(user=request.user).order_by('-created_at')
    sessions = QuizSession.objects.filter(user=request.user).order_by('-created_at')[:5]
    return render(request, 'core/home.html', {'quizzes': quizzes, 'sessions': sessions})

@login_required
def generate_quiz_view(request):
    if request.method == 'POST':
        form = QuizGenerationForm(request.POST, request.FILES)
        if form.is_valid():
            title = form.cleaned_data['title']
            text_input = form.cleaned_data['text_input']
            pdf_file = form.cleaned_data.get('pdf_file')
            url_input = form.cleaned_data.get('url_input')
            num_questions = form.cleaned_data['num_questions']
            difficulty = form.cleaned_data['difficulty']
            
            q_types = []
            if form.cleaned_data['mcq']: q_types.append("MCQ")
            if form.cleaned_data['tf']: q_types.append("TF")
            
            # Extract content
            content = ""
            if text_input:
                content += text_input + "\n"
            if pdf_file:
                content += extract_text_from_pdf(pdf_file) + "\n"
            if url_input:
                content += extract_text_from_url(url_input) + "\n"
                
            if not content.strip():
                messages.error(request, "Could not extract any content from the provided sources.")
                return render(request, 'core/generate.html', {'form': form})
            
            # Call AI
            quiz_data = generate_quiz_from_ai(content[:15000], num_questions, difficulty, q_types)
            if not quiz_data:
                messages.error(request, "Failed to generate quiz from AI. Please try again.")
                return render(request, 'core/generate.html', {'form': form})
            
            # Save to DB
            quiz = Quiz.objects.create(user=request.user, title=title, difficulty=difficulty)
            
            for q_data in quiz_data:
                question = Question.objects.create(
                    quiz=quiz,
                    text=q_data.get('text', ''),
                    question_type=q_data.get('question_type', 'MCQ'),
                    explanation=q_data.get('explanation', '')
                )
                for opt_data in q_data.get('options', []):
                    Option.objects.create(
                        question=question,
                        text=opt_data.get('text', ''),
                        is_correct=opt_data.get('is_correct', False)
                    )
            
            messages.success(request, "Quiz generated successfully!")
            return redirect('quiz_detail', quiz_id=quiz.id)
    else:
        form = QuizGenerationForm()
    return render(request, 'core/generate.html', {'form': form})

@login_required
def quiz_detail_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, user=request.user)
    return render(request, 'core/quiz_detail.html', {'quiz': quiz})

@login_required
def take_quiz_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, user=request.user)
    questions = quiz.questions.all()
    
    if request.method == 'POST':
        session = QuizSession.objects.create(
            user=request.user,
            quiz=quiz,
            total_questions=questions.count()
        )
        score = 0
        
        for question in questions:
            selected_option_id = request.POST.get(f'question_{question.id}')
            if selected_option_id:
                selected_option = get_object_or_404(Option, id=selected_option_id)
                is_correct = selected_option.is_correct
                if is_correct:
                    score += 1
                UserAnswer.objects.create(
                    session=session,
                    question=question,
                    selected_option=selected_option,
                    is_correct=is_correct
                )
            else:
                UserAnswer.objects.create(
                    session=session,
                    question=question,
                    selected_option=None,
                    is_correct=False
                )
        
        session.score = score
        session.save()
        return redirect('quiz_result', session_id=session.id)

    return render(request, 'core/take_quiz.html', {'quiz': quiz, 'questions': questions})

@login_required
def quiz_result_view(request, session_id):
    session = get_object_or_404(QuizSession, id=session_id, user=request.user)
    answers = session.answers.all()
    return render(request, 'core/quiz_result.html', {'session': session, 'answers': answers})
