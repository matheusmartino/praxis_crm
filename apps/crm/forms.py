from django import forms

from apps.crm.models import Cliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            "nome", "cnpj_cpf", "tipo",
            "telefone", "email",
            "nome_contato_principal", "telefone_contato", "email_contato",
        ]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "cnpj_cpf": forms.TextInput(attrs={"class": "form-control", "placeholder": "Opcional para cadastro rápido"}),
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "telefone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "nome_contato_principal": forms.TextInput(attrs={"class": "form-control"}),
            "telefone_contato": forms.TextInput(attrs={"class": "form-control"}),
            "email_contato": forms.EmailInput(attrs={"class": "form-control"}),
        }
