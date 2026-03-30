import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests

st.set_page_config(page_title="개선 현황", layout="wide")

API_BASE_URL = "https://ppe-dashboard-backend.onrender.com"

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
    line-height: 1.6;
}

.section-card-head-fixed {
    min-height: 210px;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
}

.section-title-fixed {
    min-height: 54px;
    display: flex;
    align-items: center;
    margin-bottom: 0.8rem;
}

.section-sub-fixed {
    min-height: 72px;
    display: flex;
    align-items: flex-start;
    line-height: 1.6;
    color: #64748b;
    font-size: 0.86rem;
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
    font-size: 0.92rem;
    color: #1e3a8a;
    line-height: 1.7;
    font-weight: 700;
}

.metric-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 20px;
    padding: 20px 22px;
    min-height: 190px;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.metric-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 14px;
    height: 100%;
}

.metric-label {
    color: #64748b;
    font-size: 0.92rem;
    margin-bottom: 10px;
    font-weight: 600;
    min-height: 28px;
}

.metric-value {
    color: #0f172a;
    font-size: 1.8rem;
    font-weight: 800;
    line-height: 1.15;
    margin-bottom: 10px;
    letter-spacing: -0.02em;
    min-height: 84px;
    display: flex;
    align-items: center;
    word-break: keep-all;
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

.recommend-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 14px;
}

