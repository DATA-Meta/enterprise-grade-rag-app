"""
Evaluation suite using DeepEval, scoring the real pipeline's answers on 5 metrics:
- Faithfulness: does the answer only use information from retrieved context?
- Answer Relevancy: does the answer actually address the question asked?
- Contextual Precision: are the most relevant chunks ranked highest?
- Contextual Recall: does the retrieved context contain everything needed
  to produce the expected answer?
- Answer Correctness: does the answer match the expected ground truth,
  factually? (via GEval, DeepEval's custom-criteria judge)

Run with: python -m tests.run_evals
"""

from langchain_openai import ChatOpenAI
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from openai import RateLimitError

from deepeval import evaluate
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    GEval,
)
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.models.base_model import DeepEvalBaseLLM

from src.utils.config import settings
from src.retrieval.retriever import retrieve
from src.retrieval.reranker import rerank
from src.gateway.llm import generate_answer
from tests.eval_dataset import EVAL_QUESTIONS


class GroqViaPortkeyModel(DeepEvalBaseLLM):
    """
    Wraps our existing Groq-via-Portkey setup so DeepEval can use it as the
    judge model, instead of defaulting to OpenAI.

    Includes automatic retry with exponential backoff, since Groq's free
    tier has a fairly low tokens-per-minute limit that's easy to hit when
    running several metrics back-to-back.
    """

    def __init__(self):
        self.model = ChatOpenAI(
            model="llama-3.3-70b-versatile",
            base_url="https://api.portkey.ai/v1",
            api_key="not-needed-using-portkey",
            default_headers={
                "x-portkey-api-key": settings.portkey_api_key,
                "x-portkey-virtual-key": settings.groq_virtual_key,
            },
        )

    def load_model(self):
        return self.model

    @retry(
        retry=retry_if_exception_type(RateLimitError),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(5),
    )
    def generate(self, prompt: str) -> str:
        return self.model.invoke(prompt).content

    @retry(
        retry=retry_if_exception_type(RateLimitError),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(5),
    )
    async def a_generate(self, prompt: str) -> str:
        response = await self.model.ainvoke(prompt)
        return response.content

    def get_model_name(self) -> str:
        return "llama-3.3-70b-versatile (via Portkey/Groq)"


def run_pipeline_for_eval(question: str):
    """
    Run retrieval + reranking + generation (skipping guardrails, since
    we're evaluating answer quality on known-good questions here).
    """
    initial_chunks = retrieve(question, top_k=5)
    chunks = rerank(question, initial_chunks, top_k=3)
    contexts = [chunk.text for chunk in chunks]
    context_text = "\n\n".join(contexts)
    answer = generate_answer(question, context_text)
    return answer, contexts


def main():
    judge_model = GroqViaPortkeyModel()

    metrics = [
        FaithfulnessMetric(model=judge_model, threshold=0.5, async_mode=False),
        AnswerRelevancyMetric(model=judge_model, threshold=0.5, async_mode=False),
        ContextualPrecisionMetric(model=judge_model, threshold=0.5, async_mode=False),
        ContextualRecallMetric(model=judge_model, threshold=0.5, async_mode=False),
        GEval(
            name="Answer Correctness",
            criteria=(
                "Determine whether the actual output is factually correct "
                "and consistent with the expected output, even if worded "
                "differently."
            ),
            evaluation_params=[
                LLMTestCaseParams.ACTUAL_OUTPUT,
                LLMTestCaseParams.EXPECTED_OUTPUT,
            ],
            model=judge_model,
            threshold=0.5,
            async_mode=False,
        ),
    ]

    test_cases = []
    for item in EVAL_QUESTIONS:
        answer, contexts = run_pipeline_for_eval(item["question"])
        test_case = LLMTestCase(
            input=item["question"],
            actual_output=answer,
            expected_output=item["ground_truth"],
            retrieval_context=contexts,
        )
        test_cases.append(test_case)

        print(f"\nQuestion: {item['question']}")
        print(f"Answer: {answer}")

    print("\n--- Running evaluation (5 metrics) ---")
    evaluate(test_cases, metrics)


if __name__ == "__main__":
    main()