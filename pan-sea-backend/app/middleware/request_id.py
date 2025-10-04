import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that assigns a unique request ID to each incoming request and
    exposes it via request.state.request_id and the X-Request-ID response header.
    If the client provides X-Request-ID, it is propagated if it looks valid.
    """

    header_name = "X-Request-ID"

    async def dispatch(self, request: Request, call_next):
        incoming_request_id = request.headers.get(self.header_name)
        if incoming_request_id and 8 <= len(incoming_request_id) <= 128:
            request_id = incoming_request_id
        else:
            request_id = str(uuid.uuid4())

        request.state.request_id = request_id

        response: Response = await call_next(request)
        response.headers[self.header_name] = request_id
        return response


