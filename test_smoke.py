import pandas as pd
from src.core.config import load_settings
from src.retrieval.index import LocalEmbeddingIndex
from src.retrieval.qa import answer_question

s = load_settings()
idx = LocalEmbeddingIndex.build(pd.read_json('data/fixtures/papers_clean.json'), s)
ans = answer_question("Who are the authors of the paper 'Continuous Benchmark Evaluation for Enterprise Retrieval Pipelines'?", s, idx)
print(ans.answer[:120])
