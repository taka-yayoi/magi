# MAGI System

**Multiple AI General Intelligence** - 3つのAIモデルによる多数決型意思決定システム

## 概要

MAGI Systemは、新世紀エヴァンゲリオンに登場するスーパーコンピュータシステムMAGIにインスパイアされた、3つの異なるAIモデルを使った意思決定支援システムです。Databricks Apps上で動作するStreamlitアプリケーションとして実装されています。

### 3つのシステム

- **MELCHIOR** (GPT-5) - 科学者としての人格
- **BALTHASAR** (Claude Opus 4.1) - 母としての人格
- **CASPER** (Gemini 2.5 Pro) - 女性としての人格

各システムは独自の人格を持ち、同じ提案や質問に対して異なる視点から判断を下します。

## 機能

### 1. 賛成/反対モード（メイン機能）
エヴァンゲリオンのMAGI方式を忠実に再現した、提案の承認/却下システムです。

- 提案を入力すると、3つのMAGIシステムが賛成/反対を投票
- **2対1の多数決で決定**（承認/却下/保留）
- リアルタイムで投票過程を可視化（⏳ 待機中 → 🔄 投票中 → ✅ 完了）
- 各システムの判断理由を詳細表示
- サンプル提案ボタンで簡単にテスト可能

**サンプル提案:**
- 💼 リモートワーク全面導入
- 🤖 AI採用選考導入
- 📅 週休3日制導入

### 2. 質問分析モード
3つの異なる人格から同じ質問への回答を取得し、比較分析します。

- 同じ質問を3つのモデルに並列送信
- 各モデルの回答を比較表示
- コンセンサス分析により最適な回答を選択
- 一致度スコアの表示

**サンプル質問:**
- 🤖 AIの未来
- 🌍 気候変動
- 💼 リモートワーク

### 3. 選択肢投票モード
複数の選択肢から3つのモデルに投票させ、最多得票を選択します。

- 複数の選択肢（2-4個）に対して投票
- 投票結果を集計・可視化
- 最多得票の選択肢を表示

**サンプル投票:**
- 💻 技術選定
- 🍕 ランチ選び
- 📚 学習言語

### 4. 信頼性機能
- API呼び出しの自動リトライ（最大3回）
- 502/503/504エラー時の指数バックオフ
- エラーハンドリングと詳細なエラー表示
- タイムアウト処理（180秒）

### 5. リアルタイム可視化
- 各モデルの処理状況をリアルタイム表示
- ⏳ 待機中 → 🔄 処理中 → ✅ 完了 / ❌ エラー / ⏱️ タイムアウト
- 投票/分析過程を視覚的に確認可能

## デプロイ方法

### Databricks Appsでのデプロイ（推奨）

1. **ファイルのアップロード**
   ```bash
   databricks workspace import-dir . /Workspace/Users/<your-email>/magi --profile <your-profile>
   ```

2. **アプリの作成**
   - Databricksワークスペースで **Apps** に移動
   - **Create App** をクリック
   - 以下を設定:
     - **Name**: `magi-system` (任意の名前)
     - **Source code path**: `/Workspace/Users/<your-email>/magi`
   - **Create** をクリック

3. **自動デプロイ**
   - Databricks Appsが自動的に:
     - `requirements.txt`から依存関係をインストール
     - `app.yaml`の設定に従ってStreamlitアプリを起動
     - 環境変数（`DATABRICKS_HOST`、`DATABRICKS_TOKEN`）を自動設定
     - 公開URLを生成

### ローカルでの開発（オプション）

1. **依存関係のインストール**
   ```bash
   pip install -r requirements.txt
   ```

2. **環境変数の設定**
   ```bash
   export DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
   export DATABRICKS_TOKEN=your_token_here
   ```

3. **アプリの起動**
   ```bash
   streamlit run app.py
   ```

## 使い方

1. Databricks Appsの公開URLにアクセス
2. タブを選択:
   - **⚖️ 賛成/反対**: 提案の承認/却下（メイン機能）
   - **💬 質問分析**: 3つの視点から回答を比較
   - **📊 選択肢投票**: 選択肢への投票
3. サンプルボタンをクリック、または独自の提案/質問を入力
4. 投票/分析開始ボタンをクリック
5. リアルタイムで処理過程を確認
6. 結果を確認

