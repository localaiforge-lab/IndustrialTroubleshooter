# Models (GGUF)

Ide kerül a szerver LLM súlya. Példa fájlnév:

`qwen2.5-1.5b-instruct-q4_k_m.gguf`

Majd állítsd:

```bash
export LLM_MODEL_PATH=/abszolút/út/qwen2.5-1.5b-instruct-q4_k_m.gguf
```

Docker / Cloud Run: a `Dockerfile` alapból  
`/app/models/qwen2.5-1.5b-instruct-q4_k_m.gguf` útvonalat várja  
(vagy mountold a `models/` mappát futáskor).

Letöltés: lásd a szülő [`../README.md`](../README.md) „Qwen GGUF letöltése” szekcióját.

**Fontos:** MediaPipe `.task` fájl ide **nem** kell – a szerver GGUF-et használ.
