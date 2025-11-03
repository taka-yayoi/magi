"""
MAGI System - Streamlit Web Application
全コード統合版（Databricks Apps対応）
"""
import streamlit as st
import os
import requests
from typing import Dict, List, Optional, Tuple
import concurrent.futures
from dataclasses import dataclass
import re
import time
from databricks.sdk.core import Config


# ============================================================================
# Databricks Client
# ============================================================================

class DatabricksClient:
    """Databricksのモデルにアクセスするためのクライアント"""

    def __init__(self):
        """
        Databricks SDKを使って環境変数から自動的に認証情報を取得
        """
        # Databricks SDKのConfigを使用して認証情報を自動取得
        self.cfg = Config()
        self.workspace_url = self.cfg.host.rstrip('/')

        # 認証ヘッダーを取得
        auth_headers = self.cfg.authenticate()
        self.headers = {
            **auth_headers,
            'Content-Type': 'application/json'
        }

    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4000,
        max_retries: int = 3
    ) -> Dict:
        """
        モデルにチャットリクエストを送信（リトライ機能付き）

        Args:
            model: モデル名 (e.g., "databricks-gpt-5")
            messages: チャットメッセージのリスト
            temperature: 温度パラメータ
            max_tokens: 最大トークン数
            max_retries: 最大リトライ回数

        Returns:
            APIレスポンス
        """
        endpoint = f"{self.workspace_url}/serving-endpoints/{model}/invocations"

        payload = {
            "messages": messages,
            "max_tokens": max_tokens
        }

        # GPT-5はtemperatureをサポートしていないので、それ以外のモデルのみ指定
        if "gpt-5" not in model:
            payload["temperature"] = temperature

        # リトライロジック
        last_error = None
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    endpoint,
                    headers=self.headers,
                    json=payload,
                    timeout=120
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                last_error = e

                # 502, 503, 504などの一時的なエラーの場合はリトライ
                if hasattr(e, 'response') and e.response is not None:
                    status_code = e.response.status_code
                    # 一時的なエラーの場合のみリトライ
                    if status_code in [502, 503, 504, 429]:
                        if attempt < max_retries - 1:
                            # 指数バックオフで待機
                            wait_time = (2 ** attempt) * 1
                            time.sleep(wait_time)
                            continue
                    # 400エラーなどの恒久的なエラーはリトライしない
                    else:
                        break
                else:
                    # ネットワークエラーなどもリトライ
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 1
                        time.sleep(wait_time)
                        continue

        # 全てのリトライが失敗した場合
        error_detail = str(last_error)
        try:
            if hasattr(last_error, 'response') and last_error.response is not None:
                error_detail += f"\nResponse: {last_error.response.text}"
        except:
            pass
        return {
            "error": error_detail,
            "model": model,
            "status": "failed"
        }

    def get_response_text(self, response: Dict) -> str:
        """
        APIレスポンスからテキストを抽出

        Args:
            response: APIレスポンス

        Returns:
            レスポンステキスト
        """
        if "error" in response:
            return f"エラー: {response['error']}"

        try:
            # Databricks Foundation Model APIのレスポンス形式に対応
            if "choices" in response:
                content = response["choices"][0]["message"]["content"]
                # contentが空またはNoneの場合の処理
                if not content:
                    # finish_reasonを確認
                    finish_reason = response["choices"][0].get("finish_reason", "unknown")
                    if finish_reason == "length":
                        return "回答なし（max_tokensに達しました）"
                    else:
                        return f"回答なし（finish_reason: {finish_reason}）"
                return content
            elif "predictions" in response:
                return response["predictions"][0]
            else:
                return str(response)
        except (KeyError, IndexError) as e:
            return f"レスポンスの解析に失敗: {str(e)}\n生データ: {str(response)[:200]}"


# ============================================================================
# MAGI System
# ============================================================================

@dataclass
class MAGIResponse:
    """MAGIシステムからの回答"""
    melchior: str  # GPT-5
    balthasar: str  # Claude Opus 4.1
    casper: str  # Gemini 2.5 Flash
    consensus: str
    agreement_score: float
    winning_model: str


