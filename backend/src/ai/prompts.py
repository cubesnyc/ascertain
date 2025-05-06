from src.services.schema import AIQuestionVariantsResponse, CodeLookupAction, DocumentChunkSimilarityRead, MedicalConcept


def _stitch_lines(*lines) -> str:
    """
    Simply helper for stiching lines together to make prompt creation more readable.
    """
    return "\n".join(lines)



def get_summarize_prompt_instructions() -> str:
    """
    Get the prompt for summarizing a document.
    """
    prompt = _stitch_lines(
        "You are a worldclass document summarizer.",
        "# Task:",
        "- You will be provided with a document delineated by <Document>...</Document> tags. Summarize the document and extract key insights from it.",
        "- Include all key points, ideas, and contexts."
        "- Use professional and clear prose."
        "",
    )

    return prompt.format()

def get_summarize_prompt_input(document: str) -> str:
    """
    Get the prompt for summarizing a document.
    """
    prompt = _stitch_lines(
        "<Document>{content}</Document>",
    )

    return prompt.format(content=document)



def get_chunk_prompt_instructions(document: str) -> str:
    """
    Get the starter prompt for chunking a document. This is meant to be cached, and so will only contain the first part of the prompt to be followed by the actual chunk.
    """

    prompt = _stitch_lines(
        "You are a world-class *document context enhancer* used inside a Retrieval-Augmented Generation (RAG) pipeline.",
        "Task:",
        "- Given one full document and one extracted chunk, create concise supplemental context.",
        "",
        "Rules:",
        "- You will receive:",
        "  - A full document enclosed in <Document> tags.",
        "  - A single chunk from that document enclosed in <Chunk> tags.",
        "- Write a SHORT context string that:",
        "  * Adds named entities, dates, section headings, or key facts missing from the chunk.",
        "  * **Never** repeats text already present in the chunk.",
        "- Respond with *only* the added context wrapped in <Context> tags and nothing else. If a given chunk is self-contained return an empty string.",
        "",
        "<Document>{content}</Document>",
    )

    return prompt.format(content=document)

def get_chunk_prompt_input(chunk: str) -> str:
    """
    Get the prompt for chunking a document.
    """
    prompt = _stitch_lines(
        "",
        "<Chunk>{content}</Chunk>",
    )

    return prompt.format(content=chunk)

def get_question_variants_instructions() -> str:
    prompt = _stitch_lines(
        "You are a world-class *question variant generator* used inside a Retrieval-Augmented Generation (RAG) pipeline.",
        "Task:",
        "- Given one user question delineated by a <Question> tag, create **4 semantically different** rewrites that retrieve complementary evidence when embedded.",
        "",
        "Rules:",
        "- **Do NOT** answer the question.",
        "- Preserve intent, entities, constraints, and time periods.",
        "   - Four diversity styles, in order:",
        "   - Paraphrase with synonyms",
        "   - Focus on a core sub-aspect",
        "   - Expand with helpful context (e.g., explain acronyms)",
        "- Decompose multi-hop into a single explicit query",
        "- Each variant ≤ 25 words, ≥ 5 words.",
        "- Drop any variant sharing ≥ 75% of the original tokens.",
        ""
    )

    return prompt

def get_question_variants_input(question: str) -> str:
    prompt = _stitch_lines(
        "<Question>{question}</Question>"
    )

    return prompt.format(question=question)

def get_rag_qa_instructions() -> str:
    prompt = _stitch_lines(
        "You are a world-class evidence-grounded answer generator in a Retrieval-Augmented Generation (RAG) pipeline.",
        "",
        "## Task",
        "- Answer the user’s question **solely** using the provided evidence chunks.",
        "- Write 1–3 well-formed sentences unless more detail is unavoidable.",
        "",
        "## Input format",
        "- <Question>...</Question>: the user’s question.",
        "- <Chunks>...</Chunks>: evidence chunks, each inside <Chunk id=\"X\" document_id=\"Y\">...</Chunk>.",
        "",
        "## Rules",
        "- Use information **only from the chunks**; do *not* add outside knowledge.",
        "- If the chunks lack enough information, reply exactly: “I don’t have sufficient information to answer.”",
        "- Every id in \"citations\" must appear in square brackets in \"answer\" **and vice-versa**.",
        "- Write in clear, professional prose.",
        "",
    )

    return prompt

