"""Load RAG1 prebuilt_index.bin produced by scripts/prebuild_llm_pack_index.py."""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from pathlib import Path

import numpy as np

MAGIC = b"RAG1"


@dataclass
class Chunk:
    id: str
    document_id: str
    document_title: str
    chunk_index: int
    text: str
    embedding: np.ndarray
    metadata_json: str


@dataclass
class DocumentPack:
    document_id: str
    title: str
    embedding_model_id: str
    dimensions: int
    chunks: list[Chunk]

    @property
    def matrix(self) -> np.ndarray:
        if not self.chunks:
            return np.zeros((0, self.dimensions), dtype=np.float32)
        return np.stack([c.embedding for c in self.chunks], axis=0)


def _read_cstring(buf: memoryview, offset: int) -> tuple[str, int]:
    (length,) = struct.unpack_from("<I", buf, offset)
    offset += 4
    raw = bytes(buf[offset : offset + length])
    offset += length
    return raw.decode("utf-8"), offset


def load_prebuilt_index(path: Path) -> DocumentPack:
    data = path.read_bytes()
    view = memoryview(data)
    if bytes(view[:4]) != MAGIC:
        raise ValueError(f"Bad magic in {path}")
    offset = 4
    format_version, dims, count = struct.unpack_from("<III", view, offset)
    offset += 12
    if format_version != 1:
        raise ValueError(f"Unsupported format {format_version}")

    embedding_model_id, offset = _read_cstring(view, offset)
    document_id, offset = _read_cstring(view, offset)
    title, offset = _read_cstring(view, offset)

    chunks: list[Chunk] = []
    for _ in range(count):
        chunk_id, offset = _read_cstring(view, offset)
        (chunk_index,) = struct.unpack_from("<I", view, offset)
        offset += 4
        text, offset = _read_cstring(view, offset)
        metadata_json, offset = _read_cstring(view, offset)
        nbytes = dims * 4
        emb = np.frombuffer(view[offset : offset + nbytes], dtype="<f4").astype(
            np.float32, copy=True
        )
        offset += nbytes
        chunks.append(
            Chunk(
                id=chunk_id,
                document_id=document_id,
                document_title=title,
                chunk_index=chunk_index,
                text=text,
                embedding=emb,
                metadata_json=metadata_json,
            )
        )

    return DocumentPack(
        document_id=document_id,
        title=title,
        embedding_model_id=embedding_model_id,
        dimensions=dims,
        chunks=chunks,
    )


def load_manifest(materials_dir: Path) -> list[dict]:
    manifest_path = materials_dir / "materials_manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    return list(data.get("materials") or [])
