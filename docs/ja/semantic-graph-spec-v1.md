
## 第1章 設計思想

### 1.1 目的

本仕様は、自然言語における「意味」を、**統計・文脈・表現に依存しない永続的な意味構造**として保存する方式を定義する。

本方式は、辞書・コーパス・人間・AI・歴史変化の影響を受けつつも、  
**意味本体を不変なデータ構造として保存し続けること**を目的とする。

### 1.2 基本理念

| 範囲 | 保存対象                | 性質                  |
|------|-------------------------|-----------------------|
| 意味 | core_concept + 三連結   | 不変 (immutable)      |
| 文脈 | conditions_json         | 可変 (contextual)     |
| 証拠 | triple_evidence         | 追加/対立可           |
| 常識 | triple_stats            | 変化・減衰・逆転可能 |
| 表現 | expr_links              | 言語依存・地域依存    |
| 説明 | 9要素ビュー             | 保存禁止、動的生成    |

- 意味（core + triple）は歴史に保存し、  
  常識・証拠・表現は変化に任せる。

> 言語OSは、事実ではなく **関係としての意味** を保存する。

### 1.3 三連結による意味表現

本OSは、意味を以下の三要素の関係（S, R, D）として保存する。

`(src_concept, rel_concept, dst_concept)`

例：

