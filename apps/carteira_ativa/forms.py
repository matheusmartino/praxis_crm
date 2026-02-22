"""
Módulo Carteira Ativa — forms.

ContatoCarteiraForm: formulário para registrar um contato com o cliente.
Os campos cliente e responsavel são preenchidos pela view, não pelo usuário.
"""

from django import forms

from apps.carteira_ativa.models import ContatoCarteira


class ContatoCarteiraForm(forms.ModelForm):
    """
    Formulário de registro de contato.

    Campos expostos ao usuário:
      - tipo          : canal de comunicação (obrigatório)
      - observacao    : notas livres sobre o contato
      - proxima_acao_em : data para o próximo contato (opcional)

    O cliente e o responsável são injetados pela view antes de salvar.
    """

    class Meta:
        model = ContatoCarteira
        fields = ["tipo", "observacao", "proxima_acao_em"]
        widgets = {
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "observacao": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Descreva o que foi tratado neste contato...",
                }
            ),
            "proxima_acao_em": forms.DateInput(
                attrs={"class": "form-control", "type": "date"},
                format="%Y-%m-%d",
            ),
        }
        labels = {
            "tipo": "Tipo de contato",
            "observacao": "Observação",
            "proxima_acao_em": "Próxima ação em",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # tipo é obrigatório — garantia extra além da validação do model
        self.fields["tipo"].required = True
        # proxima_acao_em é opcional por padrão
        self.fields["proxima_acao_em"].required = False
