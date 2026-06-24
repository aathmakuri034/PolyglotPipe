"""Ingestion node (fan-out by file type).

PURPOSE
    Entry point of the graph. Inspects each incoming file and routes it to the
    right loader: audio -> Whisper, pdf -> OCR, image -> Tesseract, text -> read.

WHAT TO BUILD HERE
    - A node function that reads from / writes to the shared graph state.
    - File-type detection and dispatch to the correct document loader.
    - Emit LangChain Document objects with metadata (see Contract 1).
"""