```text
(core:knife.kitchen-001, core:use-purpose-001, core:cut.with_blade-001)
````

### 1.4 ラベルと意味の分離

* 単語（文字列）は、**意味ではない**。

* 単語は expr_node として保存され、
  意味コア（core_concept）へのラベル付与として扱う。

* 単語 = 言語上の表現

* 意味 = core_concept の ネットワーク位置

### 1.5 不変データ vs 可変データ

| 種別 | 例                 | 変化   |
| -- | ----------------- | ---- |
| 不変 | 包丁・切る・料理、包丁→用途→切る | 消さない |
| 可変 | 地域差、時代差、禁止/許可、流行  | 変わる  |
| 追加 | 証拠、使用回数、統計データ     | 増える  |
| 減衰 | 使用頻度の低下、死語化       | 減る   |
| 逆転 | 「禁止」→「解禁」など       | 反転可  |

> 意味は消さず、常識だけが変化する構造を採用する。

---

## 第2章 ノード仕様

### 2.1 core_concept（意味コア）

表現（単語）に依存しない純粋な意味単位。

例：

* 「料理用包丁」
* 「刃物で切る行為」
* 「鋼材」
* 「料理ドメイン」 など

特長:

* 多言語間で共有可能。
* 上位/下位クラスは概念間関係と属性の絞り込みから導出する。

**命名規則（推奨）**

```text
core:<概念名>.<分類>-<番号>
```

例：

* `core:knife.kitchen-001`
* `core:cut.with_blade-001`
* `core:domain.cooking-001`

### 2.2 expr_node（表現ラベル）

意味ではなく、**言語表現**を表すノード。

* 方言・地域・時代差は expr_links 側に保持する。

例：

* `"包丁_ja"`
* `"knife_en"`
* `"大判焼き_ja"`

1つの core_concept に複数の expr_node を紐付け可能。

### 2.3 rel_concept（関係コア）

**意味関係も core として扱う。**

例：用途・素材・分類・役割・状態・部位・原料・所属ドメイン。

| 種類          | 例                      |
| ----------- | ---------------------- |
| 用途          | `core:use-purpose-001` |
| 素材          | `core:material-001`    |
| 原料          | `core:ingredient-001`  |
| 分類          | `core:category-001`    |
| 役割          | `core:role-001`        |
| 状態          | `core:state-001`       |
| 部位          | `core:part-001`        |
| 所属ドメイン（第1層） | `core:domain-001`      |

### 2.4 rel_concept 正逆ペアの原則

`(src, rel, dst)` を登録するとき、**逆方向 triple を OS が自動生成**する。

例：

```text
(core:knife.kitchen-001, core:domain-001, core:domain.cooking-001)
```

自動生成：

```text
(core:domain.cooking-001, core:domain-of-001, core:knife.kitchen-001)
```

* 逆 triple の conditions と polarity は **正方向 triple を完全にコピー** する。

### 2.5 domain ノード（意味領域）

分野そのものも core として扱う。

例：

* `core:domain.cooking-001`
* `core:domain.medicine-001`
* `core:domain.sports-001`

> 意味としての領域（所属） を core で保持し、
> 特定 triple の「成立条件」としての domain は conditions_json に保持する（後述）。

---

## 第3章 意味三連結仕様（meaning_triples）

### 3.1 目的

本章は、意味命題を保存するための **不変（immutable）データ構造**として、
三連結 `(src, rel, dst)` をどのように扱うかを定義する。

* meaning_triples は OS の **歴史層** であり、**削除禁止**。
* 変更は「条件・証拠・統計」が担う。

### 3.2 三連結構造

```text
(src_concept_id, rel_concept_id, dst_concept_id)
```

| フィールド           | 型      | 説明                          |
| --------------- | ------ | --------------------------- |
| triple_id       | UUID   | 一意ID                        |
| src_concept_id  | core:* | 主体                          |
| rel_concept_id  | core:* | 関係                          |
| dst_concept_id  | core:* | 対象                          |
| conditions_json | JSON   | 成立条件（後述）                    |
| polarity        | enum   | positive / negative         |
| status          | enum   | draft / active / deprecated |
| note            | text   | 任意の備考                       |

### 3.3 polarity（命題符号）

| 値        | 意味                         |
| -------- | -------------------------- |
| positive | その条件下で S-R-D が成立する         |
| negative | その条件下で S-R-D は成立しない／禁止／不可能 |

例：肯定命題

```text
(core:knife.kitchen-001, core:use-purpose-001, core:cut.with_blade-001)
polarity = positive
```

例：否定命題（禁止）

```text
(core:raw-chicken-001, core:use-purpose-001, core:sashimi-001)
polarity = negative
conditions = {domain:["cooking"], region:["JP"]}
```

### 3.4 逆方向 triple 自動生成

三連結登録時、OSは必ず **正逆ペアの triple** を生成する。

| 入力                          | 自動生成                            |
| --------------------------- | ------------------------------- |
| `(A, core:material-001, B)` | `(B, core:material-for-001, A)` |
| `(A, core:domain-001, B)`   | `(B, core:domain-of-001, A)`    |

* 逆 triple の conditions と polarity は **正方向 triple を完全コピー**。

### 3.5 三連結は「意味」であり、証拠ではない

**禁止事項（仕様）**

| 操作            | 理由             |
| ------------- | -------------- |
| triple の削除    | 歴史改ざんになるため禁止   |
| triple の上書き   | 証拠や条件で解釈を更新すべき |
| triple の合併・統合 | 意味差が消えるため      |

* 三連結は、人間やAIの解釈ミスすら含んで歴史保存し、
  その正否を **後段の evidence / stats で判断**する。

---

## 第4章 条件仕様（conditions_json）

### 4.1 役割

conditions_json は、三連結の **成立条件（文脈）** を表す。

* 意味そのものではなく、**成立範囲** を制御する。
* 条件が変わっても三連結は変わらない。

### 4.2 JSONキー一覧

| キー         | 意味例                           |
| ---------- | ----------------------------- |
| domain     | `["cooking","medicine"]`      |
| region     | `["JP","JP-Kansai"]`          |
| era        | `["Showa","Heisei"]`          |
| year_range | `[1950,2000]`                 |
| lang       | `"ja"`                        |
| register   | `"slang","academic"`          |
| medium     | `"speech","net","literature"` |
| freq       | `0.8` （確率／頻度の傾向）              |

### 4.3 条件の結合仕様

* 条件は **AND** で解釈する。

例：

```json
{ "domain":["cooking"], "region":["JP-Kansai"] }
```

→ 「関西料理領域で成立」

* キーがない＝制約なし
  → `{}` は「普遍条件（一般的に成立）」を意味する。
* 空配列や `null` の使用は禁止
  → キーごと削除する。

### 4.4 domain の二層性（重要）

| 役割        | 保存場所                   | 例              |
| --------- | ---------------------- | -------------- |
| 概念が属する世界  | triple：core:domain-001 | 包丁は料理の道具       |
| 関係が成立する世界 | conditions.domain      | 「料理領域で」切る用途が成立 |

* 包丁は料理の道具 → 三連結
* 包丁→切る用途→料理で成立 → conditions

### 4.5 region / era / lang の粒度

* 保存はフラットラベル

例：

```json
"region": ["JP-Kyoto"]
```

* 解釈はOS側で階層処理

  * `"JP-Kyoto" ⊂ "JP"`
  * `"Edo" = [1603–1868]` （内部辞書）

> DBは複雑にせず、解釈側がツリー／時間帯処理を持つ。

### 4.6 freq の扱い

* freq は成立傾向を表す統計値（0.0〜1.0 推奨）。

例：

* `{ "freq": 0.9 }` → よく成立する
* `{ "freq": 0.3 }` → あまり成立しないが例外あり

freqは「条件の一部」であり、
**常識度（stats.confidence）とは別物**。

### 4.7 条件と triple/evidence/stats の境界

| データ        | 何を表すか   | 変動        |
| ---------- | ------- | --------- |
| triple     | 命題（意味）  | 不変        |
| conditions | 文脈・成立範囲 | 不変 or 追加  |
| evidence   | 根拠      | 追加・対立可    |
| stats      | 常識・使用   | 変動・減衰・逆転可 |

* 条件は「真偽の前提」
* 証拠は「根拠」
* 統計は「社会変化」

> ここまでが **不変層（意味 + 条件）** の仕様。

---

## 第5章 証拠仕様（triple_evidence）

### 5.1 目的

triple_evidence は、三連結（meaning_triples）に対する **根拠** を記録する。

* 複数の証拠が同一 triple を支持・否定し得る。
* 証拠は意味を修正しない。
* 意味は、証拠によって査定される。

### 5.2 データ構造

**テーブル： `triple_evidence`**

| カラム           | 型         | 説明                                              |
| ------------- | --------- | ----------------------------------------------- |
| evidence_id   | UUID      | 証拠レコードID                                        |
| triple_id     | FK        | meaning_triples への参照                            |
| evidence_type | enum      | dictionary / corpus / human / rule / hypothesis |
| source_kind   | enum      | reference / human / corpus / ai / rule          |
| stance        | enum      | positive / negative                             |
| weight        | float     | 0.0〜1.0 推奨                                      |
| source_detail | text      | 辞書ID・URL・文献・文番号など                               |
| note          | text      | コメント                                            |
| created_at    | timestamp | 登録日時                                            |

### 5.3 evidence_type（方法）

| 種類         | 説明                   |
| ---------- | -------------------- |
| dictionary | 辞書・百科・辞典に掲載された事実     |
| corpus     | 文書・Web・SNS などの実例     |
| human      | 専門家・編集者・ユーザの判断       |
| rule       | 体系的なルール（料理法、法律、化学など） |
| hypothesis | 仮説、または未検証の推測         |

### 5.4 source_kind（ソース属性）

| 値         | 説明              |
| --------- | --------------- |
| reference | 権威ある資料（辞書・論文など） |
| corpus    | 検索集合・ニュース・SNS   |
| human     | ユーザ個人           |
| ai        | NLPモデル・LLM      |
| rule      | 体系化された専門ルール     |

### 5.5 stance（支持/反対）

* `positive` : triple が成立する根拠
* `negative` : triple が成立しない根拠

例：

* SNS投稿：「鶏刺し最高」 → positive
* 厚労省ガイドライン：「生鶏肉は生食禁止」 → negative

肯定 vs 否定の両方が証拠になる。

### 5.6 weight（信頼度）

weight は単一 evidence の信頼度指標。

* 0.0～1.0 の実数
* ユーザ設定 or 自動算出（将来）

例：

| type  | weight の目安 |
| ----- | ---------- |
| 辞書・論文 | 0.9        |
| 法律・規制 | 1          |
| 個人ブログ | 0.3        |
| 生成AI  | 0.4        |
| 体系ルール | 0.8〜1.0    |

### 5.7 triple vs evidence の関係

| 役割       | 保存物          | 更新   |
| -------- | ------------ | ---- |
| triple   | 命題           | 不変   |
| evidence | 命題を支持/否定する根拠 | 追加のみ |
| stats    | 常識の量的変化      | 更新あり |

> triple は墓石、evidence は裁判資料、stats は世論。

---

## 第6章 常識（統計）仕様（triple_stats）

### 6.1 目的

triple_stats は、三連結の **社会的成立度（常識度）** を扱う。

* 人々が今どう解釈しているか
* どの程度使われているか
* どんな条件下で主流か

evidence が「根拠」、
stats は「世論」である。

### 6.2 データ構造

**テーブル： `triple_stats`**

| カラム          | 型         | 説明                   |
| ------------ | --------- | -------------------- |
| triple_id    | FK        | meaning_triples への参照 |
| usage_count  | integer   | API、GUI使用回数          |
| corpus_count | integer   | 対象文書での登場回数           |
| stance_score | float     | 支持-反対値（0.0〜1.0）      |
| confidence   | float     | 総合常識度（0.0〜1.0）       |
| last_used_at | timestamp | 最後に使用された日時           |

### 6.3 confidence（常識度）の算出

例：

```text
confidence = (stance_score * 0.7) + (normalized(corpus_count) * 0.3)
```

* 計算式はバージョン可能（実装改良を許容）。

### 6.4 decay（時代減衰）

* corpus_count 等は **時間とともに減衰**していく。
* 過去の常識が「過去の常識」として扱われる。

```text
corpus_count = corpus_count * 0.99^(years_elapsed)
```

> 意味は残る。常識だけが古くなる。

### 6.5 常識の逆転（例）

| 時代   | 命題        | 立場       |
| ---- | --------- | -------- |
| 1960 | 喫煙→飲食店で許可 | positive |
| 2025 | 喫煙→飲食店で禁止 | negative |

* triple は同じ
* evidence と stats が逆転する

### 6.6 triple/evidence/stats の役割比較

| 要素       | 具体例         | 変化     |
| -------- | ----------- | ------ |
| triple   | 包丁→用途→切る    | 不変     |
| evidence | 厚労省論文、SNS投稿 | 追加のみ   |
| stats    | SNS頻度・常識度   | 変動・逆転可 |

**ここまでのまとめ（不変層 + 評価層）**

| 層   | 実体                         | 性質       |
| --- | -------------------------- | -------- |
| 不変層 | core + triple + conditions | 保存のみ     |
| 評価層 | evidence + stats           | 追加・更新・逆転 |

> ⛓ OSは意味の歴史アーカイブであり、
> その評価は社会の責任と変化に委ねられる。

---

## 第7章 表現仕様（expr_links）

### 7.1 目的

expr_links は、core_concept に **言語表現（単語・表記）を付与する層** である。

* 単語は意味ではなく、**人間向けラベル**である。
* OS は、単語ではなく **concept ID** を軸に推論する。

### 7.2 データ構造

**テーブル： `expr_links`**

| カラム             | 型      | 説明                                     |
| --------------- | ------ | -------------------------------------- |
| expr_id         | UUID   | 表現リンクの永続ID                             |
| expr_label      | string | 表現文字列（単語・表記）                           |
| core_concept_id | core:* | 対応する意味コア                               |
| conditions_json | JSON   | この表現が使われる条件（lang/region/era/...）       |
| source_kind     | enum   | reference / human / corpus / ai / rule |
| source_detail   | text   | 出典情報                                   |
| note            | text   | 内部メモ                                   |

### 7.3 単語 vs 意味（分離ルール）

| 役割   | 保存場所                   | 変更     |
| ---- | ---------------------- | ------ |
| 単語   | expr_node + expr_links | 削除/改名可 |
| 意味   | core + triple          | 不変     |
| 使用傾向 | stats                  | 変動     |

* 単語の変化（名称・流行・死語）は自由に許容し、
  意味（core）は変化させない。

### 7.4 地域差・方言・時代差の扱い

例：

```text
expr_label: "今川焼"
conditions: {lang:"ja", region:["JP-Kanto"]}

