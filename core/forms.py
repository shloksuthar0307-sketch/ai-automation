import re
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from .models import QuoteRequest

phone_regex = RegexValidator(
    regex=r'^[+]?[0-9\s\-()]{6,30}$',
    message="Please enter a valid phone or WhatsApp number (digits, +, spaces, hyphens)."
)


class QuoteForm(forms.ModelForm):
    # Anti-bot honeypot field (hidden from legitimate users, auto-filled by bots)
    contact_ref_url = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'id': 'formContactRefUrl',
            'tabindex': '-1',
            'autocomplete': 'off',
            'style': 'position: absolute; left: -9999px; width: 1px; height: 1px; opacity: 0; pointer-events: none;',
            'aria-hidden': 'true',
        })
    )
    website_trap = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'id': 'formWebsiteTrap',
            'tabindex': '-1',
            'autocomplete': 'off',
            'style': 'position: absolute; left: -9999px; width: 1px; height: 1px; opacity: 0; pointer-events: none;',
            'aria-hidden': 'true',
        })
    )

    class Meta:
        model = QuoteRequest
        fields = ['name', 'email', 'business_name', 'phone', 'plan', 'brief']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'cult-input form-control',
                'id': 'clientName',
                'required': True,
                'maxlength': '120',
                'placeholder': 'Your Name *'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'cult-input form-control',
                'id': 'clientEmail',
                'maxlength': '150',
                'placeholder': 'Your Email Address (optional if phone given)'
            }),
            'business_name': forms.TextInput(attrs={
                'class': 'cult-input form-control',
                'id': 'clientBusiness',
                'maxlength': '150',
                'placeholder': 'Business / Project Name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'cult-input form-control',
                'id': 'clientPhone',
                'maxlength': '30',
                'placeholder': 'WhatsApp / Phone (optional if email given)'
            }),
            'brief': forms.Textarea(attrs={
                'class': 'cult-input form-control',
                'id': 'clientBrief',
                'rows': 4,
                'maxlength': '3000',
                'placeholder': 'Tell us what your business does and what pages or features you need...'
            }),
            'plan': forms.HiddenInput(attrs={'id': 'clientSelectedPlan'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False
        self.fields['phone'].required = False

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email', '').strip()
        phone = cleaned_data.get('phone', '').strip()
        if not email and not phone:
            raise ValidationError("Please provide at least one contact method (email or phone) so we can reach you.")
        return cleaned_data

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        # Remove CRLF / control characters to prevent header/log injection
        cleaned = re.sub(r'[\r\n\t]+', ' ', name)
        if len(cleaned) < 2:
            raise ValidationError("Please provide a valid name.")
        return cleaned

    def clean_email(self):
        return self.cleaned_data.get('email', '').strip()

    def clean_business_name(self):
        biz = self.cleaned_data.get('business_name', '').strip()
        return re.sub(r'[\r\n\t]+', ' ', biz)

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone:
            phone_regex(phone)
        return phone

    def clean_brief(self):
        brief = self.cleaned_data.get('brief', '').strip()
        if len(brief) > 3000:
            raise ValidationError("Project brief is too long (maximum 3,000 characters).")
        return brief

    def clean_plan(self):
        plan = self.cleaned_data.get('plan', 'Business').strip()
        valid_plans = [p[0] for p in QuoteRequest.PLAN_CHOICES]
        if plan not in valid_plans:
            plan = 'Business'
        return plan
