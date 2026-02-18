from django import forms

from apps.prospeccao.models import ContatoLead, Lead


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = [
            "nome",
            "empresa",
            "telefone",
            "whatsapp",
            "email",
            "origem",
            "produto_interesse",
            "status",
            "observacoes",
        ]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "empresa": forms.TextInput(attrs={"class": "form-control"}),
            "telefone": forms.TextInput(attrs={"class": "form-control"}),
            "whatsapp": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "origem": forms.Select(attrs={"class": "form-select"}),
            "produto_interesse": forms.TextInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "observacoes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class ContatoLeadForm(forms.ModelForm):
    """Formulário para registrar contato. O lead é passado pela view."""

    proximo_contato = forms.DateField(
        required=False,
        label="Data do próximo contato",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )

    class Meta:
        model = ContatoLead
        fields = ["tipo", "resultado", "observacao"]
        widgets = {
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "resultado": forms.Select(attrs={"class": "form-select"}),
            "observacao": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
