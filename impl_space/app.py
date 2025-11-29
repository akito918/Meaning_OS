# app.py -- HuggingFace Spaces 用 Gradio UI（日本語/英語対応）

import json
from pathlib import Path

import gradio as gr

from mini_os_demo import MiniMeaningOS, answer_ja_question, answer_en_question

BASE_DIR = Path(__file__).parent

# OS 本体を 1 回ロードして使い回す
os_instance = MiniMeaningOS()


def query_fn(text: str, lang: str):
    """
    Gradio から呼ばれる 1 回分のクエリ処理。
    lang が "ja" なら日本語質問として、"en" なら英語質問として処理する。
    戻り値:
      - answer_text: 人間向けの短い答え
      - pretty_json: OS から返ってきた JSON の整形文字列
    """
    text = (text or "").strip()
    if not text:
        return "質問 / Question を入力してください。", "{}"

    # 言語ごとに質問ハンドラを切り替え
    if lang == "ja":
        ans = answer_ja_question(os_instance, text)
    else:
        ans = answer_en_question(os_instance, text)

    p_id = ans.get("pattern_id")
    results = ans.get("results", [])
    answer_text = ""

    # ==== 共通の「簡易答え」組み立て ====

    # ① 用途 / 分類 / 道具 / 翻訳（日英）
    if p_id in (
        "USE_1",
        "CAT_1",
        "TOOL_FOR_1",
        "TRANS_EN_1",
        "USE_EN_1",
        "CAT_EN_1",
    ):
        values = [
            r.get("value")
            for r in results
            if isinstance(r, dict) and "value" in r
        ]
        if values:
            answer_text = " / ".join(str(v) for v in values)

    # ② 素材（日・英）
    elif p_id in ("MAT_1", "MAT_EN_1"):
        if results:
            pretty = []
            for r in results:
                if not isinstance(r, dict):
                    continue
                labels = r.get("labels") or [r.get("core_id")]
                pretty.append(" / ".join(str(x) for x in labels if x))
            if pretty:
                answer_text = " / ".join(pretty)

    # ③ プロフィール（日・英）
    elif p_id in ("PROFILE_1", "PROFILE_EN_1"):
        if results and isinstance(results[0], dict):
            prof = results[0].get("profile", {}) or {}
            main_slots = []
            for slot in ["WHAT", "HOW", "OUTCOME", "DISC"]:
                vals = prof.get(slot) or []
                if vals:
                    main_slots.append(f"{slot}: {', '.join(map(str, vals))}")
            if main_slots:
                answer_text = " | ".join(main_slots)
            else:
                answer_text = "Profile information is available."

    # ④ 意味差（今は日本語のみ）
    elif p_id == "DIFF_1":
        if results and isinstance(results[0], dict):
            diff = results[0]
            shared = diff.get("shared_cores") or []
            only_left = diff.get("only_left_cores") or []
            only_right = diff.get("only_right_cores") or []
            answer_text = (
                f"共有 / shared: {shared} | "
                f"左のみ / only left: {only_left} | "
                f"右のみ / only right: {only_right}"
            )

    # フォールバック：何か value があればそれを表示
    if not answer_text and results:
        first = results[0]
        if isinstance(first, dict) and "value" in first:
            answer_text = str(first["value"])

    if not answer_text:
        answer_text = "（答え候補なし / no candidate answer）"

    pretty_json = json.dumps(ans, ensure_ascii=False, indent=2)
    return answer_text, pretty_json


with gr.Blocks() as demo:
    gr.Markdown(
        """
        # Mini Meaning OS (prototype)

        日本語 / English で質問できます。

        **日本語例:**
        - 包丁の用途は何？
        - 包丁の素材は？
        - 包丁の分類は？
        - 切るのに使う道具は？
        - 包丁の英語は？

        **English examples:**
        - What is the use of a kitchen knife?
        - What is a kitchen knife made of?
        - What category is a knife?
        - Tell me about kitchen knife.
        """
    )

    with gr.Row():
        inp = gr.Textbox(
            label="質問 / Question",
            placeholder="例: 包丁の用途は何？ / What is the use of a kitchen knife?",
            lines=2,
        )

    with gr.Row():
        lang_select = gr.Radio(
            ["ja", "en"],
            value="ja",
            label="Language / 言語",
        )

    btn = gr.Button("実行 / Run")

    out_answer = gr.Textbox(
        label="答え（簡易） / Answer (short)",
        interactive=False,
    )

    out_json = gr.Code(
        label="生JSON / Raw JSON",
        language="json",
    )

    btn.click(
        fn=query_fn,
        inputs=[inp, lang_select],
        outputs=[out_answer, out_json],
    )

if __name__ == "__main__":
    demo.launch()
