# nli_verification_ollama.py
from __future__ import annotations
import json
import re
from dataclasses import dataclass, asdict
from typing import List, Any, Callable, Optional, Tuple

import nltk
import numpy as np
import ollama
from concurrent.futures import ThreadPoolExecutor, as_completed



# ----------------------------
# Config & Data Structures
# ----------------------------

@dataclass
class NLIOllamaModelConfig:
    """Configuration for Ollama models and clients."""
    embedding_model_name: str = 'mxbai-embed-large'
    nli_model_name: str = 'qwen3-coder:30b'
    # Host for CPU-optimized tasks like embeddings
    cpu_client_host: str = 'http://localhost:11435'
    # Host for GPU-accelerated tasks like NLI
    gpu_client_host: str = 'http://localhost:11434'

@dataclass
class Thresholds:
    entailment_support: float = 0.5
    contradiction_support: float = 0.35
    max_sim_coverage: float = 0.3
    top_k_retrieval: int = 5

@dataclass
class PassCriteria:
    min_supported_rate: float = 0.70
    max_hallucination_rate: float = 0.1
    min_coverage: float = 0.80
    zero_contradictions: bool = True  # no contradiction > 0.5

@dataclass
class EvidenceScores:
    entailment: float
    contradiction: float
    supporting_evidence: str
    conflicting_evidence: str

@dataclass
class SentenceResult:
    sentence: str
    supported: bool
    entailment: float
    contradiction: float
    supporting_evidence: Optional[str] = None
    conflicting_evidence: Optional[str] = None
    note: Optional[str] = None  # "contested" / "unsupported" reasons

@dataclass
class CoverageResult:
    coverage: float
    uncovered_chunks: int
    uncovered_examples: List[str]

@dataclass
class TopContradiction:
    sentence: Optional[str]
    evidence: Optional[str]
    score: float

@dataclass
class VerificationReport:
    supported_rate: float
    hallucination_rate: float
    contradiction_hits: int
    coverage: CoverageResult
    top_contradiction: TopContradiction
    contested: List[SentenceResult]
    unsupported: List[SentenceResult]
    per_sentence: List[SentenceResult]
    passed: bool

# ----------------------------
# NLI Prompting
# ----------------------------

NLI_SYSTEM_PROMPT = """
You are an expert linguistic analyst. Your task is to determine the logical relationship
between a "Premise" and a "Hypothesis". Classify the relationship into one of three
categories: "entailment", "contradiction", or "neutral".
- "entailment": The Hypothesis is fully supported by the Premise.
- "contradiction": The Hypothesis directly contradicts the Premise.
- "neutral": The relationship is neither a clear entailment nor a contradiction.
You MUST provide your response in a single, valid JSON object with two keys:
1. "label": Your classification ("entailment", "contradiction", or "neutral").
2. "score": Your confidence in this classification (float between 0.0 and 1.0).
Do not provide any text or explanation outside of this JSON object.
"""


# ----------------------------
# Utilities (I/O and Text Processing)
# ----------------------------

def load_text(path: str) -> str:
    """Loads text from a file."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def safe_nli(client, model, system, user):
    r = client.chat(model=model,
                    messages=[{"role":"system","content": system},
                              {"role":"user","content": user}],
                    options={"temperature":0}, stream=False)
    msg = (r.get("message") or {}).get("content","").strip()
    if not msg:
        r = client.generate(model=model, prompt=system + "\n\n" + user, stream=False)
        msg = (r.get("response") or "").strip()
    try:
        return json.loads(msg)
    except Exception:
        m = re.search(r"\{.*\}", msg, re.DOTALL)
        return json.loads(m.group(0)) if m else None

def load_draft_from_json(path: str, keys: List[str]) -> str:
    """Loads and concatenates specified keys from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    parts = []
    for k in keys:
        node = data
        for seg in k.split("."):
            node = node.get(seg, "") if isinstance(node, dict) else ""
        if isinstance(node, str):
            parts.append(node)
    text = " ".join(parts)
    return re.sub(r"\s+", " ", text).strip()


