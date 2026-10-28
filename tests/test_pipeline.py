from generation.answer import generate_answer, parse_answer
from generation.llm import FakeLLM
from retrieval.embedding import FakeEmbedder
from retrieval.search import Retriever, read_pairs
from retrieval.store import MemoryStore
from shared.config import ROOT


def make_retriever() -> Retriever:
    r = Retriever(FakeEmbedder(256), MemoryStore())
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


def test_parse_answer_handles_non_json():
    answer = parse_answer("not json at all", allowed_ids={1})
    assert answer.examples == []
    assert answer.summary
