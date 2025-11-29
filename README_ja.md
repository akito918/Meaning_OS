# 言語OS – 意味ネットワーク 基本仕様 v1


このリポジトリは、自然言語の「意味」を統計・文脈・表現から切り離し、
**不変な意味構造（core + triple）** として保存するための「言語OS（Language OS）」の
**意味ネットワーク仕様 v1** をまとめたものです。

- 意味 = core_concept が meaning_triples によって占めるネットワーク位置
- 単語 = expr_node / expr_links による「人間向けラベル」
- 常識・流行・禁止/解禁 = triple_evidence / triple_stats で扱う評価層
- 9要素ビュー（WHO/WHAT/WHY/HOW/WHERE/WHEN/OUTCOME/STATE + DISC）は
  保存禁止の動的ビュー（レンダリング専用）

## ドキュメント

- 📄 **仕様本体（日本語＋用語英語併記）**  
  [`docs/semantic-graph-spec-v1.md`](docs/semantic-graph-spec-v1.md)

## コアアイデア（超ざっくり）

1. **意味は三連結 (src, rel, dst) で保存する**
   - 例:  
     `core:knife.kitchen-001  -- core:use-purpose-001 -->  core:cut.with_blade-001`
   - meaning_triples は **削除・上書き禁止**。歴史アーカイブとして保持。

2. **単語と意味を完全に分離**
   - 単語は expr_node / expr_links
   - 意味は core_concept + meaning_triples
   - 地域差・時代差・スラング・死語などは expr_links.conditions_json で扱う

3. **条件・証拠・統計を分離**
   - conditions_json: 命題が成立する「文脈条件」（domain/region/era/lang/freq など）
   - triple_evidence: その triple を支持/否定する「証拠」
   - triple_stats: 時代とともに変化する「常識度・使用頻度」

4. **逆方向 triple は OS が自動生成**
   - 入力: (A, core:material-001, B)  
   - 自動生成: (B, core:material-for-001, A)  
   - conditions / polarity はコピーされ、全方向推論が可能になる。

5. **9要素ビューは「説明モデル」であって保存しない**
   - core をフォーカス（主役）として meaning_triples から  
     WHO/WHAT/WHY/HOW/WHERE/WHEN/OUTCOME/STATE/DISC を動的レンダリングする。
   - DBに保存すると整合性が崩れるため、**関数（ビュー生成ロジック）のみ**。

## 実装の優先度（推奨）

付録Bより抜粋：

1. core_concept / rel_concept 登録と正逆生成
2. meaning_triples（conditions_json 付き）
3. expr_links（地域差・表記差）
4. triple_evidence（辞書 → 人 → corpus → AIの順）
5. triple_stats（後からでもOK）
6. 9要素ビュー（レンダリングのみ）

## 想定するステージ

- **A: 手入力中心** – 意味を手で構築（現在）
- **B: 統計 / UD / 辞書から半自動生成** – これが短期目標
- **C: 自動推論型** – OS自身が core/triple を提案
- **D: 科学推論型** – 意味→推論→世界構築（長期的な未来モデル）

## 貢献・コラボレーション

- 現段階では仕様整備フェーズです。
- Issue / Pull Request でのフィードバックや、ドメイン別の triple 例（料理・医学・法律など）の提案を歓迎します。
- データ形式は CSV / JSON / RDB のいずれにもマッピングできるように設計されています。
