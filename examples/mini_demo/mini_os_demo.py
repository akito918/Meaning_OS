# mini_os_demo.py

import csv
import json
import re
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).parent

CORE_CSV = BASE_DIR / "core_concepts.csv"
TRIPLES_WITH_REV = BASE_DIR / "meaning_triples_with_reverse.csv"
TRIPLES_CSV = BASE_DIR / "meaning_triples.csv"
EXPR_CSV = BASE_DIR / "expr_links.csv"
TRIPLE_EVIDENCE_CSV = BASE_DIR / "triple_evidence.csv"  # ★追加


# ========== データ構造 ==========

@dataclass
class CoreConcept:
    core_id: str
    can_be_relation: bool
    status: str
    created_at: str


@dataclass
class Triple:
    triple_id: str
    src: str
    rel: str
    dst: str
    conditions: Dict[str, Any]
    polarity: str
    status: str
    is_reverse: bool
    reverse_of: Optional[str]
    created_at: str
    note: str


@dataclass
class ExprLink:
    expr_id: str
    expr_label: str
    core_id: str
    conditions: Dict[str, Any]
    source_kind: str
    source_detail: str
    status: str
    created_at: str
    updated_at: str
    note: str


# ★ 新しいデータ構造：evidence
@dataclass
class TripleEvidence:
    evidence_id: str
    triple_id: str
    evidence_type: str
    source_kind: str
    stance: str
    weight: float
    source_detail: str
    note: str
    created_at: str


# ========== ロード関数 ==========

def load_core_concepts(path: Path) -> Dict[str, CoreConcept]:
    cores: Dict[str, CoreConcept] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cores[row["core_id"]] = CoreConcept(
                core_id=row["core_id"],
                can_be_relation=row.get("can_be_relation", "0") in ("1", "true", "True"),
                status=row.get("status", "active"),
                created_at=row.get("created_at", ""),
            )
    return cores


def _fix_raw_json(cond_raw: str, where: str) -> dict:
    """
    CSV 内のゆるい JSON をそれっぽく補正してから parse する。
    - {""domain"":[""cooking""]} → {"domain":["cooking"]}
    - ' ←コメント...' 以降をカット
    """
    if not cond_raw:
        return {}

    cond_raw = cond_raw.split("←")[0].strip()

    cond_raw = cond_raw.strip()

    if '""' in cond_raw and '"' in cond_raw:
        cond_raw = cond_raw.replace('""', '"')

    if not (cond_raw.startswith("{") and cond_raw.endswith("}")):
        if cond_raw not in ("", "{}"):
            print(f"[WARN] {where}: not a JSON object -> {cond_raw}")
        return {}

    try:
        return json.loads(cond_raw)
    except json.JSONDecodeError:
        print(f"[WARN] {where}: json decode error -> {cond_raw}")
        return {}


def load_triples(path: Path) -> List[Triple]:
    triples: List[Triple] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cond_raw = row.get("conditions_json", "") or ""
            conditions = _fix_raw_json(cond_raw, f"triple {row.get('triple_id')}")
            triples.append(
                Triple(
                    triple_id=row["triple_id"],
                    src=row["src_core_id"],
                    rel=row["rel_core_id"],
                    dst=row["dst_core_id"],
                    conditions=conditions,
                    polarity=row.get("polarity", "positive"),
                    status=row.get("status", "active"),
                    is_reverse=row.get("is_reverse", "0") in ("1", "true", "True"),
                    reverse_of=row.get("reverse_of") or None,
                    created_at=row.get("created_at", ""),
                    note=row.get("note", ""),
                )
            )
    return triples


def load_expr_links(path: Path) -> List[ExprLink]:
    exprs: List[ExprLink] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cond_raw = row.get("conditions_json", "") or ""
            conditions = _fix_raw_json(cond_raw, f"expr {row.get('expr_id')}")
            exprs.append(
                ExprLink(
                    expr_id=row["expr_id"],
                    expr_label=row["expr_label"],
                    core_id=row["core_id"],
                    conditions=conditions,
                    source_kind=row.get("source_kind", ""),
                    source_detail=row.get("source_detail", ""),
                    status=row.get("status", "active"),
                    created_at=row.get("created_at", ""),
                    updated_at=row.get("updated_at", ""),
                    note=row.get("note", ""),
                )
            )
    return exprs


