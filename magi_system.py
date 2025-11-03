"""
MAGI System - Multiple AI General Intelligence
3つのAIモデルによる多数決型意思決定システム
"""
import re
import concurrent.futures
from typing import Dict, List, Tuple
from dataclasses import dataclass
from databricks_client import DatabricksClient


@dataclass
class MAGIResponse:
    """MAGIシステムからの回答"""
    melchior: str  # GPT-5
    balthasar: str  # Claude Opus 4.1
    casper: str  # Gemini 2.5 Pro
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
    CASPER = "databricks-gemini-2-5-pro"  # 女性としての人格

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
