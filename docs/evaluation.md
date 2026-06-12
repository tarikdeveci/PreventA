# Evaluation Plan

Use held-out, engineer-reviewed HAZOP rows. Do not train or tune on the evaluation set.

Primary metrics:

- `recall@k`: whether an accepted historical evidence chunk appears in retrieval.
- `citation_accuracy`: whether every generated citation belongs to retrieved context.
- `citation_support`: engineer judgment that the cited excerpt supports the candidate.
- `acceptance_rate`: accepted or edited suggestions divided by displayed suggestions.
- `unsafe_suggestion_rate`: candidates marked technically unsafe by two reviewers.

Slice results by equipment type, parameter, guideword, source type, and study age. Keep
prompt version, embedding model, reranker version, and corpus snapshot in every run.

The JSONL input accepted by `scripts/evaluate_retrieval.py` is:

```json
{"expected_chunk_ids":["a"],"retrieved_chunk_ids":["a","b"],"cited_chunk_ids":["a"]}
```

