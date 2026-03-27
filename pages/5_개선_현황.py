import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests

st.set_page_config(
    page_title="개선 현황",
    layout="wide"
)

API_BASE_URL = "http://127.0.0.1:8000"


# =========================
# API
# =========================
def fetch_incentive_data():
    try:
        res = requests.get(f"{API_BASE_URL}/improvement/summary", timeout=8)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"개선 현황 조회 실패: {e}")
        return None


# =========================
# 스타일
# =========================
st.markdown("""
<style>
.block-container {
    padding-top: 2.4rem;
    padding-bottom: 2rem;
    max-width: 1480px;
}

.main-title {
    font-size: 2.1rem;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 0.2rem;
    letter-spacing: -0.02em;
}

.sub-title {
    color: #64748b;
    font-size: 1rem;
    margin-bottom: 1rem;
}

.section-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 22px;
    padding: 22px 22px;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
    margin-bottom: 1rem;
}

.section-title {
    font-size: 1.15rem;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 0.8rem;
}

.section-sub {
    color: #64748b;
    font-size: 0.86rem;
    margin-bottom: 1rem;
}

.principle-card {
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    border: 1px solid #bfdbfe;
    border-radius: 22px;
    padding: 20px 22px;
    margin-bottom: 1rem;
}

.principle-title {
    font-size: 1.05rem;
    font-weight: 800;
    color: #1d4ed8;
    margin-bottom: 12px;
}

.principle-item {
    font-size: 0.9rem;
    color: #1e3a8a;
    line-height: 1.6;
    font-weight: 700;
}

.metric-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 20px;
    padding: 20px 22px;
    min-height: 145px;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
}

.metric-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 14px;
}

.metric-label {
    color: #64748b;
    font-size: 0.92rem;
    margin-bottom: 10px;
    font-weight: 600;
}

.metric-value {
    color: #0f172a;
    font-size: 1.8rem;
    font-weight: 800;
    line-height: 1.15;
    margin-bottom: 10px;
    letter-spacing: -0.02em;
}

.metric-badge {
    display: inline-block;
    padding: 6px 11px;
    border-radius: 999px;
    font-size: 0.76rem;
    font-weight: 700;
}

.metric-icon {
    width: 52px;
    height: 52px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.35rem;
    flex-shrink: 0;
}

.insight-box {
    border-radius: 14px;
    padding: 12px 14px;
    margin-top: 0.8rem;
    font-size: 0.87rem;
    line-height: 1.55;
    border: 1px solid;
}

.summary-item {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 10px;
    color: #334155;
    font-size: 0.9rem;
    line-height: 1.6;
}

.recommend-card {
    border-radius: 18px;
    padding: 16px 18px;
    margin-bottom: 12px;
    border: 1px solid;
}

.recommend-title {
    font-size: 1rem;
    font-weight: 800;
    margin-bottom: 8px;
}

.recommend-desc {
    font-size: 0.9rem;
    line-height: 1.6;
}

.notice-box {
    background: #eff6ff;
    border: 1px solid #93c5fd;
    border-radius: 18px;
    padding: 18px;
    color: #1e3a8a;
    font-size: 0.92rem;
    line-height: 1.7;
}

.stButton > button {
    border-radius: 14px;
    font-weight: 700;
    min-height: 44px;
}
</style>
""", unsafe_allow_html=True)


