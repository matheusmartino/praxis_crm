"""
Middleware global de captura de exceções.

Registra no log todas as exceções não tratadas com contexto completo
(usuário, IP, path, método HTTP) antes de repropagar para o handler500.

NÃO engole exceções — apenas loga e relança.

FUTURO — request_id correlation:
  Para rastrear uma requisição ponta-a-ponta nos logs, ativar um
  RequestIDMiddleware (antes deste) que injete request.id (uuid4)
  e adicione um logging.Filter que insira request_id em cada registro.
  Exemplo de filter:
      class RequestIdFilter(logging.Filter):
          def filter(self, record):
              record.request_id = getattr(threading.local(), 'request_id', '-')
              return True
"""

import logging

logger = logging.getLogger("praxis.seguranca")


class GlobalExceptionMiddleware:
    """Captura exceções não tratadas e registra contexto completo no log."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        """Loga a exceção com contexto e repropaga para handler500."""
        user = getattr(request, "user", None)
        username = getattr(user, "username", "anonymous") if user else "anonymous"

        logger.exception(
            "Exceção não tratada: user=%s ip=%s path=%s method=%s — %s",
            username,
            _get_client_ip(request),
            request.path,
            request.method,
            str(exception),
        )

        # Retorna None para repropagar a exceção ao handler500 do Django
        return None


def _get_client_ip(request):
    """Extrai IP do cliente, respeitando proxy reverso (X-Forwarded-For)."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")
