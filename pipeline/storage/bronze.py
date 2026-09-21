"""Bronze Storage Layer: Raw, immutable blob and file ingestion.

Stores original unparsed inputs (PDFs, raw CSV files, JSON payloads) alongside
cryptographic SHA-256 hashes and metadata to ensure 100% auditability and enable
re-processing whenever extraction models or parsing heuristics improve.
"""

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO, Optional, Union

from pipeline.models import SourceType

DEFAULT_BRONZE_DIR = Path("data/bronze")
DEFAULT_MANIFEST_PATH = DEFAULT_BRONZE_DIR / "manifest.json"


class BronzeStorage:
    """Manages raw immutable file storage and receipt generation."""

    def __init__(self, base_dir: Path = DEFAULT_BRONZE_DIR):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.base_dir / "manifest.json"
        self._init_manifest()

    def _init_manifest(self) -> None:
        if not self.manifest_path.exists():
            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _compute_sha256(self, content_bytes: bytes) -> str:
        hasher = hashlib.sha256()
        hasher.update(content_bytes)
        return hasher.hexdigest()

    def ingest_raw_file(
        self,
        file_or_bytes: Union[bytes, BinaryIO, str, Path],
        filename: str,
        source: SourceType,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Store raw byte payload immutably into bronze partitioned directory."""
        if isinstance(file_or_bytes, (str, Path)):
            with open(file_or_bytes, "rb") as f:
                content = f.read()
        elif isinstance(file_or_bytes, bytes):
            content = file_or_bytes
        else:
            content = file_or_bytes.read()
            if hasattr(file_or_bytes, "seek"):
                file_or_bytes.seek(0)

        sha256_hash = self._compute_sha256(content)
        now = datetime.now(timezone.utc)
        date_partition = now.strftime("%Y/%m/%d")

        target_dir = self.base_dir / source.value / date_partition
        target_dir.mkdir(parents=True, exist_ok=True)

        target_path = target_dir / f"{sha256_hash[:12]}_{filename}"
        with open(target_path, "wb") as f:
            f.write(content)

        receipt = {
            "file_id": f"{source.value}_{sha256_hash[:12]}",
            "original_filename": filename,
            "source": source.value,
            "sha256": sha256_hash,
            "stored_path": str(target_path),
            "size_bytes": len(content),
            "ingested_at_utc": now.isoformat(),
            "metadata": metadata or {},
        }

        # Append to manifest
        self._record_manifest(receipt)
        return receipt

    def _record_manifest(self, receipt: dict) -> None:
        with open(self.manifest_path, "r+", encoding="utf-8") as f:
            records = json.load(f)
            records.append(receipt)
            f.seek(0)
            json.dump(records, f, indent=2)

    def list_raw_files(self, source: Optional[SourceType] = None) -> list[dict]:
        if not self.manifest_path.exists():
            return []
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            records = json.load(f)
        if source:
            return [r for r in records if r.get("source") == source.value]
        return records
