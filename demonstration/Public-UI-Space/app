# app.py - パブリック UI スペース（プライベート バックエンド スペースを gradio_client で叩く）

インポートOS
JSONをインポート
gradio をgrとしてインポート
gradio_clientからクライアントをインポート

# ==== バックエンドスペースのIDを書く場所 ====
# 例: https://huggingface.co/spaces/akito/mini-os-backend
# の場合 → "akito/mini-os-backend"
BACKEND_SPACE_ID = "aki117463/mini-meaning-os"

#秘密に保存したついでにを
HF_TOKEN = os.environ[ "HF_TOKEN" ]

#gradio_client でプライベートスペースに接続
backend_client = クライアント(BACKEND_SPACE_ID、トークン=HF_TOKEN)


# ==========================
#バックエンド呼び出し関数
# ==========================
def  call_backend (テキスト: str、 言語: str ):
    「」
    パブリックUIから呼ばれる1回分の処理。
    Private Backend Space に入力を渡し、結果(dict)を受け取ります。
    「」
    text = (テキストまたは "" ).strip()
     テキストでない場合:
        return  "質問を入力してください。" , "{}"

    試す：
        # バックエンドのquery_fn(text, lang) に対応
        # backend側はdictを返す想定：
        # { "回答テキスト": "...", "生データ": {...} }
        データ = backend_client.predict(
            文章、
            ラン、
            # api_name="/predict" # 必要なら付けるが、単一エンドポイントなら省略でOKなことが多い
        ）
    except Exceptionをeとして:
        return  f"バックエンドAPIエラー: {e} "、"{}"

    #gradio_client は dict をそのまま返してくれる想定
     isinstance (data, dict )でない 場合:
        #もしかしたら違う形だったときの保険
        試す：
            データ = json.loads( str (データ))
        例外を除く:
            return  f"予期しないバックエンド応答: { type (data)} "、"{}"

    Answer_text = data.get( "answer_text" , "（答えなし）" )
    raw_json = json.dumps(data.get( "raw" , {}), ensure_ascii= False , indent= 2 )

    answer_text、raw_jsonを返す


# ==========================
# Gradio UI レイアウト
# ==========================
gr.Blocks()をデモとして使用します:

    gr.マークダウン(
        「」
        # ミニ意味OS（パブリックUI）
        日本語 / 日本語で質問できます（実際の処理は Private Backend が実行）
        **日本語の例:**  
        - 包丁の用途は何ですか？  
        - 包丁の素材は？  
        - 包丁の分類は？  
        - 切るのに使う道具は？  
        - 包丁の英語は？
        **英語の例:**  
        - ナイフは何に使いますか？  
        - 日本の包丁は何でできていますか？  
        - ナイフはどのカテゴリーに入りますか?  
        「」
    ）

    gr.Row()を使用する場合:
        inp = gr.テキストボックス(
            label= "質問 / 質問" ,
            placeholder= "例: ナイフの用途は何ですか? / ナイフは何に使用されますか?"、
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
        label= "答え（簡易） / 短い答え" ,
        インタラクティブ= False、
    ）

    out_json = gr.コード(
        label= "生JSON / 生のJSON" ,
        言語 = "json"、
    ）

    btn.click(
        fn=コールバックエンド、
        入力=[inp, lang_select],
        出力=[out_answer, out_json],
    ）


__name__ == "__main__"の場合:
    デモ.launch()