.recommend-card {
    border-radius: 18px;
    padding: 18px 20px;
    border: 1px solid;
    min-height: 128px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.recommend-title {
    font-size: 1.02rem;
    font-weight: 800;
    margin-bottom: 8px;
    line-height: 1.35;
}

.recommend-desc {
    font-size: 0.93rem;
    line-height: 1.65;
    word-break: keep-all;
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
# 데이터 전처리
# =========================
data = fetch_incentive_data()

if data:
    kpis = data.get("kpis", {})
    charts = data.get("charts", {})
    team_comparison_chart = data.get("team_comparison_chart", [])
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

violation_df = pd.DataFrame(charts.get("violation_trend_chart", []))
if not violation_df.empty:
    violation_df["count"] = pd.to_numeric(violation_df["count"], errors="coerce").fillna(0).astype(int)

ppe_df = pd.DataFrame(charts.get("ppe_trend_chart", []))
if not ppe_df.empty:
    ppe_df["count"] = pd.to_numeric(ppe_df["count"], errors="coerce").fillna(0).astype(int)

team_df = pd.DataFrame(team_comparison_chart)
if not team_df.empty:
    team_df["initial_rate"] = pd.to_numeric(team_df["initial_rate"], errors="coerce").fillna(0)
    team_df["current_rate"] = pd.to_numeric(team_df["current_rate"], errors="coerce").fillna(0)
    team_df = team_df.sort_values(by="team").reset_index(drop=True)

imp_val = kpis.get("improvement_rate", 0)
imp_text = f"+{imp_val}%p" if imp_val > 0 else f"{imp_val}%p"
imp_icon = "📈" if imp_val > 0 else "📉"
imp_color, imp_bg, imp_fg = (
    ("#22c55e", "#dcfce7", "#166534") if imp_val >= 0
    else ("#ef4444", "#fef2f2", "#b91c1c")
)

rep_val = kpis.get("repeat_ppe_reduction_rate", 0)
rep_text = f"{abs(rep_val)}% 감소" if rep_val >= 0 else f"{abs(rep_val)}% 증가 🚨"
rep_icon = "📉" if rep_val >= 0 else "📈"
rep_color, rep_bg, rep_fg = (
    ("#ef4444", "#fef2f2", "#b91c1c") if rep_val < 0
    else ("#3b82f6", "#dbeafe", "#1d4ed8")
)

risk_val = kpis.get("risk_recurrence_reduction_rate", 0)
risk_text = f"{abs(risk_val)}% 감소" if risk_val >= 0 else f"{abs(risk_val)}% 증가 🚨"
risk_icon = "📊" if risk_val >= 0 else "📈"
risk_color, risk_bg, risk_fg = (
    ("#ef4444", "#fef2f2", "#b91c1c") if risk_val < 0
    else ("#a855f7", "#f3e8ff", "#7e22ce")
)

best_team = kpis.get("best_team", "-")

# =========================
# 헤더
# =========================
st.markdown('<div class="main-title">개선 및 인센티브 현황</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">주간 개선 흐름과 팀별 성과를 통해 안전문화 개선 방향을 확인합니다</div>',
    unsafe_allow_html=True
)

st.markdown("""
<div class="principle-card">
    <div class="principle-title">운영 원칙</div>
    <div class="principle-item">• 개인 처벌보다 팀 단위 개선 유도에 초점을 둡니다.</div>
    <div class="principle-item">• 절대 수준보다 얼마나 좋아졌는지, 즉 개선율을 중심으로 평가합니다.</div>
    <div class="principle-item">• 반복 위반 감소와 참여도를 함께 반영해 지속 가능한 안전문화를 설계합니다.</div>
</div>
""", unsafe_allow_html=True)

# =========================
# KPI
# =========================
c1, c2, c3, c4 = st.columns(4)

with c1:
    render_metric_card("이번 주 개선율", imp_text, "전주 대비 변화", imp_color, imp_bg, imp_fg, imp_bg, imp_color, imp_icon)

with c2:
    render_metric_card("반복 누락 추이", rep_text, "5주간 집계", rep_color, rep_bg, rep_fg, rep_bg, rep_color, rep_icon)

with c3:
    render_metric_card("위험행동 재발 추이", risk_text, "반복 행동 추이", risk_color, risk_bg, risk_fg, risk_bg, risk_color, risk_icon)

with c4:
    render_metric_card("우수 개선 팀", best_team, "현재 최고 개선", "#f97316", "#ffedd5", "#c2410c", "#ffedd5", "#ea580c", "🏅")

st.write("")

# =========================
# 차트 1행
# =========================
l1, r1 = st.columns(2)

with l1:
    st.markdown('<div class="section-card"><div class="section-title">주간 위험행동 건수 추이</div>', unsafe_allow_html=True)
    fig_v = go.Figure()
    if not violation_df.empty:
        fig_v.add_trace(go.Scatter(
            x=violation_df["label"].astype(str).tolist(),
            y=violation_df["count"].tolist(),
            mode="lines+markers",
            line=dict(color="#3b82f6", width=3, shape="spline"),
            marker=dict(size=8, color="#2563eb", line=dict(color="white", width=2)),
            fill="tozeroy",
            fillcolor="rgba(59, 130, 246, 0.15)",
            hovertemplate="%{x}: %{y}건<extra></extra>"
        ))
    fig_v.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=20, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        xaxis=dict(showgrid=False, tickfont=dict(size=12, color="#334155")),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9", zeroline=False, tickfont=dict(size=11, color="#94a3b8"), rangemode="tozero")
    )
    st.plotly_chart(fig_v, use_container_width=True, config={"displayModeBar": False}, key="p5_violation_chart")
    st.markdown('<div class="insight-box" style="background:#eff6ff; border-color:#bfdbfe; color:#1e3a8a;">📌 주간 위험행동 추세를 기반으로 개선 흐름을 추적합니다.</div></div>', unsafe_allow_html=True)

with r1:
    st.markdown('<div class="section-card"><div class="section-title">주간 PPE 누락 건수 추이</div>', unsafe_allow_html=True)
    fig_p = go.Figure()
    if not ppe_df.empty:
        fig_p.add_trace(go.Scatter(
            x=ppe_df["label"].astype(str).tolist(),
            y=ppe_df["count"].tolist(),
            mode="lines+markers",
            line=dict(color="#f97316", width=3, shape="spline"),
            marker=dict(size=8, color="#ea580c", line=dict(color="white", width=2)),
            fill="tozeroy",
            fillcolor="rgba(249, 115, 22, 0.15)",
            hovertemplate="%{x}: %{y}건<extra></extra>"
        ))
    fig_p.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=20, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        xaxis=dict(showgrid=False, tickfont=dict(size=12, color="#334155")),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9", zeroline=False, tickfont=dict(size=11, color="#94a3b8"), rangemode="tozero")
    )
    st.plotly_chart(fig_p, use_container_width=True, config={"displayModeBar": False}, key="p5_ppe_chart")
    st.markdown('<div class="insight-box" style="background:#fff7ed; border-color:#fed7aa; color:#9a3412;">📌 반복 누락 PPE 감소 여부를 통해 보호구 착용문화 개선 수준을 판단합니다.</div></div>', unsafe_allow_html=True)

# =========================
# 팀 비교
# =========================
st.markdown('<div class="section-card"><div class="section-title">팀별 개선율 비교</div><div class="section-sub">초기 준수율과 현재 준수율을 비교해 팀별 개선 정도를 확인합니다</div>', unsafe_allow_html=True)

fig_team = go.Figure()
if not team_df.empty:
    fig_team.add_trace(go.Bar(
        x=team_df["team"].astype(str).tolist(),
        y=team_df["initial_rate"].tolist(),
        name="초기 준수율 %",
        marker=dict(color="rgba(148, 163, 184, 0.65)", line=dict(color="#94a3b8", width=1.5)),
        offsetgroup="1",
        hovertemplate="팀: %{x}<br>초기 준수율: %{y}%<extra></extra>"
    ))
    fig_team.add_trace(go.Bar(
        x=team_df["team"].astype(str).tolist(),
        y=team_df["current_rate"].tolist(),
        name="현재 준수율 %",
        marker=dict(color="rgba(59, 130, 246, 0.75)", line=dict(color="#2563eb", width=1.5)),
        offsetgroup="2",
        hovertemplate="팀: %{x}<br>현재 준수율: %{y}%<extra></extra>"
    ))

