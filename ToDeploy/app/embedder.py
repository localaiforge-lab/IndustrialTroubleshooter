"""DistilUSE ONNX embedder – same vocab / dims as the mobile app."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import onnxruntime as ort


class WordPieceTokenizer:
    def __init__(self, vocab_path: Path, do_lower_case: bool = False):
        self.do_lower_case = do_lower_case
        self.vocab: dict[str, int] = {}
        for i, line in enumerate(vocab_path.read_text(encoding="utf-8").splitlines()):
            tok = line.strip()
            if tok:
                self.vocab[tok] = i
        self.cls_id = self.vocab.get("[CLS]", 101)
        self.sep_id = self.vocab.get("[SEP]", 102)
        self.pad_id = self.vocab.get("[PAD]", 0)
        self.unk_id = self.vocab.get("[UNK]", 100)

    def encode(self, text: str, max_length: int = 128) -> tuple[list[int], list[int]]:
        s = " ".join(text.strip().split())
        if self.do_lower_case:
            s = s.lower()
        ids = [self.cls_id]
        for word in (w for w in s.split(" ") if w):
            ids.extend(self._word_piece(word))
        ids.append(self.sep_id)
        if len(ids) > max_length:
            ids = ids[:max_length]
            ids[-1] = self.sep_id
        mask = [1] * len(ids)
        while len(ids) < max_length:
            ids.append(self.pad_id)
            mask.append(0)
        return ids, mask

    def _word_piece(self, word: str) -> list[int]:
        if word in self.vocab:
            return [self.vocab[word]]
        chars = list(word)
        start = 0
        pieces: list[int] = []
        while start < len(chars):
            end = len(chars)
            cur_id = None
            while start < end:
                sub = "".join(chars[start:end])
                if start > 0:
                    sub = "##" + sub
                if sub in self.vocab:
                    cur_id = self.vocab[sub]
                    break
                end -= 1
            if cur_id is None:
                return [self.unk_id]
            pieces.append(cur_id)
            start = end
        return pieces


class Embedder:
    def __init__(self, onnx_path: Path, vocab_path: Path):
        if not onnx_path.exists():
            raise FileNotFoundError(f"Missing embedding ONNX: {onnx_path}")
        if not vocab_path.exists():
            raise FileNotFoundError(f"Missing vocab: {vocab_path}")
        self._session = ort.InferenceSession(
            str(onnx_path), providers=["CPUExecutionProvider"]
        )
        self._tokenizer = WordPieceTokenizer(vocab_path, do_lower_case=False)
        self.dimensions = 512

    def embed(self, text: str) -> np.ndarray:
        ids, mask = self._tokenizer.encode(text)
        feeds = {
            "input_ids": np.array([ids], dtype=np.int64),
            "attention_mask": np.array([mask], dtype=np.int64),
        }
        out = self._session.run(["sentence_embedding"], feeds)[0][0]
        vec = np.asarray(out, dtype=np.float32)
        n = float(np.linalg.norm(vec))
        if n > 0:
            vec = vec / n
        return vec
