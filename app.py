"""
MAGI System - Streamlit Web Application
Databricks Apps対応
"""
import streamlit as st
import concurrent.futures
from magi_system import MAGISystem, MAGIResponse


# ============================================================================
# Streamlit UI
# ============================================================================

# ページ設定
st.set_page_config(
    page_title="MAGI System",
    page_icon="🤖",
    layout="wide"
)

# CSS スタイリング - エヴァンゲリオンMAGI風
st.markdown("""
    <style>
    /* ダークテーマベース - 真っ黒 */
    .stApp {
        background-color: #000000;
        color: #ff6600;
    }

    /* CRTスキャンライン効果 */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: repeating-linear-gradient(
            0deg,
            rgba(0, 0, 0, 0.15),
            rgba(0, 0, 0, 0.15) 1px,
            transparent 1px,
            transparent 2px
        );
        pointer-events: none;
        z-index: 1000;
    }

    /* 見出しとテキストの色 - オレンジ */
    h1, h2, h3, h4, h5, h6 {
        color: #ff6600 !important;
        font-family: 'Courier New', monospace;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    /* メインヘッダー - MAGIシステムコード風 */
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: #000000;
        color: #ff6600;
        border: 3px solid #ff6600;
        margin-bottom: 1.5rem;
        box-shadow: 0 0 30px rgba(255, 102, 0, 0.5);
        font-family: 'Courier New', monospace;
    }
    .main-header h1 {
        color: #ff6600;
        text-shadow: 0 0 10px #ff6600;
        font-family: 'Courier New', monospace;
        letter-spacing: 0.3em;
        font-weight: bold;
        margin-bottom: 0.3rem;
    }
    .main-header p {
        margin: 0;
    }

    /* モデルカード - エヴァMAGI風の大きなブロック */
    .model-card {
        border: 4px solid;
        padding: 1rem;
        margin: 1.5rem 0;
        border-radius: 0;
        font-family: 'Courier New', monospace;
        position: relative;
        min-height: 120px;
        font-size: 0.85em;
    }
    /* MELCHIOR - 赤色ブロック */
    .melchior {
        border-color: #ff0000;
        background: #cc0000;
        box-shadow: 0 0 30px rgba(255, 0, 0, 0.8);
    }
    /* BALTHASAR - 青色ブロック */
    .balthasar {
        border-color: #0080ff;
        background: #0066cc;
        box-shadow: 0 0 30px rgba(0, 128, 255, 0.8);
    }
    /* CASPER - 黄色ブロック */
    .casper {
        border-color: #ffff00;
        background: #cccc00;
        box-shadow: 0 0 30px rgba(255, 255, 0, 0.8);
    }
    /* CONSENSUS - オレンジ */
    .consensus {
        border-color: #ff6600;
        background: #cc5500;
        box-shadow: 0 0 30px rgba(255, 102, 0, 0.8);
    }
    .model-name {
        font-weight: bold;
        font-size: 1.3em;
        margin-bottom: 8px;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
        font-family: 'Courier New', monospace;
        letter-spacing: 0.15em;
        text-transform: uppercase;
    }
    .melchior .model-name {
        color: #000000;
    }
    .balthasar .model-name {
        color: #000000;
    }
    .casper .model-name {
        color: #000000;
    }
    .consensus .model-name {
        color: #000000;
    }
    /* カード内のテキストも黒に */
    .model-card p,
    .model-card div,
    .model-card span {
        color: #000000 !important;
    }

    /* エヴァMAGI風 - 3つのボックスの横並び配置 */
    .magi-container {
        display: flex;
        gap: 1.5rem;
        justify-content: space-between;
        width: 100%;
        margin: 2rem 0;
    }
    .magi-box {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        font-family: 'Courier New', monospace;
        font-weight: bold;
        font-size: 1em;
        border: 4px solid;
        padding: 2rem;
        min-height: 200px;
        clip-path: polygon(10% 0%, 90% 0%, 100% 10%, 100% 90%, 90% 100%, 10% 100%, 0% 90%, 0% 10%);
    }
    .magi-box-title {
        font-size: 0.7em;
        margin-bottom: 0.5rem;
        letter-spacing: 0.1em;
        white-space: nowrap;
        color: #000000 !important;
    }
    .magi-box-status {
        font-size: 1.0em;
        margin-top: 0.5rem;
        color: #000000 !important;
    }

    /* 各MAGIシステムの色（固有色で統一） */
    .magi-melchior {
        background: #cc0000 !important;
        border-color: #ff0000 !important;
        box-shadow: 0 0 40px rgba(255, 0, 0, 0.8) !important;
        color: #000000 !important;
    }
    .magi-melchior .magi-box-title,
    .magi-melchior .magi-box-status {
        color: #000000 !important;
    }
    .magi-balthasar {
        background: #0066cc !important;
        border-color: #0080ff !important;
        box-shadow: 0 0 40px rgba(0, 128, 255, 0.8) !important;
        color: #000000 !important;
    }
    .magi-balthasar .magi-box-title,
    .magi-balthasar .magi-box-status {
        color: #000000 !important;
    }
    .magi-casper {
        background: #cccc00 !important;
        border-color: #ffff00 !important;
        box-shadow: 0 0 40px rgba(255, 255, 0, 0.8) !important;
        color: #000000 !important;
    }
    .magi-casper .magi-box-title,
    .magi-casper .magi-box-status {
        color: #000000 !important;
    }

    /* 投票中の状態 */
    .magi-pending {
        opacity: 0.6;
    }

    /* アニメーション定義 */
    @keyframes fadeInScale {
        0% {
            opacity: 0;
            transform: scale(0.8);
        }
        100% {
            opacity: 1;
            transform: scale(1);
        }
    }

    @keyframes blink {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.3;
        }
    }

    /* MAGIボックスの表示アニメーション */
    .magi-box {
        animation: fadeInScale 0.8s ease-out forwards;
        opacity: 0;
    }

    .magi-melchior {
        animation-delay: 0.1s;
    }

    .magi-balthasar {
        animation-delay: 0.3s;
    }

    .magi-casper {
        animation-delay: 0.5s;
    }

    /* 投票中の点滅アニメーション */
    .voting-status {
        animation: blink 1.5s infinite;
        color: #000000 !important;
    }

    /* Streamlitアラートボックスの色調整 */
    .stAlert {
        background-color: #1a1a1a !important;
        border: 2px solid #ff6600 !important;
        color: #ff6600 !important;
    }
    .stAlert > div {
        color: #ff6600 !important;
    }
    .stSuccess {
        background-color: #1a1a1a !important;
        border-color: #00ff00 !important;
        color: #00ff00 !important;
    }
    .stError {
        background-color: #1a1a1a !important;
        border-color: #ff0000 !important;
        color: #ff0000 !important;
    }
    .stWarning {
        background-color: #1a1a1a !important;
        border-color: #ffff00 !important;
        color: #ffff00 !important;
    }
    .stInfo {
        background-color: #1a1a1a !important;
        border-color: #00ffff !important;
        color: #00ffff !important;
    }

    /* その他の白い背景を持つコンポーネントを修正 */
    .stMarkdown, .stText {
        background-color: transparent !important;
    }
    div[data-testid="stMarkdownContainer"] {
        background-color: transparent !important;
    }
    .element-container {
        background-color: transparent !important;
    }

    .stExpander {
        background-color: #1a1a1a !important;
        border: 2px solid #ff6600 !important;
    }
    [data-testid="stExpander"] {
        background-color: #1a1a1a !important;
        border-color: #ff6600 !important;
    }

    /* Streamlitコンポーネントの色調整 - オレンジベース */
    .stButton > button {
        background-color: #000000;
        color: #ff6600;
        border: 2px solid #ff6600;
        font-family: 'Courier New', monospace;
        text-transform: uppercase;
    }
    .stButton > button:hover {
        background-color: #ff6600;
        color: #000000 !important;
        box-shadow: 0 0 20px #ff6600;
    }
    .stButton > button:hover p,
    .stButton > button:hover span,
    .stButton > button:hover div {
        color: #000000 !important;
    }
    .stTextArea textarea {
        background-color: #1a1a1a;
        color: #ff6600;
        border: 2px solid #ff6600;
        font-family: 'Courier New', monospace;
    }
    .stTextArea textarea::placeholder {
        color: #cc5500 !important;
        opacity: 0.7;
    }
    .stTextInput input {
        background-color: #1a1a1a;
        color: #ff6600;
        border: 2px solid #ff6600;
        font-family: 'Courier New', monospace;
    }
    .stTextInput input::placeholder {
        color: #cc5500 !important;
        opacity: 0.7;
    }

    /* サイドバー */
    section[data-testid="stSidebar"] {
        background-color: #000000;
        border-right: 3px solid #ff6600;
    }
    section[data-testid="stSidebar"] * {
        color: #ff6600 !important;
        font-family: 'Courier New', monospace;
    }

    /* タブ */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #000000;
        border-bottom: 2px solid #ff6600;
    }
    .stTabs [data-baseweb="tab"] {
        color: #ff6600 !important;
        border-color: #ff6600 !important;
        font-family: 'Courier New', monospace;
        text-transform: uppercase;
    }
    .stTabs [data-baseweb="tab"] p {
        color: #ff6600 !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ff6600 !important;
    }
    .stTabs [aria-selected="true"] p {
        color: #000000 !important;
        font-weight: bold;
    }

    /* 区切り線 */
    hr {
        border-color: #ff6600;
        opacity: 0.5;
    }

    /* Streamlitヘッダーとツールバーを真っ黒に */
    header[data-testid="stHeader"] {
        background-color: #000000 !important;
        border-bottom: 2px solid #ff6600;
    }
    .stDeployButton {
        visibility: hidden;
    }
    #MainMenu {
        visibility: hidden;
    }
    footer {
        visibility: hidden;
    }

    /* ツールバーボタンの色 - オレンジ */
    header[data-testid="stHeader"] button {
        color: #ff6600 !important;
    }
    header[data-testid="stHeader"] svg {
        fill: #ff6600 !important;
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
    # ヘッダー - エヴァMAGI風
    st.markdown("""
        <div class="main-header">
            <h1>MAGI SYSTEM</h1>
            <p style="font-size: 0.8em; letter-spacing: 0.2em; margin-top: 0.5rem;">MULTIPLE AI GENERAL INTELLIGENCE</p>
        </div>
    """, unsafe_allow_html=True)

    # サイドバー設定
    with st.sidebar:
        st.header("MAGI SYSTEM INFO")
        st.markdown("""
        **MAGI SYSTEM** - Multiple AI General Intelligence

        3つの異なるAIモデルによる多数決型意思決定システム

        **3 SYSTEMS:**
        - **MELCHIOR-1** (GPT-5) - SCIENTIST
        - **BALTHASAR-2** (Claude Opus 4.1) - MOTHER
        - **CASPER-3** (Gemini 2.5 Pro) - WOMAN
        """)

    # デフォルトのtemperature値
    temperature = 0.7

    # メインコンテンツ

    # タブ作成
    tab1, tab2, tab3 = st.tabs(["APPROVE/REJECT", "QUESTION ANALYSIS", "OPTION VOTING"])

    with tab1:
        st.header("提案の承認/却下")
        st.markdown("提案を入力すると、3つのMAGIシステムが承認/否定を投票し、多数決で決定します")

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

        sample_col4, sample_col5, sample_col6 = st.columns(3)

        with sample_col4:
            if st.button("🌱 完全ペーパーレス化", use_container_width=True):
                st.session_state.proposal = "環境保護のため、社内の紙資料を完全に廃止しペーパーレス化すべきか？"

        with sample_col5:
            if st.button("🎓 社内教育プログラム必須化", use_container_width=True):
                st.session_state.proposal = "全社員に対して月10時間以上の社内教育プログラム受講を必須化すべきか？"

        with sample_col6:
            if st.button("💰 成果報酬制度導入", use_container_width=True):
                st.session_state.proposal = "固定給与の一部を成果報酬型に変更し、個人の業績に応じた報酬体系を導入すべきか？"

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

            # MAGIボックスをプレースホルダーで管理
            magi_container = st.empty()

            # MAGIボックスを描画する関数
            def render_magi_boxes(balthasar_vote, casper_vote, melchior_vote, show_decision=False, decision_text="", melchior_reason="", balthasar_reason="", casper_reason=""):
                # 投票結果に応じてステータステキストを決定
                def get_status_text(vote):
                    if vote == "承認" or vote == "否定":
                        return vote
                    else:
                        return '投票中...'

                # 投票結果に応じて背景色とテキスト色を決定
                def get_box_style(vote):
                    if vote == "承認":
                        return "background: #0099cc; border-color: #00ccff; box-shadow: 0 0 40px rgba(0, 204, 255, 0.8);", "#000000"
                    elif vote == "否定":
                        return "background: #cc0000; border-color: #ff0000; box-shadow: 0 0 40px rgba(255, 0, 0, 0.8);", "#000000"
                    else:
                        return "background: #555555; border-color: #888888; box-shadow: 0 0 40px rgba(136, 136, 136, 0.5); opacity: 0.6;", "#ffffff"

                melchior_style, melchior_color = get_box_style(melchior_vote)
                balthasar_style, balthasar_color = get_box_style(balthasar_vote)
                casper_style, casper_color = get_box_style(casper_vote)

                melchior_status = get_status_text(melchior_vote)
                balthasar_status = get_status_text(balthasar_vote)
                casper_status = get_status_text(casper_vote)

                decision_html = ""
                if show_decision:
                    decision_html = f'<div style="text-align: center; margin-top: 2rem; font-size: 1.5em; color: #ff6600; font-weight: bold;">{decision_text}</div>'

                # 判断理由のHTML
                reason_html = ""
                if melchior_reason or balthasar_reason or casper_reason:
                    reason_html = f"""
<div style="display: flex; gap: 1.5rem; justify-content: space-between; width: 100%; margin-top: 2rem;">
    <div style="flex: 1; background: #1a1a1a; border: 2px solid #ff0000; padding: 1rem; font-size: 0.85em;">
        <div style="color: #ff0000; font-weight: bold; margin-bottom: 0.5rem;">🔴 MELCHIOR (GPT-5)</div>
        <div style="color: #ff6600;">{melchior_reason}</div>
    </div>
    <div style="flex: 1; background: #1a1a1a; border: 2px solid #0080ff; padding: 1rem; font-size: 0.85em;">
        <div style="color: #0080ff; font-weight: bold; margin-bottom: 0.5rem;">🔵 BALTHASAR (Claude Opus 4)</div>
        <div style="color: #ff6600;">{balthasar_reason}</div>
    </div>
    <div style="flex: 1; background: #1a1a1a; border: 2px solid #ffff00; padding: 1rem; font-size: 0.85em;">
        <div style="color: #ffff00; font-weight: bold; margin-bottom: 0.5rem;">🟡 CASPER (Gemini 2.5 Pro)</div>
        <div style="color: #ff6600;">{casper_reason}</div>
    </div>
</div>
"""

                with magi_container.container():
                    st.markdown(f"""
<div style="display: flex; gap: 1.5rem; justify-content: space-between; width: 100%; margin: 2rem 0;">
    <div style="flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; font-family: 'Courier New', monospace; font-weight: bold; border: 4px solid; padding: 2rem; min-height: 200px; clip-path: polygon(10% 0%, 90% 0%, 100% 10%, 100% 90%, 90% 100%, 10% 100%, 0% 90%, 0% 10%); {melchior_style}">
        <div style="font-size: 1.0em; margin-bottom: 0.5rem; letter-spacing: 0.05em; white-space: nowrap; color: {melchior_color};">MELCHIOR-1</div>
        <div style="font-size: 1.5em; margin-top: 0.5rem; color: {melchior_color};">{melchior_status}</div>
    </div>
    <div style="flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; font-family: 'Courier New', monospace; font-weight: bold; border: 4px solid; padding: 2rem; min-height: 200px; clip-path: polygon(10% 0%, 90% 0%, 100% 10%, 100% 90%, 90% 100%, 10% 100%, 0% 90%, 0% 10%); {balthasar_style}">
        <div style="font-size: 1.0em; margin-bottom: 0.5rem; letter-spacing: 0.05em; white-space: nowrap; color: {balthasar_color};">BALTHASAR-2</div>
        <div style="font-size: 1.5em; margin-top: 0.5rem; color: {balthasar_color};">{balthasar_status}</div>
    </div>
    <div style="flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; font-family: 'Courier New', monospace; font-weight: bold; border: 4px solid; padding: 2rem; min-height: 200px; clip-path: polygon(10% 0%, 90% 0%, 100% 10%, 100% 90%, 90% 100%, 10% 100%, 0% 90%, 0% 10%); {casper_style}">
        <div style="font-size: 1.0em; margin-bottom: 0.5rem; letter-spacing: 0.05em; white-space: nowrap; color: {casper_color};">CASPER-3</div>
        <div style="font-size: 1.5em; margin-top: 0.5rem; color: {casper_color};">{casper_status}</div>
    </div>
</div>
{decision_html}
{reason_html}
                    """, unsafe_allow_html=True)

            # 初期状態のMAGIボックスを表示
            render_magi_boxes("", "", "")

            try:
                # 承認/否定投票用のプロンプトを作成
                voting_prompt = f"""{proposal}

この提案について、あなたの人格（科学者/母/女性）の観点から判断してください。

回答は以下の形式で必ず記載してください：
【投票】承認 または 【投票】否定

その後に、判断の理由を詳しく説明してください。"""

                # 3つのモデルに並列で投票させる
                results = {}
                votes = {}
                reasons = {}

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

                    # 完了したものから順次処理し、リアルタイムで更新
                    try:
                        for future in concurrent.futures.as_completed(futures, timeout=180):
                            try:
                                model_name, answer, status = future.result()
                                results[model_name] = {"answer": answer, "status": status}

                                # 承認/否定を抽出
                                if "【投票】承認" in answer or "承認" in answer[:100]:
                                    vote_result = "承認"
                                    votes[model_name] = "承認"
                                elif "【投票】否定" in answer or "否定" in answer[:100]:
                                    vote_result = "否定"
                                    votes[model_name] = "否定"
                                else:
                                    vote_result = "不明"
                                    votes[model_name] = "不明"

                                reasons[model_name] = answer

                                # 投票が完了するたびにMAGIボックスを更新
                                balthasar_vote = votes.get("BALTHASAR", "")
                                casper_vote = votes.get("CASPER", "")
                                melchior_vote = votes.get("MELCHIOR", "")
                                render_magi_boxes(balthasar_vote, casper_vote, melchior_vote)

                            except Exception as e:
                                model_name = futures[future]
                                results[model_name] = {"answer": f"エラー: {str(e)}", "status": "error"}
                                votes[model_name] = "不明"
                                reasons[model_name] = f"エラー: {str(e)}"

                                # エラー時も更新
                                balthasar_vote = votes.get("BALTHASAR", "")
                                casper_vote = votes.get("CASPER", "")
                                melchior_vote = votes.get("MELCHIOR", "")
                                render_magi_boxes(balthasar_vote, casper_vote, melchior_vote)

                    except concurrent.futures.TimeoutError:
                        for future, model_name in futures.items():
                            if model_name not in results:
                                results[model_name] = {"answer": "タイムアウト: 応答時間を超過しました", "status": "timeout"}
                                votes[model_name] = "不明"
                                reasons[model_name] = "タイムアウト: 応答時間を超過しました"

                # すべての投票が完了
                import time
                time.sleep(0.5)

                # 投票結果を集計
                approve_count = sum(1 for v in votes.values() if v == "承認")
                reject_count = sum(1 for v in votes.values() if v == "否定")
                unknown_count = sum(1 for v in votes.values() if v == "不明")

                # 決定結果
                if approve_count > reject_count:
                    decision = "承認"
                    decision_icon = "✅"
                    decision_text = f"{decision_icon} 最終決定: {decision} ({approve_count}/3)"
                elif reject_count > approve_count:
                    decision = "否定"
                    decision_icon = "❌"
                    decision_text = f"{decision_icon} 最終決定: {decision} ({reject_count}/3)"
                else:
                    decision = "保留（同数）"
                    decision_icon = "⚠️"
                    decision_text = f"{decision_icon} 最終決定: {decision} (承認 {approve_count} / 否定 {reject_count})"

                # 最終決定をMAGIボックスと同じコンテナに表示
                balthasar_vote = votes.get("BALTHASAR", "不明")
                casper_vote = votes.get("CASPER", "不明")
                melchior_vote = votes.get("MELCHIOR", "不明")

                melchior_reason = reasons.get("MELCHIOR", "回答なし")
                balthasar_reason = reasons.get("BALTHASAR", "回答なし")
                casper_reason = reasons.get("CASPER", "回答なし")

                render_magi_boxes(
                    balthasar_vote, casper_vote, melchior_vote,
                    show_decision=True, decision_text=decision_text,
                    melchior_reason=melchior_reason,
                    balthasar_reason=balthasar_reason,
                    casper_reason=casper_reason
                )

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

        analysis_sample_col4, analysis_sample_col5, analysis_sample_col6 = st.columns(3)

        with analysis_sample_col4:
            if st.button("🏥 医療とテクノロジー", use_container_width=True, key="analysis_health"):
                st.session_state.analysis_q = "AIやIoT技術が医療業界にもたらす革新について教えてください"

        with analysis_sample_col5:
            if st.button("📚 教育改革", use_container_width=True, key="analysis_education"):
                st.session_state.analysis_q = "現代の教育システムが抱える課題と、その解決策について論じてください"

        with analysis_sample_col6:
            if st.button("🚀 宇宙開発", use_container_width=True, key="analysis_space"):
                st.session_state.analysis_q = "民間企業による宇宙開発が人類にもたらす影響について分析してください"

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
                                <small>Gemini 2.5 Pro (女性)</small>
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

        vote_sample_col4, vote_sample_col5, vote_sample_col6 = st.columns(3)

        with vote_sample_col4:
            if st.button("☁️ クラウド選定", use_container_width=True, key="sample_cloud"):
                st.session_state.vote_q = "新規プロジェクトで使うべきクラウドプラットフォームは？"
                st.session_state.vote_opt1 = "AWS"
                st.session_state.vote_opt2 = "Azure"
                st.session_state.vote_opt3 = "GCP"
                st.session_state.vote_opt4 = "Oracle Cloud"

        with vote_sample_col5:
            if st.button("🎬 週末の過ごし方", use_container_width=True, key="sample_weekend"):
                st.session_state.vote_q = "今週末のチームビルディングで何をすべき？"
                st.session_state.vote_opt1 = "映画鑑賞"
                st.session_state.vote_opt2 = "スポーツ"
                st.session_state.vote_opt3 = "BBQ"
                st.session_state.vote_opt4 = "ボードゲーム"

        with vote_sample_col6:
            if st.button("🗄️ データベース選定", use_container_width=True, key="sample_db"):
                st.session_state.vote_q = "新しいアプリケーションで使うべきデータベースは？"
                st.session_state.vote_opt1 = "PostgreSQL"
                st.session_state.vote_opt2 = "MongoDB"
                st.session_state.vote_opt3 = "MySQL"
                st.session_state.vote_opt4 = "Redis"

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
