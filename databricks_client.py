"""
Databricks Foundation Model API Client
"""
import requests
import time
from typing import Dict, List
from databricks.sdk.core import Config


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

        # 最終的にエラーを返す
        if last_error:
            raise last_error
        else:
            raise Exception("Unknown error occurred")

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