# ★ triple_evidence のロード
def load_triple_evidence(path: Path) -> List[TripleEvidence]:
    if not path.exists():
        print(f"[INFO] triple_evidence.csv not found, skip evidence layer.")
        return []

    evidences: List[TripleEvidence] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("evidence_id"):
                continue
            try:
                weight = float(row.get("weight", "0") or 0.0)
            except ValueError:
                weight = 0.0
            evidences.append(
                TripleEvidence(
                    evidence_id=row["evidence_id"],
                    triple_id=row.get("triple_id", ""),
                    evidence_type=row.get("evidence_type", ""),
                    source_kind=row.get("source_kind", ""),
                    stance=row.get("stance", "positive"),
                    weight=weight,
                    source_detail=row.get("source_detail", ""),
                    note=row.get("note", ""),
                    created_at=row.get("created_at", ""),
                )
            )
    return evidences


# ========== 条件フィルタ ==========

def cond_match(conditions: Dict[str, Any], wanted: Dict[str, Any]) -> bool:
    for k, v in wanted.items():
        if v is None:
            continue
        if k not in conditions:
            return False
        cv = conditions[k]
        if isinstance(cv, list):
            if isinstance(v, list):
                if not any(x in cv for x in v):
                    return False
            else:
                if v not in cv:
                    return False
        else:
            if isinstance(v, list):
                if cv not in v:
                    return False
            else:
                if cv != v:
                    return False
    return True


# ========== インデックス構築 & OS本体 ==========

