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

# CSS スタイリング
st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .model-card {
        border-left: 4px solid;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
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
        - 🟡 **CASPER** (Gemini 2.5 Pro)
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

            # 投票過程セクション全体をplaceholderで管理
            progress_section = st.empty()

            with progress_section.container():
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

                                # 賛成/反対を抽出
                                if "【投票】賛成" in answer or "賛成" in answer[:100]:
                                    vote_result = "賛成"
                                    votes[model_name] = "賛成"
                                elif "【投票】反対" in answer or "反対" in answer[:100]:
                                    vote_result = "反対"
                                    votes[model_name] = "反対"
                                else:
                                    vote_result = "不明"
                                    votes[model_name] = "不明"

                                reasons[model_name] = answer

                                # ステータスを更新（投票結果を表示）
                                with status_placeholders[model_name].container():
                                    st.markdown(f"**{model_name}**")
                                    if status == "success" and not answer.startswith("エラー") and not answer.startswith("回答なし"):
                                        if vote_result == "賛成":
                                            st.success("✅ 賛成")
                                        elif vote_result == "反対":
                                            st.error("❌ 反対")
                                        else:
                                            st.warning("❓ 不明")
                                    else:
                                        st.error("❌ エラー")
                            except Exception as e:
                                model_name = futures[future]
                                results[model_name] = {"answer": f"エラー: {str(e)}", "status": "error"}
                                votes[model_name] = "不明"
                                reasons[model_name] = f"エラー: {str(e)}"
                                with status_placeholders[model_name].container():
                                    st.markdown(f"**{model_name}**")
                                    st.error("❌ エラー")
                    except concurrent.futures.TimeoutError:
                        for future, model_name in futures.items():
                            if model_name not in results:
                                results[model_name] = {"answer": "タイムアウト: 応答時間を超過しました", "status": "timeout"}
                                votes[model_name] = "不明"
                                reasons[model_name] = "タイムアウト: 応答時間を超過しました"
                                with status_placeholders[model_name].container():
                                    st.markdown(f"**{model_name}**")
                                    st.error("⏱️ タイムアウト")

                # すべての投票が完了したら投票過程セクションを非表示
                import time
                time.sleep(1.5)  # 結果を確認する時間を与える
                progress_section.empty()  # 投票過程セクション全体を削除

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
                            <small>Gemini 2.5 Pro (女性)</small>
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
