import anthropic
from app.config import settings
from typing import List, Tuple

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are DocuMind AI, an expert document analyst.
Answer questions based ONLY on the provided document context.
If the answer is not in the context, say "I couldn't find that in the document."
Be concise, accurate, and cite relevant parts of the context."""

def ask_question(question: str, context_chunks: List[str]) -> Tuple[str, int]:
    """Send question + context to Claude and return (answer, tokens_used)."""
    context = "\n\n---\n\n".join(context_chunks)
    
    user_message = f"""Here is the relevant document context:

{context}

---

Question: {question}

Please answer based on the context above."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}]
    )
    
    answer = response.content[0].text
    tokens = response.usage.input_tokens + response.usage.output_tokens
    return answer, tokens

async def generate_summary(text_sample: str) -> str:
    """Generate a brief document summary."""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": f"Summarize this document in 3 sentences:\n\n{text_sample[:3000]}"
        }]
    )
    return response.content[0].text