class MiniMeaningOS:
    def __init__(self):
        self.cores = load_core_concepts(CORE_CSV)

        triples_path = TRIPLES_WITH_REV if TRIPLES_WITH_REV.exists() else TRIPLES_CSV
        print(f"[INFO] load triples from {triples_path.name}")
        self.triples = load_triples(triples_path)
        self.exprs = load_expr_links(EXPR_CSV)

        # evidence
        self.evidences = load_triple_evidence(TRIPLE_EVIDENCE_CSV)
        self.evidence_index: Dict[str, List[TripleEvidence]] = defaultdict(list)
        for ev in self.evidences:
            if ev.triple_id:
                self.evidence_index[ev.triple_id].append(ev)

        # expr_label → [ExprLink]
        self.expr_index: Dict[str, List[ExprLink]] = defaultdict(list)
        for e in self.exprs:
            self.expr_index[e.expr_label].append(e)

        # core_id → [ExprLink]
        self.labels_by_core: Dict[str, List[ExprLink]] = defaultdict(list)
        for e in self.exprs:
            self.labels_by_core[e.core_id].append(e)

    # ----- expr_label から core 候補を引く -----

    def find_cores_by_expr(self, label: str, lang: Optional[str] = None) -> List[str]:
        candidates = self.expr_index.get(label, [])
        result = []
        for e in candidates:
            if lang is not None:
                if e.conditions.get("lang") != lang:
                    continue
            result.append(e.core_id)
        return sorted(set(result))

    # ----- core_id → ラベル候補 -----

    def labels_for_core(
        self,
        core_id: str,
        lang: Optional[str] = None,
        top_k: int = 3,
    ) -> List[str]:
        exprs = self.labels_by_core.get(core_id, [])
        scored = []
        for e in exprs:
            if lang is not None and e.conditions.get("lang") != lang:
                continue
            freq = float(e.conditions.get("freq", 1.0))
            scored.append((freq, e.expr_label))
        scored.sort(reverse=True)
        return [label for _, label in scored[:top_k]]

    # ----- meaning_triples 検索 -----

    def find_triples(
        self,
        src: Optional[str] = None,
        rel: Optional[str] = None,
        dst: Optional[str] = None,
        domain: Optional[str] = None,
        polarity: str = "positive",
    ) -> List[Triple]:
        wanted_conds: Dict[str, Any] = {}
        if domain:
            wanted_conds["domain"] = [domain]

        out = []
        for t in self.triples:
            if polarity and t.polarity != polarity:
                continue
            if src and t.src != src:
                continue
            if rel and t.rel != rel:
                continue
            if dst and t.dst != dst:
                continue
            if wanted_conds and not cond_match(t.conditions, wanted_conds):
                continue
            out.append(t)
        return out

    # ----- evidence 取得 -----

    def get_evidence_for_triple(self, triple_id: str) -> List[Dict[str, Any]]:
        evs = self.evidence_index.get(triple_id, [])
        out = []
        for e in evs:
            out.append(
                {
                    "evidence_id": e.evidence_id,
                    "evidence_type": e.evidence_type,
                    "source_kind": e.source_kind,
                    "stance": e.stance,
                    "weight": e.weight,
                    "source_detail": e.source_detail,
                    "note": e.note,
                    "created_at": e.created_at,
                }
            )
        return out

    # ========== 意味クエリ関数群 ==========

    # ① 用途：Xの用途は？
    def purpose_of(self, expr_label: str, lang: str = "ja") -> List[Dict[str, Any]]:
        cores = self.find_cores_by_expr(expr_label, lang=lang)
        if not cores:
            print(f"[WARN] expr '{expr_label}' (lang={lang}) に対応する core が見つからない")
            return []
        core_id = cores[0]
        triples = self.find_triples(
            src=core_id,
            rel="core:use-purpose-001",
            domain="cooking",
        )
        results: List[Dict[str, Any]] = []
        for t in triples:
            labels = self.labels_for_core(t.dst, lang=lang)
            results.append(
                {
                    "triple_id": t.triple_id,
                    "value": labels[0] if labels else t.dst,
                    "labels": labels,
                    "conditions": t.conditions,
                }
            )
        return results

    # ② 素材：Xの素材は？
    def materials_of(self, expr_label: str, lang: str = "ja") -> List[Dict[str, Any]]:
        cores = self.find_cores_by_expr(expr_label, lang=lang)
        if not cores:
            print(f"[WARN] expr '{expr_label}' (lang={lang}) に対応する core が見つからない")
            return []
        core_id = cores[0]
        triples = self.find_triples(
            src=core_id,
            rel="core:material-001",
            domain="cooking",
        )
        out = []
        for t in triples:
            labels = self.labels_for_core(t.dst, lang=lang)
            out.append(
                {
                    "triple_id": t.triple_id,   # ★ triple_id を保持
                    "core_id": t.dst,
                    "labels": labels,
                    "conditions": t.conditions,
                }
            )
        return out

    # ③ 分類：Xは何の仲間？ / 分類は？
    def categories_of(self, expr_label: str, lang: str = "ja") -> List[Dict[str, Any]]:
        cores = self.find_cores_by_expr(expr_label, lang=lang)
        if not cores:
            print(f"[WARN] expr '{expr_label}' (lang={lang}) に対応する core が見つからない")
            return []
        core_id = cores[0]
        triples = self.find_triples(
            src=core_id,
            rel="core:category-001",
            domain="cooking",
        )
        results: List[Dict[str, Any]] = []
        for t in triples:
            labels = self.labels_for_core(t.dst, lang=lang)
            results.append(
                {
                    "triple_id": t.triple_id,
                    "value": labels[0] if labels else t.dst,
                    "labels": labels,
                    "conditions": t.conditions,
                }
            )
        return results

    # ④ 逆向き：Xに使う道具は？（切る → 包丁など）
    def tools_for_action(self, expr_label: str, lang: str = "ja") -> List[Dict[str, Any]]:
        cores = self.find_cores_by_expr(expr_label, lang=lang)
        if not cores:
            print(f"[WARN] expr '{expr_label}' (lang={lang}) に対応する core が見つからない")
            return []
        action_core = cores[0]
        tools: List[Dict[str, Any]] = []

        triples1 = self.find_triples(
            dst=action_core,
            rel="core:use-purpose-001",
            domain="cooking",
        )
        for t in triples1:
            labels = self.labels_for_core(t.src, lang=lang)
            tools.append(
                {
                    "triple_id": t.triple_id,
                    "value": labels[0] if labels else t.src,
                    "labels": labels,
                    "conditions": t.conditions,
                }
            )

        triples2 = self.find_triples(
            src=action_core,
            rel="core:use-purpose-for-001",
            domain="cooking",
        )
        for t in triples2:
            labels = self.labels_for_core(t.dst, lang=lang)
            tools.append(
                {
                    "triple_id": t.triple_id,
                    "value": labels[0] if labels else t.dst,
                    "labels": labels,
                    "conditions": t.conditions,
                }
            )

        # triple_id + value で重複排除するならここでやってもよいが、デモではそのまま
        return tools

    # ⑤ プロフィール（9スロットビュー）
    REL_TO_SLOT = {
        "core:use-purpose-001": ("OUTCOME", "TARGET"),
        "core:use-purpose-for-001": ("TARGET", "OUTCOME"),
        "core:material-001": ("HOW", None),
        "core:material-for-001": (None, "HOW"),
        "core:category-001": ("WHAT", None),
        "core:category-of-001": (None, "WHAT"),
        "core:domain-001": ("DISC", None),
        "core:domain-of-001": (None, "DISC"),
    }

    def render_profile(
        self,
        expr_label: str,
        lang: str = "ja",
    ) -> Dict[str, Any]:
        cores = self.find_cores_by_expr(expr_label, lang=lang)
        if not cores:
            print(f"[WARN] expr '{expr_label}' (lang={lang}) に対応する core が見つからない")
            return {}

        focus = cores[0]

        view: Dict[str, Any] = {
            "WHO": [],
            "WHAT": [],
            "WHY": [],
            "HOW": [],
            "WHERE": [],
            "WHEN": [],
            "OUTCOME": [],
            "STATE": [],
            "DISC": [],
            "labels": {
                "ja": self.labels_for_core(focus, lang="ja"),
                "en": self.labels_for_core(focus, lang="en"),
            },
        }

        for t in self.triples:
            if t.polarity != "positive":
                continue

            if t.src == focus:
                rel_key = self.REL_TO_SLOT.get(t.rel)
                if not rel_key:
                    continue
                slot = rel_key[0]
                if not slot:
                    continue
                other_core = t.dst

            elif t.dst == focus:
                rel_key = self.REL_TO_SLOT.get(t.rel)
                if not rel_key:
                    continue
                slot = rel_key[1]
                if not slot:
                    continue
                other_core = t.src

            else:
                continue

            labels = self.labels_for_core(other_core, lang=lang)
            if not labels:
                labels = self.labels_for_core(other_core, lang="ja") or self.labels_for_core(other_core, lang="en")
            if not labels:
                labels = [other_core]

            for label in labels:
                if label not in view[slot]:
                    view[slot].append(label)

        return view

    # ⑥ 日→英
    def translations_en(self, expr_label: str) -> List[str]:
        cores = self.find_cores_by_expr(expr_label, lang="ja")
        if not cores:
            print(f"[WARN] expr '{expr_label}' (ja) に対応する core が見つからない")
            return []
        core_id = cores[0]
        labels_en = self.labels_for_core(core_id, lang="en")
        return labels_en

    # ⑦ 意味差：expr1 vs expr2
    def diff_meanings(self, expr_left: str, expr_right: str) -> Dict[str, Any]:
        def guess_lang(token: str) -> str:
            if all(ord(ch) < 128 for ch in token):
                return "en"
            return "ja"

        lang_left = guess_lang(expr_left)
        lang_right = guess_lang(expr_right)

        cores_left = set(self.find_cores_by_expr(expr_left, lang=lang_left))
        cores_right = set(self.find_cores_by_expr(expr_right, lang=lang_right))

        shared = cores_left & cores_right
        only_left = cores_left - cores_right
        only_right = cores_right - cores_left

        return {
            "expr_left": expr_left,
            "lang_left": lang_left,
            "cores_left": sorted(cores_left),
            "expr_right": expr_right,
            "lang_right": lang_right,
            "cores_right": sorted(cores_right),
            "shared_cores": sorted(shared),
            "only_left_cores": sorted(only_left),
            "only_right_cores": sorted(only_right),
        }


