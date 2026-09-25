from __future__ import annotations

import pytest

from retrieval.index import LocalEmbeddingIndex
from retrieval.qa import answer_question

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def built_index(isolated_settings_module, clean_fixture_df_module):
    return LocalEmbeddingIndex.build(clean_fixture_df_module, isolated_settings_module)


@pytest.fixture(scope="module")
def isolated_settings_module(tmp_path_factory, base_settings_module):
    from dataclasses import replace

    tmp_path = tmp_path_factory.mktemp("retrieval_chroma")
    paths = replace(
        base_settings_module.paths,
        chroma_dir=tmp_path / "chroma",
        embeddings_json=tmp_path / "embeddings.json",
    )
    return replace(base_settings_module, paths=paths)


@pytest.fixture(scope="module")
def base_settings_module():
    from core.config import load_settings

    return load_settings()


@pytest.fixture(scope="module")
def clean_fixture_df_module():
    import pandas as pd
    from pathlib import Path

    fixtures_dir = Path(__file__).resolve().parents[1] / "data" / "fixtures"
    return pd.read_json(fixtures_dir / "papers_clean.json")


def test_build_index_loads_all_documents(built_index, clean_fixture_df_module):
    assert built_index.collection.count() == len(clean_fixture_df_module)


def test_search_returns_relevant_paper_for_its_own_title(built_index, clean_fixture_df_module):
    target = clean_fixture_df_module.iloc[0]
    results = built_index.search(target["title"], top_k=3)

    assert len(results) > 0
    assert target["paper_id"] in {r.paper_id for r in results}


def test_lookup_by_exact_paper_id(built_index, clean_fixture_df_module):
    target_id = clean_fixture_df_module.iloc[0]["paper_id"]
    record = built_index.lookup(target_id)
    assert record is not None
    assert record["paper_id"] == target_id


def test_lookup_by_exact_title_case_insensitive(built_index, clean_fixture_df_module):
    target_title = clean_fixture_df_module.iloc[0]["title"]
    record = built_index.lookup(target_title.upper())
    assert record is not None
    assert record["title"] == target_title


def test_lookup_unknown_value_returns_none(built_index):
    assert built_index.lookup("this paper definitely does not exist 12345") is None


def test_answer_question_exact_title_match_returns_authors(
    built_index, isolated_settings_module, clean_fixture_df_module
):
    target = clean_fixture_df_module.iloc[0]
    question = f"Who authored the paper '{target['title']}'?"

    result = answer_question(question, isolated_settings_module, built_index)

    assert target["paper_id"] in result.retrieved_doc_ids
    assert result.answer == target["authors_joined"]
