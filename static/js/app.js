document.addEventListener("DOMContentLoaded", function () {

    // CONFIRM BUTTON
    document.querySelectorAll("[data-confirm]").forEach(function (btn) {
        btn.addEventListener("click", function (e) {
            if (!confirm(btn.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    // MASK CNPJ
    function maskCNPJ(value) {
        value = value.replace(/\D/g, '');
        value = value.replace(/^(\d{2})(\d)/, '$1.$2');
        value = value.replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3');
        value = value.replace(/\.(\d{3})(\d)/, '.$1/$2');
        value = value.replace(/(\d{4})(\d)/, '$1-$2');
        return value;
    }

    const cnpjInput = document.querySelector('#id_cnpj_cpf');
    const telefoneInput = document.querySelector('#id_telefone');

    if (cnpjInput) {
        cnpjInput.setAttribute('maxlength', '18');
        cnpjInput.setAttribute('placeholder', '00.000.000/0000-00');

        cnpjInput.addEventListener('input', function (e) {
            e.target.value = maskCNPJ(e.target.value);
        });
    }

    if (telefoneInput) {
        telefoneInput.setAttribute('maxlength', '15'); // melhor 15 para telefone BR
        telefoneInput.setAttribute('placeholder', '(00) 00000-0000');

        telefoneInput.addEventListener('input', function (e) {
            let value = e.target.value.replace(/\D/g, '');

            if (value.length > 10) {
                value = value.replace(/^(\d{2})(\d{5})(\d{4})$/, '($1) $2-$3');
            } else if (value.length > 6) {
                value = value.replace(/^(\d{2})(\d{4})(\d{0,4})$/, '($1) $2-$3');
            } else if (value.length > 2) {
                value = value.replace(/^(\d{2})(\d{0,5})$/, '($1) $2');
            } else if (value.length > 0) {
                value = value.replace(/^(\d{0,2})$/, '($1');
            }

            e.target.value = value;
        });
    }

});