# ========== 日本語質問パーサ ==========

def parse_ja_question(text: str) -> dict:
    t = text.strip()

    # ⑦ 意味差
    if "と" in t and ("違い" in t or "違う" in t or "同じ" in t or "一緒" in t):
        left, right_part = t.split("と", 1)
        left = left.strip()
        right = right_part.split("は", 1)[0]
        right = right.replace("って", "").strip()
        return {
            "query": text,
            "type": "diff_query",
            "pattern_id": "DIFF_1",
            "expr_left": left,
            "expr_right": right,
        }

    # ⑥ 英語
    if "英語" in t:
        m = re.search(r"(.+?)の英語", t)
        if not m:
            m = re.search(r"(.+?)は英語", t)
        subject = m.group(1).strip() if m else t.replace("の英語", "").replace("は英語で", "")
        subject = subject.strip("は？ 　")
        return {
            "query": text,
            "type": "expr_query",
            "pattern_id": "TRANS_EN_1",
            "subject": subject,
            "target_lang": "en",
        }

    m = re.match(r"(.+?)の(.+)", t)
    if m:
        subject = m.group(1).strip()
        rest = m.group(2)
    else:
        subject = t
        rest = t

    # ① 用途
    if "用途" in rest:
        return {
            "query": text,
            "type": "slot_query",
            "pattern_id": "USE_1",
            "subject": subject,
            "slot": "OUTCOME",
            "via_lemma": "用途",
        }

    # ② 素材
    if "素材" in rest or "材質" in rest:
        return {
            "query": text,
            "type": "slot_query",
            "pattern_id": "MAT_1",
            "subject": subject,
            "slot": "HOW",
            "via_lemma": "素材",
        }

    # ③ 分類
    if "分類" in rest or "何の仲間" in rest or "どんな種類" in rest:
        return {
            "query": text,
            "type": "slot_query",
            "pattern_id": "CAT_1",
            "subject": subject,
            "slot": "WHAT",
            "via_lemma": "分類",
        }

    # ④ 逆向き（道具）
    if "に使う道具" in t or "ための道具" in t:
        m2 = re.match(r"(.+?)の?に使う道具", t)
        if not m2:
            m2 = re.match(r"(.+?)の?ための道具", t)
        act = m2.group(1).strip() if m2 else subject
        return {
            "query": text,
            "type": "slot_query",
            "pattern_id": "TOOL_FOR_1",
            "subject": act,
            "slot": "TOOL",
            "via_lemma": "道具",
        }

    # ⑤ プロフィール
    if "プロフィール" in t or "について教えて" in t or "について教えてください" in t:
        subj = t.split("について", 1)[0].strip()
        if not subj:
            subj = subject
        return {
            "query": text,
            "type": "profile_query",
            "pattern_id": "PROFILE_1",
            "subject": subj,
        }

    return {
        "query": text,
        "type": "unknown",
        "subject": subject,
    }