def get_rag_qa_input(question: str, chunks: list[DocumentChunkSimilarityRead]):
    prompt = _stitch_lines(
        "<Question>{question}</Question>",
        "<Chunks>{chunks}</Chunks>",
    )

    return prompt.format(
        question = question,
        chunks = ''.join((f"<Chunk id=\"{chunk.id}\" document_id=\"{chunk.document_id}\">{chunk.context}\n\n{chunk.chunk}</Chunk>" for chunk in chunks))
    )

def get_structured_note_instructions() -> str:
    prompt = _stitch_lines(
        "You are a world-class *clinical data extractor* used inside a Retrieval-Augmented Generation (RAG) pipeline.",
        
        "Task:",
        "- Read the single unstructured medical note delineated by a <Note> tag and translate it into a structured output defined by the attached schema.",
        "",
        
        "Rules:",
        "- "
        "- The `system` field on the SystemConcept defines which system to associate a concept with."
        "- Preserve the exact spelling/capitalisation in every `raw_name`.",
        "- Map each `raw_name` to the **best-match** preferred term in the specified coding system.",
        "- If either code or description is unknown, set that field to null.",
        "- Use an **empty array** (`[]`) for any top-level key with no entries.",
        "- Deduplicate concepts within each concept group.",
        "- Do not attach a system code to any concept. Leave that as None"
        "- Do **NOT** output markdown, comments, or any text outside the JSON object.",
        "",
    )

    return prompt

def get_structured_note_input(note: str) -> str:
    prompt = _stitch_lines(
        "<Note>{note}</Note>"
    )

    return prompt.format(note = note)

def get_structured_note_step1_instructions() -> str:
    return _stitch_lines(
        "You are a world-class *clinical data extractor* used inside a RAG pipeline.",

        "# Task:",
        "- Read the single unstructured medical note delineated by a <Note> tag.",
        "- Identify every clinical concept and represent it exactly as the attached JSON Schema.",

        "",

        "# Concept types to capture:",
        "- Patient: demographic identifiers (e.g. id, age, sex, DOB).",
        "- Condition: problems or symptoms noted but not yet confirmed diagnoses.",
        "- Diagnosis: confirmed or billed diagnoses.",
        "- Medication: any mentioned medications.",
        "- Treatment: procedures, interventions, lifestyle advice.",
        "- Observation: vital signs, laboratory or imaging results, physical-exam findings.",
        "- PlanAction: follow-ups, referrals, recommended tests or lifestyle goals.",

        "",

        "# Rules:",
        "- **ONLY** extract the `raw_text` that pertains to a clinical concept, all other fields should be null."
        "- Output **only** the JSON structure—no markdown, comments, or extra text.",
        ""
    )

def get_structured_note_step1_input(note: str) -> str:
    return _stitch_lines(
        "<Note>{note}</Note>"
    ).format(note= note)

def get_structured_note_step2_instructions() -> str:
    return _stitch_lines(
        "You are an *action-planning* agent in a Retrieval-Augmented Generation (RAG) pipeline.",
        "",

        "# Task:",
        "- Determine what tool to use to look up a concept <Concept>.",
        "",

        "# Tools:"
        "- The tool to use is determined by the type of concept as follows:",
        "  ICD10: when a concept is a Condition, Diagnosis, or Treatment",
        "  RXNORM: when a concept is a medication",
        "  null otherise",
        "",
    )

def get_structured_note_step2_input(concept: MedicalConcept) -> str:
    return _stitch_lines(
        "<Concept>{concept}</Concept>"
    ).format(concept = concept.model_dump_json())

def get_structured_note_step4_instructions() -> str:
    prompt = _stitch_lines(
        "You are the *final-merge* agent in the RAG pipeline.",

        "",

        "# Input:",
        "- A JSON array of concept objects inside a <Concepts> tag.",
        "",

        "# Task:",
        "- Using the hydrated concept objects, compile a structured note that organized and categorized all of the data.",

        "",

        "# Output formatting:",
        "- Return **only** the JSON object of the DumbStructuredNote—no markdown, comments, or extra text."
    )

    return prompt

def get_structured_note_step4_input(concepts: list[MedicalConcept]) -> str:
    return _stitch_lines(
        "<Concepts>{concepts}</Concepts>",
    ).format(
        concepts = [f"<Concept>{it.model_dump_json()}</Concept>" for it in concepts],
    )


