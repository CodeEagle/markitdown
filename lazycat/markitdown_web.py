import argparse
import io
import os
from pathlib import Path

import uvicorn
from markitdown import MarkItDown, StreamInfo
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route


DEFAULT_MAX_UPLOAD_BYTES = 25 * 1024 * 1024


def plugins_enabled() -> bool:
    return os.getenv("MARKITDOWN_ENABLE_PLUGINS", "false").strip().lower() in (
        "true",
        "1",
        "yes",
    )


def max_upload_bytes() -> int:
    raw_value = os.getenv("MARKITDOWN_MAX_UPLOAD_BYTES", "").strip()
    if not raw_value:
        return DEFAULT_MAX_UPLOAD_BYTES

    try:
        return int(raw_value)
    except ValueError:
        return DEFAULT_MAX_UPLOAD_BYTES


def build_converter() -> MarkItDown:
    return MarkItDown(enable_plugins=plugins_enabled())


def response_payload(*, markdown: str, source: str, source_type: str, filename: str | None) -> dict:
    return {
        "ok": True,
        "source": source,
        "source_type": source_type,
        "filename": filename,
        "markdown": markdown,
    }


def wants_plain_text(request: Request) -> bool:
    if request.query_params.get("format", "").strip().lower() == "text":
        return True

    accept = request.headers.get("accept", "")
    return "text/plain" in accept and "application/json" not in accept


def markdown_name(source_name: str | None) -> str:
    if not source_name:
        return "markitdown-output.md"

    source_path = Path(source_name)
    if source_path.suffix:
        return f"{source_path.stem}.md"

    return f"{source_path.name}.md"


def json_error(message: str, status_code: int) -> JSONResponse:
    return JSONResponse({"ok": False, "error": message}, status_code=status_code)


def validate_content_length(request: Request) -> JSONResponse | None:
    content_length = request.headers.get("content-length")
    if not content_length:
        return None

    try:
        if int(content_length) > max_upload_bytes():
            limit_mb = max_upload_bytes() // (1024 * 1024)
            return json_error(f"Uploaded payload is too large. Limit: {limit_mb} MB.", 413)
    except ValueError:
        return json_error("Invalid Content-Length header.", 400)

    return None


async def healthz(_: Request) -> JSONResponse:
    return JSONResponse({"ok": True, "service": "markitdown-web"})


async def convert(request: Request):
    oversized = validate_content_length(request)
    if oversized is not None:
        return oversized

    try:
        converter = build_converter()
        content_type = request.headers.get("content-type", "")

        if content_type.startswith("application/json"):
            payload = await request.json()
            uri = str(payload.get("uri", "")).strip()
            if not uri:
                return json_error("Missing required field: uri", 400)

            result = converter.convert_uri(uri)
            response = response_payload(
                markdown=result.markdown,
                source=uri,
                source_type="uri",
                filename=markdown_name(uri),
            )
        else:
            form = await request.form()
            uri = str(form.get("uri", "")).strip()
            upload = form.get("file")

            if upload is not None and getattr(upload, "filename", ""):
                upload_bytes = await upload.read()
                if len(upload_bytes) > max_upload_bytes():
                    limit_mb = max_upload_bytes() // (1024 * 1024)
                    return json_error(f"Uploaded file is too large. Limit: {limit_mb} MB.", 413)

                extension = Path(upload.filename).suffix or None
                stream_info = StreamInfo(
                    filename=upload.filename,
                    extension=extension,
                    mimetype=(upload.content_type or None),
                )
                result = converter.convert_stream(
                    io.BytesIO(upload_bytes),
                    stream_info=stream_info,
                )
                response = response_payload(
                    markdown=result.markdown,
                    source=upload.filename,
                    source_type="upload",
                    filename=markdown_name(upload.filename),
                )
            elif uri:
                result = converter.convert_uri(uri)
                response = response_payload(
                    markdown=result.markdown,
                    source=uri,
                    source_type="uri",
                    filename=markdown_name(uri),
                )
            else:
                return json_error("Provide either a uri field or a file upload.", 400)

        if wants_plain_text(request):
            return PlainTextResponse(
                response["markdown"],
                headers={"content-disposition": f'inline; filename="{response["filename"]}"'},
            )

        return JSONResponse(response)
    except Exception as exc:
        return json_error(str(exc), 500)


app = Starlette(
    debug=False,
    routes=[
        Route("/healthz", healthz),
        Route("/api/convert", convert, methods=["POST"]),
    ],
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the MarkItDown web service")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=3000, help="Port to listen on")
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