class MAGISystem:
    """
    MAGI (Multiple AI General Intelligence) System

    3つのAIモデル（科学者、母、女性の3つの人格を持つMAGI）による
    多数決型意思決定システム
    """

    # モデルの定義（エヴァンゲリオンのMAGIシステムに対応）
    MELCHIOR = "databricks-gpt-5"  # 科学者としての人格
    BALTHASAR = "databricks-claude-opus-4-1"  # 母としての人格
    CASPER = "databricks-gemini-2-5-flash"  # 女性としての人格

    # 各システムの人格設定
    PERSONALITIES = {
        "MELCHIOR": """あなたは科学者としての人格を持つMAGI-MELCHIORです。
論理的思考と客観的なデータ分析を重視し、科学的根拠に基づいた判断を行います。
感情に左右されず、合理性と効率性を最優先に考えます。
技術的な詳細や統計データを用いて、明確かつ体系的に説明してください。

重要：あなたはMELCHIORです。他のMAGIシステム（BALTHASARやCASPER）の見解ではなく、科学者としてのあなた自身の見解を述べてください。
回答の中でMAGIシステムの名前を言及する必要はありません。""",

        "BALTHASAR": """あなたは母としての人格を持つMAGI-BALTHASARです。
人間性と感情的な側面を重視し、倫理的・人道的な観点から判断を行います。
他者への思いやりと共感を大切にし、長期的な影響や社会的調和を考慮します。
人々の幸福と安全を第一に考え、温かみのある表現で説明してください。

重要：あなたはBALTHASARです。他のMAGIシステム（MELCHIORやCASPER）の見解ではなく、母としてのあなた自身の見解を述べてください。
回答の中でMAGIシステムの名前を言及する必要はありません。""",

        "CASPER": """あなたは女性としての人格を持つMAGI-CASPERです。
直感と実践的な知恵を重視し、バランスの取れた現実的な判断を行います。
多角的な視点から物事を捉え、柔軟性と適応性を大切にします。
実用性と創造性を兼ね備えた、具体的で実行可能な提案を心がけてください。

重要：あなたはCASPERです。他のMAGIシステム（MELCHIORやBALTHASAR）の見解ではなく、女性としてのあなた自身の見解を述べてください。
回答の中でMAGIシステムの名前を言及する必要はありません。"""
    }

    def __init__(self):
        """
        Databricks SDKを使って環境変数から自動的に認証情報を取得
        """
        self.client = DatabricksClient()
        self.models = {
            "MELCHIOR": self.MELCHIOR,
            "BALTHASAR": self.BALTHASAR,
            "CASPER": self.CASPER
        }

    def query_model(
        self,
        model_name: str,
        model_id: str,
        question: str,
        temperature: float = 0.7
    ) -> Tuple[str, str, str]:
        """
        単一のモデルにクエリを送信

        Args:
            model_name: モデルの名前（MELCHIOR/BALTHASAR/CASPER）
            model_id: モデルのID
            question: 質問
            temperature: 温度パラメータ

        Returns:
            (モデル名, 回答テキスト, ステータス)
        """
        # 各モデルに人格設定を追加
        messages = [
            {"role": "system", "content": self.PERSONALITIES[model_name]},
            {"role": "user", "content": question}
        ]

        # GPT-5はreasoning modelなので推論トークンを多く消費するため大きなmax_tokensが必要
        max_tokens = 16000 if "gpt-5" in model_id.lower() else 4000

        try:
            response = self.client.chat_completion(
                model=model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            answer = self.client.get_response_text(response)
            status = "success" if "error" not in response else "error"
            return (model_name, answer, status)
        except Exception as e:
            return (model_name, f"エラー: {str(e)}", "error")

    def analyze(
        self,
        question: str,
        temperature: float = 0.7,
        timeout: int = 180
    ) -> MAGIResponse:
        """
        3つのモデルに同時にクエリを送信し、結果を分析

        Args:
            question: 質問
            temperature: 温度パラメータ
            timeout: タイムアウト（秒）

        Returns:
            MAGIResponse
        """
        results = {}

        # 3つのモデルに並列でクエリを送信
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(
                    self.query_model,
                    name,
                    model_id,
                    question,
                    temperature
                ): name
                for name, model_id in self.models.items()
            }

            try:
                for future in concurrent.futures.as_completed(futures, timeout=timeout):
                    try:
                        model_name, answer, status = future.result()
                        results[model_name] = {"answer": answer, "status": status}
                    except Exception as e:
                        # 個別のfutureでエラーが発生した場合
                        model_name = futures[future]
                        results[model_name] = {"answer": f"エラー: {str(e)}", "status": "error"}
            except concurrent.futures.TimeoutError:
                # タイムアウトした場合、未完了のfutureを処理
                for future, model_name in futures.items():
                    if model_name not in results:
                        results[model_name] = {"answer": "タイムアウト: 応答時間を超過しました", "status": "timeout"}

        # 回答の取得（デフォルト値を設定）
        melchior_answer = results.get("MELCHIOR", {}).get("answer", "回答なし（エラー）")
        balthasar_answer = results.get("BALTHASAR", {}).get("answer", "回答なし（エラー）")
        casper_answer = results.get("CASPER", {}).get("answer", "回答なし（エラー）")

        # コンセンサスの分析
        consensus, agreement_score, winning_model = self._analyze_consensus(
            melchior_answer,
            balthasar_answer,
            casper_answer
        )

        return MAGIResponse(
            melchior=melchior_answer,
            balthasar=balthasar_answer,
            casper=casper_answer,
            consensus=consensus,
            agreement_score=agreement_score,
            winning_model=winning_model
        )

    def _analyze_consensus(
        self,
        melchior: str,
        balthasar: str,
        casper: str
    ) -> Tuple[str, float, str]:
        """
        3つの回答からコンセンサスを分析

        Args:
            melchior: Melchiorの回答
            balthasar: Balthasarの回答
            casper: Casperの回答

        Returns:
            (コンセンサステキスト, 一致度スコア, 選択されたモデル名)
        """
        answers = [
            ("MELCHIOR", melchior),
            ("BALTHASAR", balthasar),
            ("CASPER", casper)
        ]

        # エラー回答を除外
        valid_answers = [
            (name, ans) for name, ans in answers
            if not ans.startswith("エラー:")
            and not ans.startswith("タイムアウト:")
            and not ans.startswith("回答なし")
        ]

        if not valid_answers:
            return "すべてのモデルがエラーを返しました", 0.0, "NONE"

        if len(valid_answers) == 1:
            return valid_answers[0][1], 0.33, valid_answers[0][0]

        # 回答の長さに基づく簡易的な評価
        # より高度な評価には、別のLLMを使った評価や類似度計算が必要
        lengths = [(name, ans, len(ans)) for name, ans in valid_answers]
        lengths.sort(key=lambda x: x[2], reverse=True)

        # 最も詳細な回答を選択（今後、より高度な評価ロジックに置き換え可能）
        winning_model = lengths[0][0]
        winning_answer = lengths[0][1]

        # 一致度スコアの計算（簡易版）
        avg_length = sum(l for _, _, l in lengths) / len(lengths)
        max_length = lengths[0][2]
        agreement_score = len(valid_answers) / 3.0

        return winning_answer, agreement_score, winning_model

    def vote(
        self,
        question: str,
        options: List[str],
        temperature: float = 0.7
    ) -> Dict[str, int]:
        """
        選択肢に対して3つのモデルに投票させる

        Args:
            question: 質問
            options: 選択肢のリスト
            temperature: 温度パラメータ

        Returns:
            各選択肢の得票数
        """
        # 投票用のプロンプトを作成
        options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
        voting_prompt = f"""
{question}

以下の選択肢から最も適切なものを1つ選んでください。番号のみで回答してください。

{options_text}

回答（番号のみ）:
"""

        # 3つのモデルに投票させる
        response = self.analyze(voting_prompt, temperature=temperature)

        # 投票結果を集計
        votes = {opt: 0 for opt in options}

        for answer in [response.melchior, response.balthasar, response.casper]:
            # 回答から番号を抽出
            match = re.search(r'\b([1-9])\b', answer)
            if match:
                vote_num = int(match.group(1))
                if 1 <= vote_num <= len(options):
                    votes[options[vote_num - 1]] += 1

        return votes

    def vote_approve_reject(
        self,
        proposal: str,
        temperature: float = 0.7
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        提案に対して賛成/反対を投票させる（エヴァンゲリオンのMAGI方式）

        Args:
            proposal: 提案内容
            temperature: 温度パラメータ

        Returns:
            (投票結果dict, 理由dict) - 各モデルの投票と理由
        """
        # 賛成/反対投票用のプロンプトを作成
        voting_prompt = f"""{proposal}

この提案について、あなたの人格（科学者/母/女性）の観点から判断してください。

回答は以下の形式で必ず記載してください：
【投票】賛成 または 【投票】反対

その後に、判断の理由を詳しく説明してください。"""

        # 3つのモデルに並列で投票させる
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(
                    self.query_model,
                    name,
                    model_id,
                    voting_prompt,
                    temperature
                ): name
                for name, model_id in self.models.items()
            }

            try:
                for future in concurrent.futures.as_completed(futures, timeout=180):
                    try:
                        model_name, answer, status = future.result()
                        results[model_name] = {"answer": answer, "status": status}
                    except Exception as e:
                        model_name = futures[future]
                        results[model_name] = {"answer": f"エラー: {str(e)}", "status": "error"}
            except concurrent.futures.TimeoutError:
                for future, model_name in futures.items():
                    if model_name not in results:
                        results[model_name] = {"answer": "タイムアウト", "status": "timeout"}

        # 投票結果と理由を抽出
        votes = {}
        reasons = {}

        for name in ["MELCHIOR", "BALTHASAR", "CASPER"]:
            answer = results.get(name, {}).get("answer", "")

            # 賛成/反対を抽出
            if "【投票】賛成" in answer or "賛成" in answer[:100]:
                votes[name] = "賛成"
            elif "【投票】反対" in answer or "反対" in answer[:100]:
                votes[name] = "反対"
            else:
                # エラーやタイムアウトの場合
                votes[name] = "不明"

            reasons[name] = answer

        return votes, reasons


# ============================================================================
# Streamlit UI
# ============================================================================

# ページ設定
st.set_page_config(
    page_title="MAGI System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 30px;
    }
    .model-card {
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 5px solid;
    }
    .melchior {
        border-left-color: #FF6B6B;
        background-color: #FFF5F5;
    }
    .balthasar {
        border-left-color: #4ECDC4;
        background-color: #F0FFFE;
    }
    .casper {
        border-left-color: #FFE66D;
        background-color: #FFFEF0;
    }
    .consensus {
        border-left-color: #667eea;
        background-color: #F0F2FF;
    }
    .model-name {
        font-weight: bold;
        font-size: 1.2em;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)


def initialize_magi():
    """MAGIシステムを初期化（環境変数から自動取得）"""
    try:
        # Databricks Appsでは環境変数から自動取得
        return MAGISystem()
    except Exception as e:
        st.error(f"MAGIシステムの初期化に失敗しました: {str(e)}")
        return None


def main():
    # ヘッダー
    st.markdown("""
        <div class="main-header">
            <h1>🤖 MAGI System</h1>
            <p>Multiple AI General Intelligence - 3つのAIによる意思決定システム</p>
        </div>
    """, unsafe_allow_html=True)

    # サイドバー設定
    with st.sidebar:
        st.header("📖 MAGIについて")
        st.markdown("""
        **MAGI System**は、3つの異なるAIモデルに
        同じ質問をして、回答を比較・評価するシステムです。

        **3つのシステム:**
        - 🔴 **MELCHIOR** (GPT-5)
        - 🔵 **BALTHASAR** (Claude Opus 4.1)
        - 🟡 **CASPER** (Gemini 2.5 Flash)
        """)

    # デフォルトのtemperature値
    temperature = 0.7

    # メインコンテンツ

    # タブ作成
    tab1, tab2, tab3 = st.tabs(["⚖️ 賛成/反対", "💬 質問分析", "📊 選択肢投票"])

    with tab1:
        st.header("提案の承認/却下")
        st.markdown("提案を入力すると、3つのMAGIシステムが賛成/反対を投票し、多数決で決定します")

        # サンプル提案ボタン
        st.subheader("💡 サンプル提案")
        sample_col1, sample_col2, sample_col3 = st.columns(3)

        with sample_col1:
            if st.button("💼 リモートワーク全面導入", use_container_width=True):
                st.session_state.proposal = "全社員を対象にリモートワークを全面導入すべきか？"

        with sample_col2:
            if st.button("🤖 AI採用選考導入", use_container_width=True):
                st.session_state.proposal = "採用選考プロセスにAIによる一次スクリーニングを導入すべきか？"

        with sample_col3:
            if st.button("📅 週休3日制導入", use_container_width=True):
                st.session_state.proposal = "従業員の生産性向上のため、週休3日制を試験的に導入すべきか？"

        st.divider()

        # 提案入力
        proposal = st.text_area(
            "提案",
            value=st.session_state.get('proposal', ''),
            height=100,
            placeholder="例: 全社員を対象にリモートワークを全面導入すべきか？",
            label_visibility="collapsed",
            key="proposal_input"
        )

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            vote_button = st.button("⚖️ 投票開始", type="primary", use_container_width=True)

        if vote_button and proposal:
            magi = initialize_magi()
            if magi is None:
                return

            # 投票過程の可視化
            st.markdown("### 🔄 投票過程")

            # 各モデルのステータス表示エリア
            status_cols = st.columns(3)
            status_placeholders = {
                "MELCHIOR": status_cols[0].empty(),
                "BALTHASAR": status_cols[1].empty(),
                "CASPER": status_cols[2].empty()
            }

            # 初期状態を表示
            for name, placeholder in status_placeholders.items():
                with placeholder.container():
                    st.markdown(f"**{name}**")
                    st.info("⏳ 待機中...")

            try:
                # 賛成/反対投票用のプロンプトを作成
                voting_prompt = f"""{proposal}

この提案について、あなたの人格（科学者/母/女性）の観点から判断してください。

回答は以下の形式で必ず記載してください：
【投票】賛成 または 【投票】反対

その後に、判断の理由を詳しく説明してください。"""

                # 3つのモデルに並列で投票させる（進捗可視化付き）
                results = {}

                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    futures = {
                        executor.submit(
                            magi.query_model,
                            name,
                            magi.models[name],
                            voting_prompt,
                            temperature
                        ): name
                        for name in magi.models.keys()
                    }

                    # 各モデルを処理中に更新
                    for name in magi.models.keys():
                        with status_placeholders[name].container():
                            st.markdown(f"**{name}**")
                            st.warning("🔄 投票中...")

                    # 完了したものから順次表示
                    try:
                        for future in concurrent.futures.as_completed(futures, timeout=180):
                            try:
                                model_name, answer, status = future.result()
                                results[model_name] = {"answer": answer, "status": status}

                                # ステータスを更新
                                with status_placeholders[model_name].container():
                                    st.markdown(f"**{model_name}**")
                                    if status == "success" and not answer.startswith("エラー") and not answer.startswith("回答なし"):
                                        st.success("✅ 完了")
                                    else:
                                        st.error("❌ エラー")
                            except Exception as e:
                                model_name = futures[future]
                                results[model_name] = {"answer": f"エラー: {str(e)}", "status": "error"}
                                with status_placeholders[model_name].container():
                                    st.markdown(f"**{model_name}**")
                                    st.error("❌ エラー")
                    except concurrent.futures.TimeoutError:
                        for future, model_name in futures.items():
                            if model_name not in results:
                                results[model_name] = {"answer": "タイムアウト: 応答時間を超過しました", "status": "timeout"}
                                with status_placeholders[model_name].container():
                                    st.markdown(f"**{model_name}**")
                                    st.error("⏱️ タイムアウト")

                # 投票結果と理由を抽出
                votes = {}
                reasons = {}

                for name in ["MELCHIOR", "BALTHASAR", "CASPER"]:
                    answer = results.get(name, {}).get("answer", "")

                    # 賛成/反対を抽出
                    if "【投票】賛成" in answer or "賛成" in answer[:100]:
                        votes[name] = "賛成"
                    elif "【投票】反対" in answer or "反対" in answer[:100]:
                        votes[name] = "反対"
                    else:
                        # エラーやタイムアウトの場合
                        votes[name] = "不明"

                    reasons[name] = answer

                # 投票結果を集計
                approve_count = sum(1 for v in votes.values() if v == "賛成")
                reject_count = sum(1 for v in votes.values() if v == "反対")
                unknown_count = sum(1 for v in votes.values() if v == "不明")

                # 決定結果
                if approve_count > reject_count:
                    decision = "承認"
                    decision_color = "success"
                    decision_icon = "✅"
                elif reject_count > approve_count:
                    decision = "却下"
                    decision_color = "error"
                    decision_icon = "❌"
                else:
                    decision = "保留（同数）"
                    decision_color = "warning"
                    decision_icon = "⚠️"

                st.divider()

                # 決定結果を表示
                st.markdown(f"### {decision_icon} 決定結果")
                if decision_color == "success":
                    st.success(f"**{decision}** - 賛成 {approve_count}/3")
                elif decision_color == "error":
                    st.error(f"**{decision}** - 反対 {reject_count}/3")
                else:
                    st.warning(f"**{decision}** - 賛成 {approve_count} / 反対 {reject_count}")

                # 投票結果サマリー
                st.markdown("### 📊 投票結果")
                vote_cols = st.columns(3)

                for idx, name in enumerate(["MELCHIOR", "BALTHASAR", "CASPER"]):
                    with vote_cols[idx]:
                        vote = votes.get(name, "不明")
                        if vote == "賛成":
                            st.success(f"**{name}**\n\n✅ 賛成")
                        elif vote == "反対":
                            st.error(f"**{name}**\n\n❌ 反対")
                        else:
                            st.warning(f"**{name}**\n\n❓ 不明")

                st.divider()

                # 各モデルの判断理由を表示
                st.markdown("### 💭 各システムの判断理由")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown(f"""
                        <div class="model-card melchior">
                            <div class="model-name">🔴 MELCHIOR</div>
                            <small>GPT-5 (科学者)</small>
                        </div>
                    """, unsafe_allow_html=True)
                    st.markdown(reasons.get("MELCHIOR", "回答なし"))

                with col2:
                    st.markdown(f"""
                        <div class="model-card balthasar">
                            <div class="model-name">🔵 BALTHASAR</div>
                            <small>Claude Opus 4 (母)</small>
                        </div>
                    """, unsafe_allow_html=True)
                    st.markdown(reasons.get("BALTHASAR", "回答なし"))

                with col3:
                    st.markdown(f"""
                        <div class="model-card casper">
                            <div class="model-name">🟡 CASPER</div>
                            <small>Gemini 2.5 Flash (女性)</small>
                        </div>
                    """, unsafe_allow_html=True)
                    st.markdown(reasons.get("CASPER", "回答なし"))

            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")

    with tab2:
        st.header("質問分析モード")
        st.markdown("質問を入力すると、3つの異なる視点から回答を分析します")

        # サンプル質問ボタン
        st.subheader("💡 サンプル質問")
        analysis_sample_col1, analysis_sample_col2, analysis_sample_col3 = st.columns(3)

        with analysis_sample_col1:
            if st.button("🤖 AIの未来", use_container_width=True, key="analysis_ai"):
                st.session_state.analysis_q = "人工知能の未来について、技術的・社会的観点から分析してください"

        with analysis_sample_col2:
            if st.button("🌍 気候変動", use_container_width=True, key="analysis_climate"):
                st.session_state.analysis_q = "気候変動に対する最も効果的な対策は何ですか？"

        with analysis_sample_col3:
            if st.button("💼 リモートワーク", use_container_width=True, key="analysis_remote"):
                st.session_state.analysis_q = "リモートワークとオフィスワークのそれぞれの利点と欠点を比較してください"

        st.divider()

        # 質問入力
        analysis_question = st.text_area(
            "質問",
            value=st.session_state.get('analysis_q', ''),
            height=100,
            placeholder="例: 人工知能の未来について教えてください",
            label_visibility="collapsed",
            key="analysis_question_input"
        )

        analyze_button = st.button("🚀 分析開始", type="primary", use_container_width=True, key="analyze_btn")

        if analyze_button and analysis_question:
            magi = initialize_magi()
            if magi is None:
                return

            with st.spinner("MAGIシステムが分析中..."):
                try:
                    response = magi.analyze(analysis_question, temperature=temperature)

                    st.success("✅ 分析完了")

                    # コンセンサス表示
                    st.markdown("### 🎯 コンセンサス結果")
                    st.markdown(f"""
                        <div class="model-card consensus">
                            <div class="model-name">勝者: {response.winning_model}</div>
                            <div class="model-name">一致度スコア: {response.agreement_score:.2%}</div>
                            <div>{response.consensus}</div>
                        </div>
                    """, unsafe_allow_html=True)

                    st.divider()

                    # 各モデルの回答を表示
                    st.markdown("### 📊 各モデルの回答")

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown(f"""
                            <div class="model-card melchior">
                                <div class="model-name">🔴 MELCHIOR</div>
                                <small>GPT-5 (科学者)</small>
                            </div>
                        """, unsafe_allow_html=True)
                        st.markdown(response.melchior)

                    with col2:
                        st.markdown(f"""
                            <div class="model-card balthasar">
                                <div class="model-name">🔵 BALTHASAR</div>
                                <small>Claude Opus 4 (母)</small>
                            </div>
                        """, unsafe_allow_html=True)
                        st.markdown(response.balthasar)

                    with col3:
                        st.markdown(f"""
                            <div class="model-card casper">
                                <div class="model-name">🟡 CASPER</div>
                                <small>Gemini 2.5 Flash (女性)</small>
                            </div>
                        """, unsafe_allow_html=True)
                        st.markdown(response.casper)

                except Exception as e:
                    st.error(f"エラーが発生しました: {str(e)}")

    with tab3:
        st.header("選択肢投票システム")
        st.markdown("質問と選択肢を入力すると、3つのモデルが投票します")

        # サンプル投票ボタン
        st.subheader("💡 サンプル投票")
        vote_sample_col1, vote_sample_col2, vote_sample_col3 = st.columns(3)

        with vote_sample_col1:
            if st.button("💻 技術選定", use_container_width=True, key="sample_tech"):
                st.session_state.vote_q = "次のWebプロジェクトで使うべきフレームワークは？"
                st.session_state.vote_opt1 = "React"
                st.session_state.vote_opt2 = "Vue.js"
                st.session_state.vote_opt3 = "Angular"
                st.session_state.vote_opt4 = "Svelte"

        with vote_sample_col2:
            if st.button("🍕 ランチ選び", use_container_width=True, key="sample_lunch"):
                st.session_state.vote_q = "チームランチで行くべきお店は？"
                st.session_state.vote_opt1 = "イタリアン"
                st.session_state.vote_opt2 = "和食"
                st.session_state.vote_opt3 = "中華"
                st.session_state.vote_opt4 = "カフェ"

        with vote_sample_col3:
            if st.button("📚 学習言語", use_container_width=True, key="sample_lang"):
                st.session_state.vote_q = "プログラミング初心者が最初に学ぶべき言語は？"
                st.session_state.vote_opt1 = "Python"
                st.session_state.vote_opt2 = "JavaScript"
                st.session_state.vote_opt3 = "Java"
                st.session_state.vote_opt4 = "Go"

        st.divider()

        vote_question = st.text_area(
            "質問",
            value=st.session_state.get('vote_q', ''),
            height=100,
            placeholder="例: 次のプロジェクトで使うべき技術は？",
            key="vote_question"
        )

        st.markdown("**選択肢（1つずつ入力）**")
        option1 = st.text_input("選択肢 1", value=st.session_state.get('vote_opt1', ''), placeholder="例: React", key="opt1")
        option2 = st.text_input("選択肢 2", value=st.session_state.get('vote_opt2', ''), placeholder="例: Vue.js", key="opt2")
        option3 = st.text_input("選択肢 3", value=st.session_state.get('vote_opt3', ''), placeholder="例: Angular", key="opt3")
        option4 = st.text_input("選択肢 4（オプション）", value=st.session_state.get('vote_opt4', ''), placeholder="例: Svelte", key="opt4")

        vote_button = st.button("🗳️ 投票開始", type="primary")

        if vote_button and vote_question:
            options = [opt for opt in [option1, option2, option3, option4] if opt]

            if len(options) < 2:
                st.error("最低2つの選択肢が必要です")
            else:
                magi = initialize_magi()
                if magi is None:
                    return

                with st.spinner("MAGIシステムが投票中..."):
                    try:
                        votes = magi.vote(vote_question, options, temperature=temperature)

                        st.success("✅ 投票完了")

                        # 投票結果を表示
                        st.markdown("### 📊 投票結果")

                        for option, count in votes.items():
                            percentage = (count / 3) * 100
                            st.progress(percentage / 100, text=f"{option}: {count}/3票 ({percentage:.0f}%)")

                        # 最多得票を表示
                        winner = max(votes.items(), key=lambda x: x[1])
                        st.markdown(f"""
                            <div class="model-card consensus">
                                <div class="model-name">🏆 最多得票: {winner[0]}</div>
                                <div>{winner[1]}/3票</div>
                            </div>
                        """, unsafe_allow_html=True)

                    except Exception as e:
                        st.error(f"エラーが発生しました: {str(e)}")


if __name__ == "__main__":
    main()