## ファイル構成

```
magi/
├── app.py              # 統合Streamlitアプリケーション（全機能を含む）
├── app.yaml            # Databricks Apps設定ファイル
├── requirements.txt    # Python依存関係
├── .gitignore          # Git無視ファイル
└── README.md           # このファイル
```

## 技術スタック

- **Streamlit 1.28+**: WebUIフレームワーク
- **Python 3.8+**: プログラミング言語
- **Databricks SDK**: 認証とAPI連携
- **Databricks Foundation Model API**: 以下の3つのモデルへのアクセス
  - GPT-5 (OpenAI) - reasoning model
  - Claude Opus 4.1 (Anthropic)
  - Gemini 2.5 Pro (Google)
- **Requests**: HTTP通信ライブラリ
- **concurrent.futures**: 並列処理

## アーキテクチャ

### 人格システム
各MAGIシステムには独自の人格が設定されています：

- **MELCHIOR (科学者)**: 論理的思考、客観的データ分析、科学的根拠を重視
- **BALTHASAR (母)**: 人間性、感情的側面、倫理的・人道的観点を重視
- **CASPER (女性)**: 直感、実践的知恵、バランスの取れた現実的判断を重視

システムプロンプトで各人格を明確に定義し、回答に反映させています。

### 認証
- Databricks SDKの`Config()`を使用して自動認証
- Databricks Appsが提供する環境変数（`DATABRICKS_HOST`、`DATABRICKS_TOKEN`）から認証情報を取得

### 並列処理
- `concurrent.futures.ThreadPoolExecutor`を使用して3つのモデルに並列リクエスト
- リアルタイムでステータスを更新
- タイムアウト設定で長時間実行を防止（180秒）

### エラーハンドリング
- 一時的なエラー（502, 503, 504, 429）は自動リトライ
- 指数バックオフで待機時間を調整（1秒 → 2秒 → 4秒）
- 恒久的なエラー（400など）は即座に失敗として返す

### モデル固有の設定
- **GPT-5**:
  - `temperature`パラメータ非対応（デフォルト値1を使用）
  - reasoning modelのため`max_tokens=16000`を設定
- **Claude Opus 4.1, Gemini 2.5 Pro**: `max_tokens=4000`、`temperature=0.7`

## 注意事項

- GPT-5は`temperature`パラメータをサポートしていません（デフォルト値1を使用）
- GPT-5はreasoning modelのため、推論トークンを多く消費します（max_tokens=16000）
- 3つのモデルへの並列リクエストにより、APIコストが発生します
- Databricks Appsのサービスプリンシパルに適切な権限が必要です

## ライセンス

MIT License

## 参考資料

- [Databricks Apps](https://docs.databricks.com/en/dev-tools/databricks-apps/index.html)
- [Databricks Apps Streamlitチュートリアル](https://docs.databricks.com/aws/ja/dev-tools/databricks-apps/tutorial-streamlit)
- [Databricks Foundation Model API](https://docs.databricks.com/machine-learning/foundation-models/index.html)
- [Databricks SDK for Python](https://docs.databricks.com/dev-tools/sdk-python.html)
- [Streamlit Documentation](https://docs.streamlit.io/)

## トラブルシューティング

### 502 Bad Gateway エラー
- GPT-5エンドポイントの一時的な問題の可能性
- 自動リトライが3回実行されます
- 再度試すか、しばらく待ってから実行してください

### GPT-5が「回答なし（max_tokensに達しました）」
- GPT-5はreasoning modelのため、推論に多くのトークンを消費します
- 現在`max_tokens=16000`に設定されていますが、複雑な質問ではさらに必要な場合があります

### 認証エラー
- Databricks Appsのサービスプリンシパルに適切な権限があることを確認
- Foundation Modelエンドポイントへのアクセス権限が必要です

### アプリがクラッシュする
- ログを確認: Databricks Apps UIの「Logs」タブ
- `app.yaml`の設定を確認
- 依存関係が正しくインストールされているか確認

### タイムアウトエラー
- デフォルトのタイムアウトは180秒です
- 複雑な質問や長い提案の場合、一部のモデルがタイムアウトする可能性があります
- その場合、完了したモデルの結果のみ表示されます