fig_team.update_layout(
    height=340,
    margin=dict(l=10, r=10, t=10, b=10),
    plot_bgcolor="white",
    paper_bgcolor="white",
    barmode="group",
    bargap=0.45,
    bargroupgap=0.1,
    xaxis=dict(showgrid=False, tickfont=dict(size=12, color="#334155")),
    yaxis=dict(showgrid=True, gridcolor="#f1f5f9", zeroline=False, tickfont=dict(size=11, color="#94a3b8"), ticksuffix="%"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11))
)
st.plotly_chart(fig_team, use_container_width=True, config={"displayModeBar": False}, key="p5_team_chart")
st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 추천 보상 방안 + 제도 설계 원칙
# =========================
col_left, col_right = st.columns([1.25, 1])

with col_left:
    st.markdown(
        '<div class="section-card section-card-head-fixed">'
        '<div class="section-title section-title-fixed">추천 보상 방안</div>'
        '<div class="section-sub-fixed">개선율과 참여도를 근거로 비징계형 인센티브를 설계합니다</div>'
        '<div class="recommend-grid">',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="recommend-card" style="background:#f0fdf4; border-color:#86efac; color:#166534;">
        <div class="recommend-title">1) 신체 보호구·작업보조용품 지원</div>
        <div class="recommend-desc">
            주간 PPE 누락 감소가 확인된 팀을 대상으로 아치 서포트 깔창, 관절 보호대, 프리미엄 장갑 등
            작업 피로 저감형 용품을 지급합니다. 이는 근골격계 부담과 작업 피로를 줄이는 직접적 지원책입니다.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="recommend-card" style="background:#eff6ff; border-color:#93c5fd; color:#1d4ed8;">
        <div class="recommend-title">2) 휴게환경 우선 이용 인센티브</div>
        <div class="recommend-desc">
            우수 개선 팀에 프리미엄 휴게공간, 냉난방 보강 좌석, 회복용 비품 등을 우선 제공해
            안전수칙 준수가 실제 작업환경 개선으로 이어진다는 경험을 만들도록 설계합니다.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="recommend-card" style="background:#faf5ff; border-color:#d8b4fe; color:#7e22ce;">
        <div class="recommend-title">3) 지역상생형 팀 인센티브</div>
        <div class="recommend-desc">
            현장 인근 식당·상점에서 사용할 수 있는 지역 연계 상품권 또는 제휴 쿠폰을 제공해
            팀 보상과 지역 상권 활성화를 함께 도모합니다. 안전 예산이 지역사회와 연결되는 구조를 강조할 수 있습니다.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="recommend-card" style="background:#fff7ed; border-color:#fdba74; color:#c2410c;">
        <div class="recommend-title">4) 회복 지원·우수사례 확산</div>
        <div class="recommend-desc">
            우수 개선 팀을 대상으로 회복 키트, 스트레칭 프로그램, 방문형 컨디션 케어 등 실질 지원을 제공하고,
            동시에 개선 사례를 공유해 현장 전체의 자발적 안전문화 확산으로 연결합니다.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div></div>', unsafe_allow_html=True)

with col_right:
    st.markdown(
        '<div class="section-card section-card-head-fixed">'
        '<div class="section-title section-title-fixed">제도 설계 원칙</div>'
        '<div class="section-sub-fixed">AI 기반 개선 지표를 활용해 팀 중심의 비징계형 안전 인센티브를 운영합니다</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="notice-box">
    • 본 플랫폼의 인센티브는 <b>단순 현금 보상</b>보다 <b>행동기반안전(BBS)</b>과 <b>비징계형 개선 유도</b>에 초점을 둡니다.<br><br>
    • AI 대시보드가 산출하는 <b>이번 주 개선율</b>, <b>반복 누락 감소율</b>, <b>우수 개선 팀</b>을 근거로 보상을 투명하게 제시합니다.<br><br>
    • 평가는 개인 처벌이 아니라 <b>팀 단위 개선 흐름</b>을 중심으로 하며, 절대 수준보다 <b>얼마나 좋아졌는지</b>를 중요하게 봅니다.<br><br>
    • 인센티브는 보호구 지원, 휴게환경 개선, 회복 지원처럼 현장 체감도가 높은 항목으로 구성해 자발적 참여를 높이도록 설계합니다.
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)