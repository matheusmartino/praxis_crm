from django import forms

from apps.sales.models import Interacao, Oportunidade


class OportunidadeForm(forms.ModelForm):
    class Meta:
        model = Oportunidade
        fields = ["titulo", "cliente", "valor_estimado", "descricao"]
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "form-control"}),
            "cliente": forms.Select(attrs={"class": "form-select"}),
            "valor_estimado": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "descricao": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class InteracaoForm(forms.ModelForm):
    class Meta:
        model = Interacao
        fields = ["oportunidade", "tipo", "descricao"]
        widgets = {
            "oportunidade": forms.Select(attrs={"class": "form-select"}),
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "descricao": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
