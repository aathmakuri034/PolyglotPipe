"""Translation chain (Gemini Flash-Lite).

PURPOSE
    Translate extracted text into the target language while preserving meaning
    and domain terminology. The most-used chain in the pipeline.

WHAT TO BUILD HERE
    - A prompt template for source_lang -> target_lang translation.
    - A chain that takes a TranslationProvider (not Gemini directly) so the
      local fallback can be swapped in.
    - Output parsing into clean translated text + confidence.
"""
