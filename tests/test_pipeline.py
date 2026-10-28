from generation.answer import generate_answer, parse_answer
from generation.llm import FakeLLM
from retrieval.embedding import FakeEmbedder
from retrieval.search import Retriever, read_pairs
from retrieval.store import MemoryStore
from shared.config import ROOT


def make_retriever() -> Retriever:
    r = Retriever(FakeEmbedder(1024), MemoryStore())
    r.index(read_pairs(ROOT / "data/sample/pairs.tsv"))
    return r


def test_sample_loads():
    sentences = read_pairs(ROOT / "data/sample/pairs.tsv")
    assert len(sentences) >= 20
    assert {s.lang for s in sentences} <= {"en", "zh", "th"}


def test_chinese_query_finds_matching_sentence():
    results = make_retriever().search("改天我请你吃饭", k=3)
    texts = [r.text for r in results]
    assert "I'll treat you to dinner another day." in texts


def test_answer_cites_only_retrieved_ids():
    retriever = make_retriever()
    retrieved = retriever.search("做决定", k=5)
    answer = generate_answer("做决定", retrieved, FakeLLM())
    assert answer.summary
    assert set(answer.examples) <= {r.sentence_id for r in retrieved}


def test_parse_answer_drops_invented_ids():
    raw = '{"summary": "s", "explanation": "e", "examples": [1, 999, "2", "x"]}'
    answer = parse_answer(raw, allowed_ids={1, 2})
    assert answer.examples == [1, 2]


def test_threshold_drops_low_scoring_examples():
    retriever = make_retriever()
    unfiltered = retriever.search("改天我请你吃饭", k=5)
    filtered = retriever.search("改天我请你吃饭", k=5, min_score=0.15)
    assert len(filtered) < len(unfiltered)
    assert all(r.score >= 0.15 for r in filtered)
    # The truly relevant sentence survives the threshold
    assert "I'll treat you to dinner another day." in [r.text for r in filtered]


def test_threshold_keeps_relevant_and_drops_irrelevant():
    retriever = make_retriever()
    texts = [r.text for r in retriever.search("下定决心", k=5, min_score=0.15)]
    assert "She finally made up her mind to study abroad." in texts
    assert "Could you do me a favor and check this email?" not in texts


def test_unrelated_query_returns_no_evidence():
    retrieved = make_retriever().search("量子色动力学", k=5, min_score=0.15)
    assert retrieved == []


def test_no_evidence_answer_is_marked_ungrounded():
    answer = generate_answer("量子色动力学", [], FakeLLM())
    assert answer.grounded is False
    assert answer.examples == []
    assert answer.summary


def test_answer_with_citations_is_grounded():
    retrieved = make_retriever().search("改天我请你吃饭", k=5, min_score=0.15)
    answer = generate_answer("改天我请你吃饭", retrieved, FakeLLM())
    assert answer.grounded is True
    assert answer.examples


def test_grounded_comes_from_citations_not_model_claims():
    # The model cites only ids it was not given: nothing survives, so not grounded.
    raw = '{"summary": "s", "explanation": "e", "examples": [999]}'
    assert parse_answer(raw, allowed_ids={1, 2}).grounded is False


def test_parse_answer_handles_non_json():
    answer = parse_answer("not json at all", allowed_ids={1})
    assert answer.examples == []
    assert answer.summary
