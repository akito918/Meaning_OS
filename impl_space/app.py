# app.py —— HuggingFace Spaces用 Gradio UI（日本語/英語対応）

JSONをインポート
pathlibからPathをインポート

gradio をgrとしてインポート

mini_os_demoからMiniMeaningOSをインポートし、answer_ja_question、answer_en_question をインポートします。

BASE_DIR = パス(__file__).parent

# OS本体を1回ロードして使い回す
os_instance = ミニ意味OS()


def  query_fn (テキスト: str、 言語: str ):
    「」
    Gradio から呼ばれる 1 回分の書き込み処理。
    langが「ja」なら日本語質問として、「en」なら英語質問として処理します。
    「」
    text = (テキストまたは "" ).strip()
     テキストでない場合:
        return  "質問 / 質問を入力してください。" , "{}"

    lang == "ja"の場合:
        ans = answer_ja_question(os_instance, テキスト)
    それ以外：
        ans = Answer_en_question(os_instance, text)

    p_id = ans.get( "パターンID" )
    結果 = ans.get( "結果" , [])
    回答テキスト = ""

    # ==== 共通の「簡単答え」組み立て ====

    # ① 用途 / 分類 / 道具 / 翻訳（日英）
    p_idが( " USE_1"、"CAT_1"、"TOOL_FOR_1"、"TRANS_EN_1"、
                「USE_EN_1」、「CAT_EN_1」 ):
        値 = [
            r.get( "値" )
            結果のrについて
             isinstance (r, dict )かつ rに"value" が ある場合
        ]
        値の場合:
            answer_text = " / " .join( str (v) 、 v内の値)

    # ②素材（日・日）
    elif p_id ( " MAT_1"、"MAT_EN_1" ):
        結果:
            かわいい = []
            結果のrについて:
                 isinstance (r, dict )でない 場合:
                    続く
                labels = r.get( "labels" )または[r.get( "core_id" )]
                pretty.append( " / " .join( str (x) for x in labels if x))
            きれいなら：
                answer_text = " / " .join(pretty)

    # ③ プロフィール（日・日）
    p_id が( "PROFILE_1"、"PROFILE_EN_1" )に含まれている場合:
        結果と isinstance (results[ 0 ], dict )の場合:
            prof = results[ 0 ].get( "profile" , {})または{}
            メインスロット = []
            for slot in [ "WHAT" , "HOW" , "OUTCOME" , "DISC" ]:
                vals = prof.get(slot)または[]
                値の場合:
                    main_slots.append( f " {slot} : { ', ' .join( map ( str , vals))} " )
            main_slotsの場合:
                answer_text = " | " .join(main_slots)
            それ以外：
                answer_text = "プロフィール情報は利用可能です。"

    # ④ 意味差（今は日本語のみ）
    p_id == "DIFF_1"の場合:
        結果と isinstance (results[ 0 ], dict )の場合:
            diff = 結果[ 0 ]
            shared = diff.get( "shared_cores" )または[]
            only_left = diff.get( "only_left_cores" )または[]
            only_right = diff.get( "only_right_cores" )または[]
            回答テキスト = (
                f"共有 / shared: {shared} | "
                f"左のみ / 左のみ: {only_left} | "
                f"右のみ / 右のみ: {only_right} "
            ）

    # フォールバック：何か値があればそれを表示
     answer_textと結果が一致しない場合は、
        最初 = 結果[ 0 ]
         isinstance (first, dict )かつfirst に"value" が ある場合:
            answer_text = str (first[ "値" ])

     回答テキストでない場合:
        Answer_text = "（答え候補なし / 回答候補なし）"

    pretty_json = json.dumps(ans, ensure_ascii= False , indent= 2 )
    answer_text、pretty_jsonを返す


gr.Blocks()をデモとして使用します:
    gr.マークダウン(
        「」
        # ミニ意味OS（プロトタイプ）
        日本語 / 英語で質問できます。
        **日本語の例:**
        - 包丁の用途は何ですか？
        - 包丁の素材は？
        - 包丁の分類は？
        - 切るのに使う道具は？
        - 包丁の英語は？
        **英語の例:**
        - 包丁は何に使うのですか？
        - 包丁は何でできていますか？
        - ナイフはどのカテゴリーですか?
        - 包丁について教えてください。
        「」
    ）

    gr.Row()を使用する場合:
        inp = gr.テキストボックス(
            label= "質問 / 質問" ,
            placeholder= "例: 包丁の用途は何ですか? / 包丁の用途は何ですか?"、
            行数= 2、
        ）

    gr.Row()を使用する場合:
        lang_select = gr.ラジオ(
            [ "ja" , "en" ],
            値= "ja"、
            label= "言語 / 言語" ,
        ）

    btn = gr.Button( "実行 / Run" )

    out_answer = gr.Textbox(
        label= "答え（簡易） / 答え（短い）" ,
        インタラクティブ= False、
    ）

    out_json = gr.コード(
        label= "生JSON / 生のJSON" ,
        言語 = "json"、
    ）

    btn.click(
        fn=クエリfn、
        入力=[inp, lang_select],
        出力=[out_answer, out_json],
    ）

__name__ == "__main__"の場合:
    デモ.launch()