# ========== 質問 → OS クエリ → JSON応答 ==========

def answer_ja_question(os: MiniMeaningOS, text: str) -> dict:
    q = parse_ja_question(text)
    qtype = q.get("type")
    subj = q.get("subject", "")

    # ① 用途
    if qtype == "slot_query" and q.get("pattern_id") == "USE_1":
        rows = os.purpose_of(subj, lang="ja")
        return {
            **q,
            "results": [
                {
                    "value": r["value"],
                    "slot": "OUTCOME",
                    "from_relation": "core:use-purpose-001",
                    "conditions": r["conditions"],
                    "triple_id": r["triple_id"],
                    "evidence": os.get_evidence_for_triple(r["triple_id"]),
                }
                for r in rows
            ],
        }

    # ② 素材
    if qtype == "slot_query" and q.get("pattern_id") == "MAT_1":
        mats = os.materials_of(subj, lang="ja")
        return {
            **q,
            "results": [
                {
                    "core_id": m["core_id"],
                    "labels": m["labels"],
                    "slot": "HOW",
                    "from_relation": "core:material-001",
                    "conditions": m["conditions"],
                    "triple_id": m["triple_id"],
                    "evidence": os.get_evidence_for_triple(m["triple_id"]),
                }
                for m in mats
            ],
        }

    # ③ 分類
    if qtype == "slot_query" and q.get("pattern_id") == "CAT_1":
        cats = os.categories_of(subj, lang="ja")
        return {
            **q,
            "results": [
                {
                    "value": r["value"],
                    "slot": "WHAT",
                    "from_relation": "core:category-001",
                    "conditions": r["conditions"],
                    "triple_id": r["triple_id"],
                    "evidence": os.get_evidence_for_triple(r["triple_id"]),
                }
                for r in cats
            ],
        }

    # ④ 逆向き（道具）
    if qtype == "slot_query" and q.get("pattern_id") == "TOOL_FOR_1":
        tools = os.tools_for_action(subj, lang="ja")
        return {
            **q,
            "results": [
                {
                    "value": r["value"],
                    "slot": "TOOL",
                    "from_relation": "core:use-purpose-001 / core:use-purpose-for-001",
                    "conditions": r["conditions"],
                    "triple_id": r["triple_id"],
                    "evidence": os.get_evidence_for_triple(r["triple_id"]),
                }
                for r in tools
            ],
        }

    # ⑤ プロフィール
    if qtype == "profile_query" and q.get("pattern_id") == "PROFILE_1":
        prof = os.render_profile(subj, lang="ja")
        return {
            **q,
            "results": [
                {
                    "profile": prof
                }
            ],
        }

    # ⑥ 日→英
    if qtype == "expr_query" and q.get("pattern_id") == "TRANS_EN_1":
        vals = os.translations_en(subj)
        return {
            **q,
            "results": [
                {
                    "value": v,
                    "target_lang": "en",
                    "via": "expr_links",
                }
                for v in vals
            ],
        }

    # ⑦ 意味差
    if qtype == "diff_query" and q.get("pattern_id") == "DIFF_1":
        diff = os.diff_meanings(q["expr_left"], q["expr_right"])
        return {
            **q,
            "results": [diff],
        }

    return {
        **q,
        "results": [],
        "note": "このパターンの質問はまだ未対応です。",
    }