expr_label: "大判焼き"
conditions: {lang:"ja", region:["JP-Hokkaido"]}

expr_label: "回転焼き"
conditions: {lang:"ja", region:["JP-Kansai"]}
```

* すべて同じ `core:imagawa-yaki-001` に紐づけられる。

### 7.5 expr_conditions と triple_conditions の違い

| 目的        | 保存場所       | 例                 |
| --------- | ---------- | ----------------- |
| 表現が成立する領域 | expr_links | 「大判焼き」が北海道で使われる   |
| 意味が成立する領域 | triple     | 生鶏肉は刺身にならない（料理領域） |

### 7.6 多義語の扱い

多義語（例：bank）は、複数 core_concept とリンクするだけ。

```text
"bank_en" → core:bank.river-001
"bank_en" → core:bank.finance-001
```

OS では同じ単語でも、意味（core）が複数存在し、それぞれ独立して扱われる。

---

## 第8章 9要素ビュー（読み取りモデル）

### 8.1 ビューの役割

9要素（WHO / WHAT / WHY / HOW / WHERE / WHEN / OUTCOME / STATE + TARGET/DISC）は、
**意味の説明と出力形式** であり、保存禁止の動的ビューである。

* 保存するのは triple、説明するのは view。

### 8.2 ビュー禁止ルール

| 操作            | 状態  |
| ------------- | --- |
| 9要素ビューのDB保存   | ❌禁止 |
| ビューの手動編集      | ❌禁止 |
| triple から自動生成 | ✔許可 |

ビューは再現（render）するための**関数**であり、データではない。

### 8.3 focus（主役）判定

ビュー生成時に、「どの core を主役とみなすか」を決める。

* フォーカスに基づき、 triple の意味が変換される。

例：包丁を主役にするビュー

```text
(core:knife.kitchen-001, core:material-001, core:steel-001)
→ HOW: 鋼でできている
```

例：鋼を主役にするビュー

```text
(core:steel-001, core:material-for-001, core:knife.kitchen-001)
→ OUTCOME/TARGET: 鋼は包丁に利用される
```

> triple は同じでも、誰を主役に見るかで意味が変わる。

### 8.4 rel_concept → スロット変換表

| rel         | 主に対応するスロット       |
| ----------- | ---------------- |
| use-purpose | OUTCOME / TARGET |
| material    | HOW              |
| ingredient  | WHAT / HOW       |
| category    | WHAT             |
| role        | WHY / WHAT       |
| part        | WHERE / STATE    |
| state       | STATE            |
| domain      | DISC（領域説明）       |

* 正方向と逆方向で “主役側に割り当てるスロット” が変わる。

### 8.5 正方向/逆方向での表示差

例：

```text
(core:knife, use-purpose, core:cut)
```

| 主役    | 表示    |
| ----- | ----- |
| knife | 用途：切る |
| cut   | 道具：包丁 |

### 8.6 包丁プロフィール（例：自動ビュー）

例として、`core:knife.kitchen-001` をフォーカスしたときの 9要素ビュー：

* WHO: なし（道具は主体ではない）
* WHAT: 包丁（料理用刃物）
* WHY: 調理の目的達成
* HOW: 鋼/セラミック等で作られる
* WHERE: 台所/厨房で使用
* WHEN: 調理時
* OUTCOME: 切る
* STATE: 切れ味・錆・硬さ
* DISC: 料理ドメイン

すべて triple から導出可能
→ ビューは triple の**解説者**

> ここで、OS 性能としての完全な意味閲覧が成立。

---

## 第9章 設計原則まとめ

### 9.1 OS が保存するもの

| 種類              | 保存 | 性質         |
| --------------- | -- | ---------- |
| core_concept    | 〇  | 不変         |
| meaning_triples | 〇  | 不変         |
| conditions_json | 〇  | 不変 or 追加のみ |
| triple_evidence | 〇  | 追加のみ       |
| triple_stats    | 〇  | 更新・減衰・逆転   |
| expr_links      | 〇  | 追加・変更・削除可  |
| 9-slot view     | ❌  | 保存禁止（生成のみ） |

> OS は 意味だけを不変層に保存し、
> 解釈は変動層に任せる。

### 9.2 意味の定義

* 意味とは、core_concept が meaning_triples により占める**ネットワーク位置**である。
* 単独の “定義文” を保存しない。
* 他概念との **関係構造** が意味となる。

### 9.3 単語と意味の分離

| 単語     | 意味         |
| ------ | ---------- |
| 表現     | 概念         |
| 時代で変化  | 変わらない      |
| 地域差あり  | 地域差に影響されない |
| データ削除可 | データ削除禁止    |

* 単語は「ラベル」
* 意味は「ネットワーク構造」

### 9.4 逆方向 triple の原則

* 人間（またはAI）は **正方向 triple のみ入力**する。
* 逆方向 triple は OS が必ず自動生成。
* 条件・肯否は全コピー。

目的：

* 人間は向きを意識するだけで良い
* OS 側は **全方向の推論** が可能になる

### 9.5 domain の二層構造

| 用途     | 何としてのドメインか   | 保存場所       |
| ------ | ------------ | ---------- |
| 概念所属   | 包丁は料理の道具     | 三連結        |
| 命題成立範囲 | 料理領域で切る用途が成立 | conditions |

* 領域（domain）は**概念**にも**条件**にも現れるが、役割が異なる。

### 9.6 常識は事実ではない

| 種別       | 内容       | 変化    |
| -------- | -------- | ----- |
| meaning  | 事実ではなく命題 | 不変    |
| evidence | 根拠       | 追加    |
| stats    | 常識       | 変化    |
| 表現       | 単語       | 変化・消滅 |

> OS は辞書ではなく **意味の歴史アーカイブ**
> 常識は遷移可能な “社会の状態”

### 9.7 OS の未来モデル

| モデル | 内容                       | 本システムの位置 |
| --- | ------------------------ | -------- |
| A   | 手入力中心 – 意味の手作業構築         | 現状       |
| B   | 統計/UD/辞書から半自動生成          | 短期目標     |
| C   | 自動推論型 – core/triple 自律生成 | 長期目標     |
| D   | 科学推論型 – 意味→推論→世界構築       | 未来構想     |

現段階では **モデルBに向けてAを堅牢に設計**。
未来のC/Dでは、OS自身が意味を提案する。

---

## 📎 付録A：禁止事項まとめ

| 操作          | 理由                |
| ----------- | ----------------- |
| triple の削除  | 歴史改ざんになる          |
| triple の上書き | 条件・証拠・統計で解釈すべき    |
| ビュー保存       | 説明をデータ化すると矛盾する    |
| core の削除    | 全ての triple が破壊される |
| 条件の空配列/null | 意味が曖昧化する          |

---

## 📎 付録B：推奨実装優先度

| 順位 | 対象                               |
| -- | -------------------------------- |
| 1  | core_concept／rel_concept 登録と正逆生成 |
| 2  | meaning_triples（条件付き）実装          |
| 3  | expr_links（地域/表記差）               |
| 4  | evidence（辞書→人→corpus→AIの順）       |
| 5  | stats（後から実装で十分）                  |
| 6  | view（render のみ）                  |

---

## 📎 付録C：推奨クエリ例（先行実装）

**包丁の用途一覧**

```sql
SELECT dst_concept_id
FROM meaning_triples
WHERE src_concept_id = 'core:knife.kitchen-001'
  AND rel_concept_id = 'core:use-purpose-001';
