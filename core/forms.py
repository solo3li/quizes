from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists.")
        return email

class OTPVerificationForm(forms.Form):
    otp = forms.CharField(max_length=6, required=True, label="Enter OTP")

class QuizGenerationForm(forms.Form):
    DIFFICULTY_CHOICES = [('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard')]
    
    title = forms.CharField(max_length=255, required=True)
    text_input = forms.CharField(widget=forms.Textarea, required=False)
    pdf_file = forms.FileField(required=False)
    url_input = forms.URLField(required=False)
    
    num_questions = forms.IntegerField(min_value=1, max_value=50, initial=5)
    difficulty = forms.ChoiceField(choices=DIFFICULTY_CHOICES, initial='Medium')
    
    mcq = forms.BooleanField(required=False, initial=True, label="Multiple Choice Questions (MCQ)")
    tf = forms.BooleanField(required=False, initial=True, label="True/False Questions (TF)")

    def clean(self):
        cleaned_data = super().clean()
        text_input = cleaned_data.get('text_input')
        pdf_file = cleaned_data.get('pdf_file')
        url_input = cleaned_data.get('url_input')
        
        if not (text_input or pdf_file or url_input):
            raise forms.ValidationError("Please provide either text, a PDF, or a URL.")
        
        mcq = cleaned_data.get('mcq')
        tf = cleaned_data.get('tf')
        if not (mcq or tf):
            raise forms.ValidationError("Please select at least one question type.")
        
        return cleaned_data
