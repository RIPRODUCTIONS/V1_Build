from __future__ import annotations

from typing import Any

from app.automation.registry import skill


@skill('documents.ocr_scan')
async def ocr_scan(context: dict[str, Any]) -> dict[str, Any]:
    # Placeholder OCR result
    files = context.get('files') or []
    return {**context, 'ocr_text': [f'text-from-{i}' for i, _ in enumerate(files)]}


@skill('documents.classify')
async def classify(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, 'doc_classes': ['invoice' for _ in context.get('ocr_text', [])]}


@skill('documents.layout_analyze')
async def layout_analyze(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, 'layout': {'blocks': len(context.get('ocr_text', []))}}


@skill('documents.extract_text')
async def extract_text(context: dict[str, Any]) -> dict[str, Any]:
    # In real impl, merge OCR lines; here pass through
    return {**context, 'extracted_text': '\n'.join(context.get('ocr_text', []))}
