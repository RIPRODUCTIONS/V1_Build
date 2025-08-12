from __future__ import annotations

import statistics
from collections import defaultdict, deque

# In-memory bandit-ish selector (persist to DB later)
_history = defaultdict(lambda: deque(maxlen=200))


def record(task: str, params: dict, outcome_score: float):
    """Record task execution parameters and outcome for learning."""
    _history[task].append((params, outcome_score))


def best_params(task: str, fallbacks: dict):
    """Get the best parameters for a task based on historical performance."""
    hist = _history[task]
    if len(hist) < 10:
        return fallbacks

    # Pick the params bucket with best median outcome
    buckets = {}
    for p, s in hist:
        key = tuple(sorted(p.items()))
        buckets.setdefault(key, []).append(s)

    if not buckets:
        return fallbacks

    best = max(buckets.items(), key=lambda kv: statistics.median(kv[1]))
    return dict(best[0])


def get_task_stats(task: str):
    """Get statistics for a specific task."""
    hist = _history[task]
    if not hist:
        return {'count': 0, 'avg_score': 0.0}

    scores = [score for _, score in hist]
    return {
        'count': len(hist),
        'avg_score': statistics.mean(scores),
        'median_score': statistics.median(scores),
        'min_score': min(scores),
        'max_score': max(scores),
    }


def clear_history(task: str = None):
    """Clear learning history for a task or all tasks."""
    if task:
        _history[task].clear()
    else:
        _history.clear()
