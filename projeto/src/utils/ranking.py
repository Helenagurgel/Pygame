"""Persistência do ranking de maiores goleadas."""

import json
import os

_SAVE_PATH = os.path.join("saves", "ranking.json")
_MAX_ENTRIES = 5


class RankingManager:

    @staticmethod
    def load() -> list:
        try:
            with open(_SAVE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return []

    @staticmethod
    def save(entries: list) -> None:
        os.makedirs(os.path.dirname(_SAVE_PATH), exist_ok=True)
        with open(_SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)

    @staticmethod
    def qualifies(score_p1: int, score_p2: int) -> bool:
        diff = abs(score_p1 - score_p2)
        entries = RankingManager.load()
        if len(entries) < _MAX_ENTRIES:
            return True
        return diff > entries[-1]["diff"]

    @staticmethod
    def add_entry(name: str, score_p1: int, score_p2: int) -> list:
        entries = RankingManager.load()
        diff = abs(score_p1 - score_p2)
        entries.append({
            "name": name,
            "score_p1": score_p1,
            "score_p2": score_p2,
            "diff": diff,
        })
        entries.sort(key=lambda e: e["diff"], reverse=True)
        entries = entries[:_MAX_ENTRIES]
        RankingManager.save(entries)
        return entries