# =========================
# 렌더
# =========================
def render_metric_card(title, value, badge_text, accent, badge_bg, badge_fg, icon_bg, icon_fg, icon_symbol):
    st.markdown(
        f"""
        <div class="metric-card" style="border-left:6px solid {accent};">
            <div class="metric-top">
                <div>
                    <div class="metric-label">{title}</div>
                    <div class="metric-value">{value}</div>
                    <span class="metric-badge" style="background:{badge_bg}; color:{badge_fg};">{badge_text}</span>
                </div>
                <div class="metric-icon" style="background:{icon_bg}; color:{icon_fg};">{icon_symbol}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================
# 데이터
# =========================
data = fetch_incentive_data()

if data:
    kpis = data.get("kpis", {})
    charts = data.get("charts", {})
    team_comparison_chart = data.get("team_comparison_chart", [])
    team_summary = data.get("team_summary", [])
else:
    kpis = {
        "improvement_rate": 0,
        "repeat_ppe_reduction_rate": 0,
        "risk_recurrence_reduction_rate": 0,
        "best_team": "-"
    }
    charts = {
        "violation_trend_chart": [],
        "ppe_trend_chart": []
    }
    team_comparison_chart = []
    team_summary = []

violation_df = pd.DataFrame(charts.get("violation_trend_chart", []))
ppe_df = pd.DataFrame(charts.get("ppe_trend_chart", []))
team_df = pd.DataFrame(team_comparison_chart)

improvement_rate = kpis.get("improvement_rate", 0)
repeat_reduction = kpis.get("repeat_ppe_reduction_rate", 0)
risk_reduction = kpis.get("risk_recurrence_reduction_rate", 0)
best_team = kpis.get("best_team", "-")


# =========================
# 헤더
# =========================
st.markdown('<div class="main-title">개선 및 인센티브 현황</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">주간 개선 흐름과 팀별 성과를 통해 안전문화 개선 방향을 확인합니다</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="principle-card">
        <div class="principle-title">운영 원칙</div>
        <div class="principle-item">• 개인 처벌 X → 팀 개선 중심</div>
        <div class="principle-item">• 절대 평가 X → 개선율 중심</div>
        <div class="principle-item">• 참여와 감소를 함께 반영</div>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================
# KPI
# =========================
c1, c2, c3, c4 = st.columns(4)

with c1:
    render_metric_card(
        "이번 주 개선율",
        f"{improvement_rate}%p",
        "전주 대비 변화",
        "#22c55e",
        "#dcfce7",
        "#166534",
        "#dcfce7",
        "#16a34a",
        "📈"
    )

with c2:
    render_metric_card(
        "반복 누락 감소율",
        f"{repeat_reduction}%",
        "5주간 집계",
        "#3b82f6",
        "#dbeafe",
        "#1d4ed8",
        "#dbeafe",
        "#2563eb",
        "📉"
    )

with c3:
    render_metric_card(
        "위험행동 재발 감소율",
        f"{risk_reduction}%",
        "반복 행동 감소",
        "#a855f7",
        "#f3e8ff",
        "#7e22ce",
        "#f3e8ff",
        "#9333ea",
        "📊"
    )

with c4:
    render_metric_card(
        "우수 개선 팀",
        best_team,
        "현재 최고 개선",
        "#f97316",
        "#ffedd5",
        "#c2410c",
        "#ffedd5",
        "#ea580c",
        "🏅"
    )

st.write("")


# =========================
# 차트 1행
# =========================
l1, r1 = st.columns(2)

with l1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">주간 위험행동 건수 추이</div>', unsafe_allow_html=True)

    fig_v = go.Figure()
    if not violation_df.empty:
        fig_v.add_trace(
            go.Scatter(
                x=violation_df["label"],
                y=violation_df["count"],
                mode="lines+markers",
                line=dict(color="#2563eb", width=3),
                marker=dict(size=8),
                hovertemplate="%{x}: %{y}건<extra></extra>"
            )
        )

    max_v = int(violation_df["count"].max()) if not violation_df.empty else 0
    y_max_v = max(10, ((max_v + 4) // 5 + 1) * 5)

    fig_v.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#e2e8f0", dtick=5, range=[0, y_max_v])
    )

    st.plotly_chart(fig_v, use_container_width=True, config={"displayModeBar": False}, key="p5_violation_chart")
    st.markdown(
        '<div class="insight-box" style="background:#eff6ff; border-color:#bfdbfe; color:#1e3a8a;">📌 주간 위험행동 추세를 기반으로 개선 흐름을 추적합니다.</div>',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

with r1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">주간 PPE 누락 건수 추이</div>', unsafe_allow_html=True)

    fig_p = go.Figure()
    if not ppe_df.empty:
        fig_p.add_trace(
            go.Scatter(
                x=ppe_df["label"],
                y=ppe_df["count"],
                mode="lines+markers",
                line=dict(color="#f97316", width=3),
                marker=dict(size=8),
                hovertemplate="%{x}: %{y}건<extra></extra>"
            )
        )

    max_p = int(ppe_df["count"].max()) if not ppe_df.empty else 0
    y_max_p = max(10, ((max_p + 4) // 5 + 1) * 5)

    fig_p.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#e2e8f0", dtick=5, range=[0, y_max_p])
    )

    st.plotly_chart(fig_p, use_container_width=True, config={"displayModeBar": False}, key="p5_ppe_chart")
    st.markdown(
        '<div class="insight-box" style="background:#fff7ed; border-color:#fed7aa; color:#9a3412;">📌 반복 누락 PPE 감소 여부를 통해 보호구 착용문화 개선 수준을 판단합니다.</div>',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)


# =========================
# 팀 비교
# =========================
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">팀별 개선율 비교</div>', unsafe_allow_html=True)
st.markdown('<div class="section-sub">초기 준수율과 현재 준수율을 비교해 팀별 개선 정도를 확인합니다</div>', unsafe_allow_html=True)

fig_team = go.Figure()

if not team_df.empty:
    fig_team.add_trace(
        go.Bar(
            x=team_df["team"],
            y=team_df["initial_rate"],
            name="초기 준수율 %",
            marker=dict(
                color="#cbd5e1",
                line=dict(color="#94a3b8", width=0.6)
            ),
            width=0.28,
            offsetgroup="1",
            hovertemplate="%{x}<br>초기 준수율: %{y}%<extra></extra>"
        )
    )

    fig_team.add_trace(
        go.Bar(
            x=team_df["team"],
            y=team_df["current_rate"],
            name="현재 준수율 %",
            marker=dict(
                color=["#3b82f6", "#60a5fa", "#818cf8", "#22c55e"][:len(team_df)],
                line=dict(color="#ffffff", width=0.6)
            ),
            width=0.28,
            offsetgroup="2",
            hovertemplate="%{x}<br>현재 준수율: %{y}%<extra></extra>"
        )
    )

fig_team.update_layout(
    height=340,
    margin=dict(l=10, r=10, t=10, b=10),
    plot_bgcolor="white",
    paper_bgcolor="white",
    barmode="group",
    bargap=0.42,
    bargroupgap=0.12,
    xaxis=dict(
        showgrid=False,
        tickfont=dict(size=12, color="#334155")
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor="#e2e8f0",
        gridwidth=1,
        zeroline=False,
        dtick=20,
        range=[0, 100],
        tickfont=dict(size=11, color="#475569")
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font=dict(size=11)
    )
)

try:
    fig_team.update_layout(barcornerradius=10)
except Exception:
    pass

st.plotly_chart(
    fig_team,
    use_container_width=True,
    config={"displayModeBar": False},
    key="p5_team_chart"
)


# =========================
# 추천 보상 방안 + 안내
# =========================
col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">추천 보상 방안</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="recommend-card" style="background:#f0fdf4; border-color:#86efac; color:#166534;">
            <div class="recommend-title">1) 체력 회복 지원</div>
            <div class="recommend-desc">월 1회 우수 개선 팀 대상 간식/음료 또는 회복 키트 제공</div>
        </div>

        <div class="recommend-card" style="background:#eff6ff; border-color:#93c5fd; color:#1d4ed8;">
            <div class="recommend-title">2) 보호장치 우선권</div>
            <div class="recommend-desc">개선 팀에 신규 안전모, 프리미엄 장갑, 보조 보호장비 우선 지급</div>
        </div>

        <div class="recommend-card" style="background:#faf5ff; border-color:#d8b4fe; color:#7e22ce;">
            <div class="recommend-title">3) 휴게환경 개선</div>
            <div class="recommend-desc">분기 우수 팀 대상 휴게공간 환경 개선 또는 복지 항목 확대</div>
        </div>

        <div class="recommend-card" style="background:#fff7ed; border-color:#fdba74; color:#c2410c;">
            <div class="recommend-title">4) 우수사례 공유</div>
            <div class="recommend-desc">안전 개선 사례를 사내 게시판/회의에서 공유해 팀 동기 부여 강화</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">중요 안내사항</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="notice-box">
            • 본 시스템은 처벌보다 <b>개선 문화 형성</b>을 목표로 합니다.<br><br>
            • 팀별 개선율은 현재 상태보다 <b>얼마나 좋아졌는지</b>를 보기 위한 지표입니다.<br><br>
            • 센서 데이터만으로 단정하지 않고, 실제 교육 참여와 현장 개선 활동을 함께 반영하는 것이 바람직합니다.<br><br>
            • 반복 위반 감소와 PPE 누락 감소는 즉시 성과뿐 아니라 장기적인 안전문화 수준을 보여주는 핵심 지표입니다.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown('</div>', unsafe_allow_html=True)