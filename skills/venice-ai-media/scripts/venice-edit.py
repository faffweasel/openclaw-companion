#!/usr/bin/env python3
"""Edit images via Venice AI Image Edit API."""

import argparse
import datetime as dt
import io
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Import shared utilities
sys.path.insert(0, str(Path(__file__).parent))
from venice_common import (
    require_api_key,
    list_models,
    print_models,
    validate_model,
    print_media_line,
    get_mime_type,
    USER_AGENT,
    API_BASE,
)

DEFAULT_MODEL = "seedream-v4-edit"


def edit_image_from_file(
    api_key: str,
    image_path: Path,
    prompt: str,
    model_id: str = DEFAULT_MODEL,
    aspect_ratio: str | None = None,
) -> bytes:
    """
    Edit an image via Venice API using multipart file upload.
    Returns raw image bytes.
    """
    url = f"{API_BASE}/image/edit"
    
    # Build multipart form data
    boundary = "----VeniceEditBoundary"
    
    # Read image
    image_data = image_path.read_bytes()
    filename = image_path.name
    mime = get_mime_type(filename)
    
    body = io.BytesIO()
    
    # Add image file
    body.write(f'--{boundary}\r\n'.encode())
    body.write(f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'.encode())
    body.write(f'Content-Type: {mime}\r\n\r\n'.encode())
    body.write(image_data)
    body.write(b'\r\n')
    
    # Add prompt
    body.write(f'--{boundary}\r\n'.encode())
    body.write(b'Content-Disposition: form-data; name="prompt"\r\n\r\n')
    body.write(prompt.encode())
    body.write(b'\r\n')
    
    # Add model ID
    body.write(f'--{boundary}\r\n'.encode())
    body.write(b'Content-Disposition: form-data; name="modelId"\r\n\r\n')
    body.write(model_id.encode())
    body.write(b'\r\n')
    
    # Add aspect ratio if specified
    if aspect_ratio:
        body.write(f'--{boundary}\r\n'.encode())
        body.write(b'Content-Disposition: form-data; name="aspect_ratio"\r\n\r\n')
        body.write(aspect_ratio.encode())
        body.write(b'\r\n')
    
    # End boundary
    body.write(f'--{boundary}--\r\n'.encode())
    
    req = urllib.request.Request(
        url,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": USER_AGENT,
        },
        data=body.getvalue(),
    )
    
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Venice API error ({e.code}): {error_body}") from e


def edit_image_from_url(
    api_key: str,
    image_url: str,
    prompt: str,
    model_id: str = DEFAULT_MODEL,
    aspect_ratio: str | None = None,
) -> bytes:
    """
    Edit an image via Venice API using a URL.
    Returns raw image bytes.
    """
    
    url = f"{API_BASE}/image/edit"
    
    payload = {
        "image": image_url,
        "prompt": prompt,
        "modelId": model_id,
    }
    
    if aspect_ratio:
        payload["aspect_ratio"] = aspect_ratio
    
    body = json.dumps(payload).encode("utf-8")
    
    req = urllib.request.Request(
        url,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
        data=body,
    )
    
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Venice API error ({e.code}): {error_body}") from e


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Edit images via Venice AI API. The AI interprets your prompt to determine what to modify."
    )
    ap.add_argument("image", nargs="?", help="Path to image file to edit (positional)")
    ap.add_argument("--input", dest="input_flag", help="Path to image file to edit (named flag, IMAGE_EDIT_CMD compatible)")
    ap.add_argument("--url", help="URL of image to edit (http:// or https://)")
    ap.add_argument("--prompt", "-p", help="Edit instructions (e.g., 'add sunglasses', 'change sky to sunset')")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"Model ID (default: {DEFAULT_MODEL})")
    ap.add_argument("--aspect-ratio", help="Output aspect ratio (auto, 1:1, 3:2, 16:9, 21:9, 9:16, 2:3, 3:4, 4:5)")
    ap.add_argument("--out-dir", help="Output directory (default: same as input or current dir for URLs)")
    ap.add_argument("--output", "-o", help="Output filename (default: auto-generated)")
    ap.add_argument("--list-models", action="store_true", help="List available edit/inpaint models and exit")
    ap.add_argument("--no-validate", action="store_true", help="Skip model validation")
    args = ap.parse_args()

    api_key = require_api_key()

    # Handle --list-models
    if args.list_models:
        try:
            models = list_models(api_key, "inpaint")
            print_models(models)
            return 0
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    # Prompt is required for editing
    if not args.prompt:
        print("Error: --prompt is required for editing", file=sys.stderr)
        return 2

    # Resolve input: --input flag takes priority over positional
    args.image = args.input_flag or args.image

    # Validate input
    if not args.image and not args.url:
        print("Error: Either image path or --url is required", file=sys.stderr)
        return 2
    if args.image and args.url:
        print("Error: Provide either image path or --url, not both", file=sys.stderr)
        return 2

    # Validate model if not skipped
    if not args.no_validate:
        exists, available = validate_model(api_key, args.model, "inpaint")
        if not exists and available:
            print(f"Error: Model '{args.model}' not found or unavailable.", file=sys.stderr)
            print(f"Available edit models: {', '.join(available)}", file=sys.stderr)
            return 2
    
    # Handle URL input
    if args.url:
        if not args.url.startswith(("http://", "https://")):
            print("Error: URL must start with http:// or https://", file=sys.stderr)
            return 2
        
        # Determine output path for URL input
        if args.output:
            out_path = Path(args.output).expanduser()
        else:
            out_dir = Path(args.out_dir).expanduser() if args.out_dir else Path.cwd()
            out_dir.mkdir(parents=True, exist_ok=True)
            timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
            out_path = out_dir / f"edited-{timestamp}.png"
        
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"Editing: {args.url[:60]}{'...' if len(args.url) > 60 else ''}")
        print(f"  Model: {args.model}")
        print(f"  Prompt: {args.prompt[:80]}{'...' if len(args.prompt) > 80 else ''}")
        
        try:
            result = edit_image_from_url(
                api_key=api_key,
                image_url=args.url,
                prompt=args.prompt,
                model_id=args.model,
                aspect_ratio=args.aspect_ratio,
            )
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    else:
        # Handle file input
        image_path = Path(args.image).expanduser()
        if not image_path.exists():
            print(f"Error: Image not found: {image_path}", file=sys.stderr)
            return 2
        
        # Determine output path
        if args.output:
            out_path = Path(args.output).expanduser()
        else:
            out_dir = Path(args.out_dir).expanduser() if args.out_dir else image_path.parent
            out_dir.mkdir(parents=True, exist_ok=True)
            timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
            suffix = image_path.suffix or ".png"
            out_path = out_dir / f"{image_path.stem}-edited-{timestamp}{suffix}"
        
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"Editing: {image_path.name}")
        print(f"  Model: {args.model}")
        print(f"  Prompt: {args.prompt[:80]}{'...' if len(args.prompt) > 80 else ''}")
        
        try:
            result = edit_image_from_file(
                api_key=api_key,
                image_path=image_path,
                prompt=args.prompt,
                model_id=args.model,
                aspect_ratio=args.aspect_ratio,
            )
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    
    out_path.write_bytes(result)
    print(f"\nSaved: {out_path.as_posix()}")
    print(f"Size: {len(result) / 1024:.1f}KB")
    
    print_media_line(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