```

**刃物として分類されるもの**

```sql
SELECT src_concept_id
FROM meaning_triples
WHERE rel_concept_id = 'core:category-001'
  AND dst_concept_id = 'core:knife.blade-tool-001';
```

**“切る道具” グループ（ビュー）**

```sql
SELECT src_concept_id
FROM meaning_triples
WHERE rel_concept_id = 'core:use-purpose-001'
  AND dst_concept_id = 'core:cut.with_blade-001';
```

---

## 第10章 データ管理仕様（管理形式と型）

本章では、第1〜9章で定義した論理モデルを、
実際のデータ管理（保存形式・編集形式・型）として定義する。

* **保存形式（internal）**：
  OS が永続的に保持するテーブル／CSV構造。
  不変層（core・triple・conditions）＋変動層（evidence・stats・expr）。

* **編集形式（editor view）**：
  人間が編集・閲覧するためのビュー。
  IDやJSONは極力隠し、単語・ラベル・分解された列で扱う。

### 10.1 型の基本方針

| 型名        | 説明                            |
| --------- | ----------------------------- |
| string    | 任意の文字列（UTF-8）                 |
| uuid      | UUID または一意なID文字列（t00000001 等） |
| core_id   | `core_concepts.core_id` への参照  |
| json      | JSON文字列。内部では構造化、エディタでは列で編集    |
| enum      | あらかじめ定義された文字列のどれか             |
| int       | 整数                            |
| float     | 浮動小数点。ここでは主に 0.0〜1.0 を想定      |
| bool      | 0/1 または true/false            |
| timestamp | 日付＋時刻                         |

### 10.2 core_concepts（意味ノード）管理

#### 10.2.1 保存形式（internal）

📌 **1) core_concepts_editor（人間が編集）**

| 列名               | 説明                | 型            | 例                      |
| ---------------- | ----------------- | ------------ | ---------------------- |
| core_id          | コア概念のID（永続・不変）    | string       | core:knife.kitchen-001 |
| can_be_relation  | relation としても使えるか | bool (0/1)   | 1                      |
| status_view      | 人向け表示用ステータス       | enum         | active                 |
| domain           | 主な適用ドメイン（; 区切り）   | string(list) | cooking;weapons        |
| region           | 主な地域（; 区切り）       | string(list) | JP;US                  |
| era              | 主な時代（; 区切り）       | string(list) | Showa;Heisei;Reiwa     |
| concept_strength | 概念としての強さ（文化的独立度）  | float        | 0.95                   |
| note             | 備考・メモ             | text         | 調理道具カテゴリ               |

📌 **2) core_concepts_internal（OS保存）**

| 列名                   | 説明                                        | 生成？           |
| -------------------- | ----------------------------------------- | ------------- |
| core_id              | editor と同じ                                | from editor   |
| can_be_relation      | editor をそのまま反映                            | from editor   |
| status_view          | editor の値をそのまま保持                          | from editor   |
| core_conditions_json | domain/region/era/concept_strength の JSON | editor から自動生成 |
| note                 | editor と同じ                                | from editor   |

---

### 10.3 meaning_triples（三連結）管理

#### 10.3.1 保存形式（internal）

**テーブル名： `meaning_triples`**

| カラム名            | 型                                   | 必須 | 説明                                        |
| --------------- | ----------------------------------- | -- | ----------------------------------------- |
| triple_id       | uuid                                | ✔  | 三連結の永続ID。不変。                              |
| src_core_id     | core_id                             | ✔  | 主語側 core。                                 |
| rel_core_id     | core_id                             | ✔  | 関係 core（can_be_relation=1 のもの）。           |
| dst_core_id     | core_id                             | ✔  | 目的語側 core。                                |
| conditions_json | json                                | ✔  | 成立条件。domain/region/era/… を持つ。空条件 `{}` も可。 |
| polarity        | enum("positive","negative")         | ✔  | 肯定／否定命題。                                  |
| status          | enum("draft","active","deprecated") | ✔  | ドラフト／有効／非推奨。削除禁止。                         |
| is_reverse      | bool                                | ✔  | 0 = 正方向 triple、1 = OS が生成した逆方向。           |
| reverse_of      | uuid or null                        | 任意 | 逆 triple の場合、元 triple の ID。正方向は NULL。     |
| created_at      | timestamp                           | ✔  | 登録日時。                                     |
| note            | string                              | 任意 | 内部メモ（運用用）。意味ではない。                         |

#### 10.3.2 編集形式（editor view）

**テーブル／ビュー名： `meaning_triples_editor`**

| カラム名          | 型                        | 編集 | 説明                                             |
| ------------- | ------------------------ | -- | ---------------------------------------------- |
| focus_expr    | string                   | ⭕  | 主役側の表現ラベル（例：「包丁」）。内部で src_core_id に解決。         |
| rel_label     | string                   | ⭕  | 関係名（「用途」「素材」「分類」等）。内部で rel_core_id に解決。        |
| value_expr    | string                   | ⭕  | 対象側の表現ラベル（「鋼」「刃物で切る」等）。内部で dst_core_id に解決。    |
| src_core_id   | core_id                  | 自動 | 解決結果。表示のみ。                                     |
| rel_core_id   | core_id                  | 自動 | 解決結果。表示のみ。                                     |
| dst_core_id   | core_id                  | 自動 | 解決結果。表示のみ。                                     |
| domain        | string                   | ⭕  | conditions.domain用。"cooking;medicine" のように複数可。 |
| region        | string                   | ⭕  | conditions.region用。"JP;JP-Kansai" など。          |
| era           | string                   | ⭕  | conditions.era用。"Showa;Heisei" 等。              |
| year_from     | int or null              | ⭕  | conditions.year_range[0]。空なら未指定。               |
| year_to       | int or null              | ⭕  | conditions.year_range[1]。空なら未指定。               |
| lang          | string                   | ⭕  | conditions.lang。空ならキーなし。                       |
| register      | string                   | ⭕  | conditions.register。複数可。                       |
| medium        | string                   | ⭕  | conditions.medium。複数可。                         |
| freq          | float or null            | ⭕  | conditions.freq。0.0〜1.0。空ならキーなし。               |
| polarity_view | enum("肯定","否定")          | ⭕  | 人向け。保存時に polarity へ変換。                         |
| status_view   | enum("ドラフト","有効","廃止候補") | ⭕  | 人向け。保存時に status へ変換。                           |
| note          | string                   | ⭕  | 内部メモ。保存時に meaning_triples.note に入る。            |

保存時のルール：

* ラベル → core_id に解決
* domain/region/era/year/lang/register/medium/freq → conditions_json に変換
* polarity_view → `"positive"` / `"negative"` に変換
* status_view → `"draft"` / `"active"` / `"deprecated"` に変換
* **正方向 triple だけ挿入**し、OS が逆方向 triple を自動生成（`is_reverse=1`）

---

### 10.4 conditions_json（文脈条件）仕様

#### 10.4.1 保存形式（JSON）

`meaning_triples.conditions_json` および
`expr_links.conditions_json` に保存される。

JSON例：

```json
{
  "domain": ["cooking"],
  "region": ["JP-Kansai"],
  "era": ["Showa", "Heisei"],
  "year_range": [1950, 2000],
  "lang": "ja",
  "register": ["slang"],
  "medium": ["speech", "net"],
  "freq": 0.8
}
```

| キー         | 型         | 備考             |
| ---------- | --------- | -------------- |
| domain     | [string]  | 意味が成立する分野。     |
| region     | [string]  | 地域（階層の解釈はOS側）。 |
| era        | [string]  | 時代ラベル。         |
| year_range | [int,int] | 西暦範囲。          |
| lang       | string    | 主な言語。          |
| register   | [string]  | 文体。            |
| medium     | [string]  | 媒体。            |
| freq       | float     | 0.0〜1.0の成立傾向。  |

ルール：

* 条件は AND で解釈
* キーが無い＝制約なし
* 空配列 / null は禁止（キーごと削除）
* freq は 0.0〜1.0 にクリップ
* 編集ビューからの変換ルールは 10.3.2 の通り

---

### 10.5 expr_links（表現ラベル ↔ core）管理

#### 10.5.1 保存形式（internal）

**テーブル名： `expr_links`**

| カラム名            | 型                                              | 必須 | 説明                                |
| --------------- | ---------------------------------------------- | -- | --------------------------------- |
| expr_id         | uuid                                           | ✔  | 表現リンクの永続ID。                       |
| expr_label      | string                                         | ✔  | 表現文字列（単語・表記）。                     |
| core_id         | core_id                                        | ✔  | 対応する意味コア。                         |
| conditions_json | json                                           | ✔  | この表現が使われる条件（lang/region/era/...）。 |
| source_kind     | enum("reference","corpus","human","ai","rule") | ✔  | 由来の種別。                            |
| source_detail   | string                                         | 任意 | 出典情報（辞書名・URL等）。                   |
| status          | enum("active","deprecated","draft")            | ✔  | 表現の状態。削除の代わりに deprecated も可。      |
| created_at      | timestamp                                      | ✔  | 登録日時。                             |
| updated_at      | timestamp                                      | ✔  | 最終更新日時。                           |
| note            | string                                         | 任意 | 内部メモ。                             |

#### 10.5.2 編集形式（editor view）

**ビュー名： `expr_links_editor`**

| カラム名              | 型                       | 編集 | 説明                                   |
| ----------------- | ----------------------- | -- | ------------------------------------ |
| expr_label        | string                  | ⭕  | 表現文字列。                               |
| core_id_or_search | string                  | ⭕  | core を指定 or 検索して選択。保存時に core_id へ確定。 |
| lang              | string                  | ⭕  | conditions.lang。基本的に必須。              |
| region            | string                  | ⭕  | conditions.region。複数値はセミコロン区切り。      |
| era               | string                  | ⭕  | conditions.era。複数可。                  |
| register          | string                  | ⭕  | conditions.register。複数可。             |
| medium            | string                  | ⭕  | conditions.medium。複数可。               |
| freq              | float or null           | ⭕  | conditions.freq。任意。                  |
| source_kind       | enum                    | ⭕  | 由来種別。                                |
| source_detail     | string                  | ⭕  | 出典情報。                                |
| status            | enum("ドラフト","有効","非推奨") | ⭕  | 保存時に internal の status に変換。          |
| note              | string                  | ⭕  | 内部メモ。                                |

保存時：

* lang/region/era/... → conditions_json に変換
* core_id_or_search → core_id に解決
* status 表記を internal enum に変換

---

### 10.6 triple_evidence（証拠）管理

#### 10.6.1 保存形式（internal）

**テーブル名： `triple_evidence`**

| カラム名          | 型                                                       | 必須 | 説明                               |
| ------------- | ------------------------------------------------------- | -- | -------------------------------- |
| evidence_id   | uuid                                                    | ✔  | 証拠レコードID。                        |
| triple_id     | uuid                                                    | ✔  | 対象となる meaning_triples.triple_id。 |
| evidence_type | enum("dictionary","corpus","human","rule","hypothesis") | ✔  | 証拠の種類。                           |
| source_kind   | enum("reference","corpus","human","ai","rule")          | ✔  | 情報源の属性。                          |
| stance        | enum("positive","negative")                             | ✔  | 命題を支持／否定。                        |
| weight        | float                                                   | ✔  | 証拠単体の信頼度（0.0〜1.0）。               |
| source_detail | string                                                  | 任意 | 出典（辞書ID・URL・文献情報など）。             |
| note          | string                                                  | 任意 | コメント・補足。                         |
| created_at    | timestamp                                               | ✔  | 証拠が登録された日時。                      |

#### 10.6.2 編集形式（editor view）

**ビュー名： `triple_evidence_editor`**

| カラム名           | 型               | 編集 | 説明                                 |
| -------------- | --------------- | -- | ---------------------------------- |
| triple_summary | string          | 自動 | 対象 triple の人向け要約（「包丁 / 用途 / 切る」等）。 |
| triple_id      | uuid            | 自動 | 対象 triple のID。編集不可。                |
| evidence_type  | enum            | ⭕  | 証拠種別。                              |
| source_kind    | enum            | ⭕  | 情報源種別。                             |
| stance         | enum("支持","否定") | ⭕  | 保存時に "positive"/"negative" に変換。    |
| weight         | float           | ⭕  | 信頼度。                               |
| source_detail  | string          | ⭕  | 出典情報。                              |
| note           | string          | ⭕  | コメント。                              |

---

### 10.7 triple_stats（常識・統計）管理

#### 10.7.1 保存形式（internal）

**テーブル名： `triple_stats`**

| カラム名         | 型         | 必須 | 説明                      |
| ------------ | --------- | -- | ----------------------- |
| triple_id    | uuid      | ✔  | 対象 triple。PK 兼 FK。      |
| usage_count  | int       | ✔  | OS/API/GUIで参照された回数。     |
| corpus_count | int       | ✔  | コーパス上での登場回数（集計値）。       |
| stance_score | float     | ✔  | 支持/否定に基づいたスコア（0.0〜1.0）。 |
| confidence   | float     | ✔  | 総合的な常識度（0.0〜1.0）。       |
| last_used_at | timestamp | ✔  | 最後に使用された日時。             |

* 通常は **自動計算・自動更新のみ**。
  人間による直接編集は原則行わない。

#### 10.7.2 閲覧ビュー（read-only）

**ビュー名： `triple_stats_view`**

| カラム名           | 説明                      |
| -------------- | ----------------------- |
| triple_summary | 対象 triple の人向け要約。       |
| triple_id      | ID。                     |
| usage_count    | その triple がどれだけ使われているか。 |
| corpus_count   | どれだけ文に現れるか。             |
| stance_score   | 支持度。                    |
| confidence     | 常識としての強さ。               |
| last_used_at   | 最終利用日時。                 |

---

### 10.8 ビュー（9要素スロット）について

9要素ビュー（WHO/WHAT/WHY/HOW/WHERE/WHEN/OUTCOME/STATE/DISC）は
**保存禁止の動的ビュー** とする。

* データ構造としては持たず、
* core_id をフォーカスとして
  関連する meaning_triples / conditions_json / expr_links をもとに
  表示時に生成する。

---

### 10.9 まとめ：編集形式と保存形式の対応

| レイヤー            | 保存テーブル              | 編集ビュー                  | 編集可否             |
| --------------- | ------------------- | ---------------------- | ---------------- |
| core_concept    | core_concepts       | core_concepts_view     | 基本読取専用（IDとフラグのみ） |
| meaning（triple） | meaning_triples     | meaning_triples_editor | 正方向 triple のみ編集  |
| conditions      | conditions_json カラム | editor の複数列            | JSONはOSが生成       |
| expressions     | expr_links          | expr_links_editor      | 表現追加・変更・削除可      |
| evidence        | triple_evidence     | triple_evidence_editor | 追加のみ（削除は運用次第）    |
| stats           | triple_stats        | triple_stats_view      | 自動更新のみ           |
| view(9-slot)    | 保存なし                | UI上の生成のみ               | 保存禁止             |

> この第10章により、
> 第1〜9章で定義した 意味OSの抽象モデル を、
> 実際の テーブル／CSVレベルでどう管理するか が一通り定義された。

```