def default_transcript_cleaner(text: str) -> str:
    """Cleans transcript text by removing common artifacts."""
    text = re.sub(r"\\", " ", text)
    text = re.sub(r"\[(?:START|ENDE)\s*Transkriptionstext\]", "", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip()


def ensure_nltk_punkt() -> None:
    """Downloads the 'punkt' tokenizer model if not found."""
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt", quiet=True)


def sentence_splitter(text: str, language: str = "german") -> List[str]:
    """Splits text into sentences."""
    ensure_nltk_punkt()
    return nltk.sent_tokenize(text, language=language)


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Calculates cosine similarity between two numpy vectors."""
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))


# ----------------------------
# Ollama Client & Retriever
# ----------------------------

@dataclass
class OllamaClients:
    """Container for CPU and GPU Ollama clients."""
    cpu: ollama.Client
    gpu: ollama.Client


def build_ollama_clients(config: NLIOllamaModelConfig) -> OllamaClients:
    """Initializes and returns Ollama clients."""
    try:
        cpu_client = ollama.Client(host=config.cpu_client_host)
        gpu_client = ollama.Client(host=config.gpu_client_host)
        # Ping servers to ensure they are available
        cpu_client.list()
        gpu_client.list()
        return OllamaClients(cpu=cpu_client, gpu=gpu_client)
    except Exception as e:
        print(f"Error connecting to Ollama servers. Please ensure they are running.")
        raise e


@dataclass
class OllamaRetrieverIndex:
    """Index for semantic retrieval using Ollama embeddings."""
    chunks: List[str]
    chunk_embeddings: np.ndarray


def _get_embedding(client: ollama.Client, model_name: str, chunk: str) -> np.ndarray:
    """Helper function to get a single embedding."""
    return np.array(client.embeddings(model=model_name, prompt=chunk)['embedding'])


def build_retriever(
        chunks: List[str],
        model_name: str,
        client: ollama.Client
) -> OllamaRetrieverIndex:
    """Generates embeddings for all chunks in parallel to create a retriever index."""
    print(f"Generating embeddings for {len(chunks)} chunks using '{model_name}'...")
    embeddings = [None] * len(chunks)

    with ThreadPoolExecutor() as executor:
        # Map each chunk to a future
        future_to_index = {
            executor.submit(_get_embedding, client, model_name, chunk): i
            for i, chunk in enumerate(chunks)
        }

        for future in as_completed(future_to_index):
            index = future_to_index[future]
            try:
                embeddings[index] = future.result()
            except Exception as e:
                print(f"Could not generate embedding for chunk {index}: {e}")
                # Handle error, e.g., by creating a zero-vector
                # Note: The embedding dimension needs to be known for this.
                # For simplicity, we'll skip this chunk in case of an error.

    # Filter out any failed embeddings before converting to numpy array
    successful_embeddings = [emb for emb in embeddings if emb is not None]
    return OllamaRetrieverIndex(chunks=chunks, chunk_embeddings=np.array(successful_embeddings))

def retrieve_evidence(
        query: str,
        retr: OllamaRetrieverIndex,
        client: ollama.Client,
        model_name: str,
        top_k: int
) -> List[str]:
    """Retrieves top_k evidence chunks based on semantic similarity."""
    query_embedding = np.array(client.embeddings(model=model_name, prompt=query)['embedding'])
    sims = [cosine_similarity(query_embedding, chunk_emb) for chunk_emb in retr.chunk_embeddings]
    top_indices = sorted(range(len(sims)), key=lambda j: sims[j], reverse=True)[:top_k]
    return [retr.chunks[i] for i in top_indices]


# ----------------------------
# NLI Wrapper
# ----------------------------

def nli_scores_for_evidence(
        nli_client: ollama.Client,
        model_name: str,
        hypothesis: str,
        premises: List[str]
) -> EvidenceScores:
    """Performs NLI for a hypothesis against multiple premises using an Ollama model."""
    if not premises:
        return EvidenceScores(0.0, 0.0, "N/A", "N/A")

    max_ent, max_contra = 0.0, 0.0
    sup_ev, con_ev = "N/A", "N/A"

    for prem in premises:
        user_prompt = f'Premise: "{prem}"\n\nHypothesis: "{hypothesis}"'
        try:
            result = safe_nli(nli_client, model_name, NLI_SYSTEM_PROMPT, user_prompt)
            if not result:
                print("    - Warning: empty/invalid JSON from model; skipping premise.")
                continue

            label = str(result.get("label", "")).lower()
            score = float(result.get("score", 0.0))

            if label in {"contradicted", "contradict"}:
                label = "contradiction"

            if label == "entailment" and score > max_ent:
                max_ent, sup_ev = score, prem
            elif label == "contradiction" and score > max_contra:
                max_contra, con_ev = score, prem

        except Exception as e:
            print(f"    - Warning: NLI failed for this premise: {e}")
            continue

    return EvidenceScores(max_ent, max_contra, sup_ev, con_ev)


# ----------------------------
# Coverage Calculation
# ----------------------------

def semantic_coverage(
        transcript_chunks: List[str],
        transcript_embs: np.ndarray,
        draft_sents: List[str],
        client: ollama.Client,
        model_name: str,
        max_sim_threshold: float
) -> CoverageResult:
    """Calculates how well the draft covers the transcript."""
    if not draft_sents:
        return CoverageResult(0.0, len(transcript_chunks), transcript_chunks[:10])

    draft_embs = np.array([
        np.array(client.embeddings(model=model_name, prompt=s)['embedding'])
        for s in draft_sents
    ])

    uncovered = []
    for i, chunk_emb in enumerate(transcript_embs):
        sims = [cosine_similarity(chunk_emb, draft_emb) for draft_emb in draft_embs]
        max_sim = max(sims) if sims else 0.0
        if max_sim < max_sim_threshold:
            uncovered.append(transcript_chunks[i])

    cov = 1.0 - (len(uncovered) / max(1, len(transcript_chunks)))
    return CoverageResult(cov, len(uncovered), uncovered[:10])


# ----------------------------
# Batch Pipeline
# ----------------------------
# --- 1. Modify the System Prompt to handle lists ---
NLI_SYSTEM_PROMPT_BATCHED = """
You are an expert linguistic analyst. Your task is to determine the logical relationship
between a "Hypothesis" and a list of "Premises". For each premise, classify the relationship 
into "entailment", "contradiction", or "neutral".

You MUST provide your response in a single, valid JSON object. The object should contain a single
key "results", which is a list of objects. Each object in the list must correspond to a premise
and have three keys:
1. "premise_index": The 0-based index of the premise from the input list.
2. "label": Your classification ("entailment", "contradiction", or "neutral").
3. "score": Your confidence in this classification (float between 0.0 and 1.0).

Do not provide any text or explanation outside of this JSON object.
"""

# --- 2. Refactor the NLI function ---
def nli_scores_for_evidence_batch(
        nli_client: ollama.Client,
        model_name: str,
        hypothesis: str,
        premises: List[str]
) -> EvidenceScores:
    """Performs NLI for a hypothesis against multiple premises in a single API call."""
    if not premises:
        return EvidenceScores(0.0, 0.0, "N/A", "N/A")

    # Create a numbered list of premises for the prompt
    premise_list_str = "\\n".join([f'{i}. "{prem}"' for i, prem in enumerate(premises)])
    user_prompt = f'Hypothesis: "{hypothesis}"\\n\\nPremises:\\n{premise_list_str}'

    try:
        # Single API call for all premises
        result = safe_nli(nli_client, model_name, NLI_SYSTEM_PROMPT_BATCHED, user_prompt)
        if not result or "results" not in result:
            return EvidenceScores(0.0, 0.0, "N/A", "N/A")

        max_ent, max_contra = 0.0, 0.0
        sup_ev, con_ev = "N/A", "N/A"

        for item in result["results"]:
            label = str(item.get("label", "")).lower()
            score = float(item.get("score", 0.0))
            idx = int(item.get("premise_index", -1))

            if idx < 0 or idx >= len(premises): continue

            if label == "entailment" and score > max_ent:
                max_ent, sup_ev = score, premises[idx]
            elif label in {"contradiction", "contradicted", "contradict"} and score > max_contra:
                max_contra, con_ev = score, premises[idx]

        return EvidenceScores(max_ent, max_contra, sup_ev, con_ev)

    except Exception as e:
        print(f"    - Warning: Batched NLI failed: {e}")
        return EvidenceScores(0.0, 0.0, "N/A", "N/A")

# ----------------------------
# Core Verification Pipeline
# ----------------------------

def verify_generation_against_truth(
        ground_truth_text: str,
        generated_text: str,
        language: str,
        models: NLIOllamaModelConfig,
        threshold_to_pass: Thresholds,
        pass_criteria: PassCriteria
) -> VerificationReport:
    """Main function to verify a draft against a transcript using Ollama."""
    # 1) Setup
    clients = build_ollama_clients(models)
    cleaned = default_transcript_cleaner(ground_truth_text)
    transcript_chunks = sentence_splitter(cleaned, language=language)
    draft_sents = [s for s in sentence_splitter(generated_text, language=language) if s.strip()]

    # 2) Build Retriever
    retr = build_retriever(transcript_chunks, models.embedding_model_name, clients.cpu)

    # 3) Per-sentence NLI
    per_sentence, contested, unsupported = [], [], []
    supported, hallucinated, contradiction_hits = 0, 0, 0
    top_contra = TopContradiction(None, None, -1.0)

    for sent in draft_sents:
        evidence = retrieve_evidence(sent, retr, clients.cpu, models.embedding_model_name, threshold_to_pass.top_k_retrieval)

        if not evidence:
            res = SentenceResult(sent, False, 0.0, 0.0, None, None, "No evidence retrieved")
            hallucinated += 1
            unsupported.append(res)
            per_sentence.append(res)
            continue

        es = nli_scores_for_evidence(clients.gpu, models.nli_model_name, sent, evidence)
        if es.contradiction > top_contra.score:
            top_contra = TopContradiction(sent, es.conflicting_evidence, es.contradiction)

        is_supported = es.entailment >= threshold_to_pass.entailment_support and es.contradiction <= threshold_to_pass.contradiction_support

        if is_supported:
            supported += 1
            res = SentenceResult(sent, True, es.entailment, es.contradiction, es.supporting_evidence,
                                 es.conflicting_evidence)
        else:
            hallucinated += 1
            res = SentenceResult(sent, False, es.entailment, es.contradiction, es.supporting_evidence,
                                 es.conflicting_evidence, "Low entailment or high contradiction")
            unsupported.append(res)

        if es.contradiction > 0.5: contradiction_hits += 1
        per_sentence.append(res)

    supported_rate = (supported / len(draft_sents)) if draft_sents else 1.0
    hallucination_rate = (hallucinated / len(draft_sents)) if draft_sents else 0.0

    # 4) Coverage
    coverage = semantic_coverage(
        transcript_chunks, retr.chunk_embeddings, draft_sents,
        clients.cpu, models.embedding_model_name, threshold_to_pass.max_sim_coverage
    )

    # 5) Final Decision
    passed = all([
        supported_rate >= pass_criteria.min_supported_rate,
        hallucination_rate <= pass_criteria.max_hallucination_rate,
        coverage.coverage >= pass_criteria.min_coverage,
        (contradiction_hits == 0) if pass_criteria.zero_contradictions else True
    ])

    return VerificationReport(
        supported_rate, hallucination_rate, contradiction_hits, coverage,
        top_contra, contested, unsupported, per_sentence, passed
    )

if __name__ == "__main__":
    import argparse
    from dataclasses import asdict

    parser = argparse.ArgumentParser(description="Verify a draft against a transcript using Ollama NLI.")
    # Inputs
    parser.add_argument("--transcript", type=str, default=None,
                        help="Path to plaintext transcript (.txt). If omitted, uses demo text.")
    parser.add_argument("--draft", type=str, default=None,
                        help="Path to plaintext draft (.txt). If omitted, uses demo text.")
    parser.add_argument("--draft-json", type=str, default=None,
                        help="Path to JSON file to extract draft text from (mutually exclusive with --draft).")
    parser.add_argument("--draft-json-keys", type=str, default=None,
                        help='Comma-separated dotted keys for --draft-json (e.g., "title,summary.body").')

    # Language
    parser.add_argument("--language", type=str, default="german",
                        help='Language for sentence splitting (e.g., "german", "english").')

    # Model config
    parser.add_argument("--embed-model", type=str, default="nomic-embed-text")
    parser.add_argument("--nli-model", type=str, default="llama3")
    parser.add_argument("--cpu-host", type=str, default="http://localhost:11435")
    parser.add_argument("--gpu-host", type=str, default="http://localhost:11434")

    # Thresholds
    parser.add_argument("--entailment-support", type=float, default=0.55,
                        help="Minimum entailment score to count as supported.")
    parser.add_argument("--contradiction-support", type=float, default=0.35,
                        help="Maximum contradiction score allowed for a sentence to still count as supported.")
    parser.add_argument("--top-k-retrieval", type=int, default=5,
                        help="Number of evidence chunks retrieved per sentence.")
    parser.add_argument("--max-sim-coverage", type=float, default=0.55,
                        help="Similarity threshold for coverage computation.")

    # Pass criteria
    parser.add_argument("--min-supported-rate", type=float, default=0.70,
                        help="Minimum fraction of draft sentences supported.")
    parser.add_argument("--max-hallucination-rate", type=float, default=0.30,
                        help="Maximum fraction of unsupported sentences allowed.")
    parser.add_argument("--min-coverage", type=float, default=0.70,
                        help="Minimum transcript coverage required.")
    parser.add_argument("--zero-contradictions", action="store_true",
                        help="Fail if any high-contradiction sentence is found (>0.5).")

    # Output
    parser.add_argument("--out", type=str, default=None,
                        help="Optional path to write the JSON report. Prints to stdout otherwise.")

    args = parser.parse_args()

    # --- Load inputs ---
    if args.transcript:
        transcript_text = load_text(args.transcript)
    else:
        # Minimal German demo transcript
        transcript_text = (
            "Herr Müller, 58 Jahre alt, stellte sich mit seit drei Tagen bestehenden Kopfschmerzen vor. "
            "Er nahm Paracetamol mit mäßiger Linderung. Fieber wurde verneint."
        )

    if args.draft and args.draft_json:
        raise SystemExit("Please provide either --draft or --draft-json, not both.")

    if args.draft:
        draft_text = load_text(args.draft)
    elif args.draft_json:
        if not args.draft_json_keys:
            raise SystemExit("--draft-json requires --draft-json-keys (comma-separated dotted paths).")
        keys = [k.strip() for k in args.draft_json_keys.split(",") if k.strip()]
        draft_text = load_draft_from_json(args.draft_json, keys)
    else:
        # Minimal German demo draft
        draft_text = (
            "Der 58-jährige Herr Müller berichtet über Kopfschmerzen seit drei Tagen. "
            "Er nahm Paracetamol mit etwas Wirkung. Fieber besteht nicht."
        )

    # --- Assemble configs ---
    model_cfg = NLIOllamaModelConfig(
        embedding_model_name=args.embed_model,
        nli_model_name=args.nli_model,
        cpu_client_host=args.cpu_host,
        gpu_client_host=args.gpu_host,
    )

    thresholds = Thresholds(
        entailment_support=args.entailment_support,
        contradiction_support=args.contradiction_support,
        top_k_retrieval=args.top_k_retrieval,
        max_sim_coverage=args.max_sim_coverage,
    )

    criteria = PassCriteria(
        min_supported_rate=args.min_supported_rate,
        max_hallucination_rate=args.max_hallucination_rate,
        min_coverage=args.min_coverage,
        zero_contradictions=args.zero_contradictions,
    )

    # --- Run verification ---
    try:
        report = verify_generation_against_truth(
            ground_truth_text=transcript_text,
            generated_text=draft_text,
            language=args.language,
            models=model_cfg,
            threshold_to_pass=thresholds,
            pass_criteria=criteria,
        )

        # Convert dataclass (with nested dataclasses) to JSON-serializable dict
        report_dict = asdict(report)

        payload = json.dumps(report_dict, ensure_ascii=False, indent=2)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(payload)
            print(f"Wrote report to {args.out}")
        else:
            print(payload)

    except Exception as e:
        # Surface a clear failure rather than a long stack trace in typical CLI usage
        import traceback
        print(f"[FATAL] Verification failed: {e}")
        traceback.print_exc()
        raise
