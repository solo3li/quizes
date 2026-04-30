import os
import django
import sys

# Setup Django Environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quiz_project.settings")
django.setup()

from core.utils import generate_quiz_from_ai, extract_text_from_url, extract_text_from_pdf
from core.models import User, Quiz, Question, Option, QuizSession, UserAnswer
from django.core.files.uploadedfile import SimpleUploadedFile

def run_tests():
    print("Starting Comprehensive Tests...\n")
    
    # 1. Test URL Extraction
    print("Testing Feature: URL Extraction...")
    url_text = extract_text_from_url("https://example.com")
    if url_text and len(url_text) > 0:
        print("  - URL Extraction Successful. Extracted text length:", len(url_text))
    else:
        print("  - URL Extraction Failed.")
        sys.exit(1)

    # 2. Test Text File parsing through PDF extractor
    print("\nTesting Feature: File parsing (.txt logic)...")
    fake_txt = SimpleUploadedFile("test.txt", b"This is a test text document.", content_type="text/plain")
    txt_content = extract_text_from_pdf(fake_txt)
    if "test text document" in txt_content:
        print("  - File parsing Successful.")
    else:
        print("  - File parsing Failed.")
        sys.exit(1)

    # 3. Test Gemini API (AI Generation)
    print("\nTesting Feature: Gemini AI Quiz Generation...")
    print("  - Sending prompt to Gemini...")
    sample_text = "The Python programming language was created by Guido van Rossum and was released in 1991. It emphasizes code readability."
    quiz_data = generate_quiz_from_ai(sample_text, num_questions=2, difficulty="Easy", question_types=["MCQ", "TF"])
    
    if quiz_data and isinstance(quiz_data, list) and len(quiz_data) > 0:
        print("  - Gemini API Call Successful!")
        print("  - Received JSON response:")
        print(f"      Number of Questions Generated: {len(quiz_data)}")
        print(f"      Sample Question Text: '{quiz_data[0].get('text', 'N/A')}'")
    else:
        print("  - Gemini API Call Failed. Did not receive valid JSON.")
        sys.exit(1)

    # 4. Test Database Models
    print("\nTesting Feature: Database Models (User, Quiz, Session, Results)...")
    try:
        user, _ = User.objects.get_or_create(username="test_ai_user", email="test_ai@example.com")
        quiz = Quiz.objects.create(user=user, title="Automated Test Quiz", difficulty="Easy")
        
        # Save generated question to DB
        q_data = quiz_data[0]
        question = Question.objects.create(
            quiz=quiz,
            text=q_data.get("text", "Sample Q"),
            question_type=q_data.get("question_type", "MCQ"),
            explanation=q_data.get("explanation", "Test explanation")
        )
        
        correct_opt = None
        for opt_data in q_data.get("options", []):
            opt = Option.objects.create(
                question=question,
                text=opt_data.get("text", "Sample Opt"),
                is_correct=opt_data.get("is_correct", False)
            )
            if opt.is_correct:
                correct_opt = opt
                
        # Simulate Quiz Session
        session = QuizSession.objects.create(user=user, quiz=quiz, total_questions=1)
        UserAnswer.objects.create(session=session, question=question, selected_option=correct_opt, is_correct=True)
        session.score = 1
        session.save()
        
        print("  - Database operations successful.")
        print(f"  - Simulated a Session for '{user.username}' with Score: {session.score}/{session.total_questions}")
        
    except Exception as e:
        print(f"  - Database Test Failed: {e}")
        sys.exit(1)

    print("\n✅ All Features and API Keys Tested Successfully!")

if __name__ == "__main__":
    run_tests()