# ========== スクリプトとしての実行部（対話モード） ==========

def main():
    os = MiniMeaningOS()
    print("日本語で質問してください（空行 or 'exit' で終了）")
    print("例: 包丁の用途は何？ / 包丁の素材は？ / 包丁の分類は？")
    print("    切るのに使う道具は？ / 包丁について教えて")
    print("    包丁の英語は？ / 包丁とknifeは同じ？ など\n")

    while True:
        try:
            line = input("> ").strip()
        except EOFError:
            break

        if not line or line.lower() == "exit":
            break

        ans = answer_ja_question(os, line)
        print("JSON:")
        print(json.dumps(ans, ensure_ascii=False, indent=2))

        results = ans.get("results", [])
        p_id = ans.get("pattern_id")

        if p_id in ("USE_1", "CAT_1", "TOOL_FOR_1", "TRANS_EN_1"):
            values = [r.get("value") for r in results if "value" in r]
            if values:
                print("答え:", "、".join(values))
        elif p_id == "MAT_1":
            if results:
                pretty = []
                for r in results:
                    labels = r.get("labels") or [r.get("core_id")]
                    pretty.append("/".join(labels))
                print("答え(素材):", "、".join(pretty))
        elif p_id == "PROFILE_1":
            if results:
                prof = results[0].get("profile", {})
                print("プロフィール(9スロットのうち主なもの):")
                for slot in ["WHAT", "HOW", "OUTCOME", "DISC"]:
                    print(f"  {slot}: {prof.get(slot, [])}")
        elif p_id == "DIFF_1":
            if results:
                diff = results[0]
                print("意味差（core_idベース）:")
                print("  共有:", diff.get("shared_cores", []))
                print("  左のみ:", diff.get("only_left_cores", []))
                print("  右のみ:", diff.get("only_right_cores", []))

        print("-" * 60)


if __name__ == "__main__":
    main()
