import asyncio
import logging
from typing import Any, Dict, List, Optional

import boto3

from app.config import settings


logger = logging.getLogger(__name__)


class TextractService:
    """AWS Textract helper for OCR of scanned PDFs/images stored in S3.

    Prefers async job for multi-page PDFs; falls back to AnalyzeDocument for images/short docs.
    Returns plain text with basic table formatting when available.
    """

    def __init__(self) -> None:
        self.client = boto3.client(
            "textract",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )

    async def _run(self, func, *args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    async def extract_text_s3(
        self,
        bucket: str,
        key: str,
        *,
        include_tables: bool = True,
        max_pages: int = 200,
        poll_interval: float = 2.0,
        timeout_seconds: int = 300,
    ) -> str:
        try:
            # Try synchronous AnalyzeDocument for images or short docs
            feature_types = ["TABLES", "FORMS"] if include_tables else ["FORMS"]
            try:
                result = await self._run(
                    self.client.analyze_document,
                    Document={"S3Object": {"Bucket": bucket, "Name": key}},
                    FeatureTypes=feature_types,
                )
                text = self._blocks_to_text(result.get("Blocks", []), include_tables)
                if text and len(text) > 1000:
                    return text
            except Exception as e:
                logger.info(f"AnalyzeDocument not suitable for {key}: {e}")

            # Fallback to async TextDetection for multi-page docs (PDF in S3)
            start_resp = await self._run(
                self.client.start_document_text_detection,
                DocumentLocation={"S3Object": {"Bucket": bucket, "Name": key}},
            )
            job_id = start_resp.get("JobId")
            if not job_id:
                return ""

            pages: List[str] = []
            elapsed = 0.0
            next_token: Optional[str] = None
            while elapsed < timeout_seconds and len(pages) < max_pages:
                status_resp = await self._run(self.client.get_document_text_detection, JobId=job_id, NextToken=next_token) if next_token else await self._run(self.client.get_document_text_detection, JobId=job_id)
                status = status_resp.get("JobStatus")
                if status in {"SUCCEEDED", "FAILED"}:
                    if status == "FAILED":
                        logger.warning(f"Textract job failed for {key}")
                        break
                    # Collect all pages by grouping Blocks on Page attribute
                    next_token = status_resp.get("NextToken")
                    blocks = status_resp.get("Blocks", [])
                    by_page: Dict[int, List[Dict[str, Any]]] = {}
                    for b in blocks:
                        p = int(b.get("Page", 1))
                        by_page.setdefault(p, []).append(b)
                    for p in sorted(by_page.keys()):
                        page_text = self._blocks_to_text(by_page[p], include_tables=False)
                        if page_text:
                            pages.append(page_text)
                    if not next_token:
                        break
                else:
                    await asyncio.sleep(poll_interval)
                    elapsed += poll_interval
            return "\n\n".join(pages)
        except Exception as e:
            logger.error(f"Textract extraction error for s3://{bucket}/{key}: {e}")
            return ""

    async def extract_pages_s3(
        self,
        bucket: str,
        key: str,
        *,
        include_tables: bool = True,
        max_pages: int = 200,
        poll_interval: float = 2.0,
        timeout_seconds: int = 300,
    ) -> List[Dict[str, Any]]:
        """Return structured pages with Markdown content for each page."""
        try:
            # Try AnalyzeDocument as single-page content
            feature_types = ["TABLES", "FORMS"] if include_tables else ["FORMS"]
            try:
                result = await self._run(
                    self.client.analyze_document,
                    Document={"S3Object": {"Bucket": bucket, "Name": key}},
                    FeatureTypes=feature_types,
                )
                text = self._blocks_to_text(result.get("Blocks", []), include_tables)
                if text:
                    return [{"index": 1, "markdown": text}]
            except Exception:
                pass

            # Async detection by page
            start_resp = await self._run(
                self.client.start_document_text_detection,
                DocumentLocation={"S3Object": {"Bucket": bucket, "Name": key}},
            )
            job_id = start_resp.get("JobId")
            if not job_id:
                return []
            pages_md: Dict[int, str] = {}
            elapsed = 0.0
            next_token: Optional[str] = None
            while elapsed < timeout_seconds and len(pages_md) < max_pages:
                status_resp = await self._run(self.client.get_document_text_detection, JobId=job_id, NextToken=next_token) if next_token else await self._run(self.client.get_document_text_detection, JobId=job_id)
                status = status_resp.get("JobStatus")
                if status in {"SUCCEEDED", "FAILED"}:
                    if status == "FAILED":
                        break
                    next_token = status_resp.get("NextToken")
                    blocks = status_resp.get("Blocks", [])
                    by_page: Dict[int, List[Dict[str, Any]]] = {}
                    for b in blocks:
                        p = int(b.get("Page", 1))
                        by_page.setdefault(p, []).append(b)
                    for p in by_page:
                        md = self._blocks_to_text(by_page[p], include_tables=False)
                        if md:
                            pages_md[p] = (pages_md.get(p, "") + ("\n" if pages_md.get(p) else "") + md).strip()
                    if not next_token:
                        break
                else:
                    await asyncio.sleep(poll_interval)
                    elapsed += poll_interval
            return [{"index": i, "markdown": pages_md[i]} for i in sorted(pages_md.keys())]
        except Exception as e:
            logger.error(f"Textract pages extraction error for s3://{bucket}/{key}: {e}")
            return []

    def _blocks_to_text(self, blocks: List[Dict[str, Any]], include_tables: bool) -> str:
        try:
            lines: List[str] = []
            if include_tables:
                # Very simple table rendering: concatenate CELL texts row-wise
                table_cells: Dict[str, Dict[int, Dict[int, str]]] = {}
                block_map = {b.get("Id"): b for b in blocks}
                for b in blocks:
                    if b.get("BlockType") == "TABLE":
                        table_cells[b["Id"]] = {}
                for b in blocks:
                    if b.get("BlockType") == "CELL":
                        table_id = None
                        for rel in b.get("Relationships", []) or []:
                            if rel.get("Type") == "CHILD":
                                continue
                        # Find parent TABLE by ParentId if available
                        table_id = b.get("ParentId") or None
                        if table_id:
                            rows = table_cells.setdefault(table_id, {})
                            row = rows.setdefault(int(b.get("RowIndex", 0)), {})
                            row[int(b.get("ColumnIndex", 0))] = self._extract_block_text(b, block_map)
                # Append tables
                for _, rows in table_cells.items():
                    for r_idx in sorted(rows.keys()):
                        row = rows[r_idx]
                        lines.append(" | ".join(row[c] for c in sorted(row.keys())))
                    lines.append("")
            # Append lines
            for b in blocks:
                if b.get("BlockType") == "LINE":
                    text = b.get("Text") or ""
                    if text.strip():
                        lines.append(text.strip())
            return "\n".join(lines).strip()
        except Exception:
            return ""

    def _extract_block_text(self, cell_block: Dict[str, Any], block_map: Dict[str, Dict[str, Any]]) -> str:
        text_parts: List[str] = []
        for rel in cell_block.get("Relationships", []) or []:
            if rel.get("Type") == "CHILD":
                for cid in rel.get("Ids", []) or []:
                    word = block_map.get(cid)
                    if word and word.get("BlockType") in {"WORD", "SELECTION_ELEMENT"}:
                        if word.get("BlockType") == "SELECTION_ELEMENT" and word.get("SelectionStatus") == "SELECTED":
                            text_parts.append("[X]")
                        elif word.get("Text"):
                            text_parts.append(word["Text"])
        return " ".join(text_parts).strip()


textract_service = TextractService()


