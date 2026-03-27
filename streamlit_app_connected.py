import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import date

st.set_page_config(
    page_title="PPE 안전관리 대시보드",
    layout="wide",
)

API_BASE_URL = "http://127.0.0.1:8000"

api_data = None

try:
    r = requests.get(f"{API_BASE_URL}/dashboard/today", timeout=5)
    r.raise_for_status()
    api_data = r.json()
    
except Exception as e:
    st.error(f"API 연결 실패: {e}")

# -----------------------------
# 데이터
# -----------------------------
if api_data:
    kpi = api_data.get("kpi", {})
    charts = api_data.get("charts", {})
    safety_points = api_data.get("safety_points", [])

    time_data = pd.DataFrame(charts.get("hourly_violations", []))
    if not time_data.empty:
        time_data = time_data.rename(columns={
            "time_slot": "time",
            "count": "count"
        })
        time_data["time"] = time_data["time"].replace({
            "오전": "오전<br>(08-12시)",
            "점심직후": "점심직후<br>(12-14시)",
            "오후": "오후<br>(14-18시)"
        })
    else:
        time_data = pd.DataFrame([
            {"time": "오전<br>(08-12시)", "count": 0},
            {"time": "점심직후<br>(12-14시)", "count": 0},
            {"time": "오후<br>(14-18시)", "count": 0},
        ])

    zone_data = pd.DataFrame(charts.get("zone_risk_scores", []))
    if not zone_data.empty:
        zone_data = zone_data.rename(columns={
            "zone": "zone",
            "risk_score": "risk"
        })
    else:
        zone_data = pd.DataFrame(columns=["zone", "risk"])

else:
    kpi = {}
    safety_points = []
    time_data = pd.DataFrame([
        {"time": "오전<br>(08-12시)", "count": 0},
        {"time": "점심직후<br>(12-14시)", "count": 0},
        {"time": "오후<br>(14-18시)", "count": 0},
    ])
    zone_data = pd.DataFrame(columns=["zone", "risk"])

compliance_rate_text = kpi.get("compliance_rate_text", "-")
weakest_zone_name = kpi.get("weakest_zone_name") or "-"
weakest_zone_score = kpi.get("weakest_zone_score", 0)
most_missing_ppe_name = kpi.get("most_missing_ppe_name") or "-"
most_missing_ppe_count = kpi.get("most_missing_ppe_count", 0)
priority_task_text = kpi.get("priority_task_text") or "-"

def get_zone_color(risk: int) -> str:
    if risk >= 80:
        return "#ef4444"
    if risk >= 60:
        return "#f97316"
    return "#22c55e"

# -----------------------------
# 스타일
# -----------------------------
st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

.main-title {
    font-size: 2rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.35rem;
}

.sub-title {
    color: #475569;
    font-size: 0.98rem;
    margin-bottom: 0;
}

.metric-card {
    background: #ffffff;
    border-radius: 16px;
    padding: 20px 22px;
    border: 1px solid #e2e8f0;
    border-left: 6px solid #3b82f6;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    min-height: 148px;
}

.metric-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
}

.metric-label {
    color: #475569;
    font-size: 0.9rem;
    margin-bottom: 8px;
}

.metric-value-lg {
    color: #0f172a;
    font-size: 2.2rem;
    font-weight: 800;
    line-height: 1.1;
    margin-bottom: 10px;
}

.metric-value-md {
    color: #0f172a;
    font-size: 1.35rem;
    font-weight: 800;
    line-height: 1.25;
    margin-bottom: 10px;
}

.metric-badge {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
}

.metric-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3rem;
    font-weight: 700;
    flex-shrink: 0;
}

.panel-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.25rem;
}

.tip-text {
    color: #475569;
    font-size: 0.9rem;
    margin-top: 0.4rem;
}

.alert-box {
    border-radius: 12px;
    padding: 14px 16px;
    border: 1px solid;
    margin-bottom: 12px;
}

.alert-title {
    font-size: 0.92rem;
    font-weight: 700;
    margin-bottom: 4px;
}

.alert-desc {
    font-size: 0.8rem;
    line-height: 1.45;
}

.recommend-wrap {
    border-top: 1px solid #e2e8f0;
    padding-top: 14px;
    margin-top: 14px;
}

.recommend-title {
    font-size: 0.78rem;
    color: #475569;
    margin-bottom: 8px;
    font-weight: 600;
}

.recommend-item {
    font-size: 0.82rem;
    color: #334155;
    margin-bottom: 6px;
}

.ai-card {
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    border: 1px solid #bfdbfe;
    border-radius: 16px;
    padding: 24px 18px;
    text-align: center;
}

.ai-icon-wrap {
    width: 64px;
    height: 64px;
    border-radius: 999px;
    background: white;
    margin: 0 auto 12px auto;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.7rem;
}

.ai-title {
    font-size: 1rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 6px;
}

.ai-desc {
    font-size: 0.88rem;
    color: #334155;
    margin-bottom: 10px;
    line-height: 1.5;
}

.ai-time {
    font-size: 0.78rem;
    color: #475569;
}

.quick-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 18px 18px;
    min-height: 92px;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.quick-card.highlight {
    background: #facc15;
    border-color: #eab308;
}

.quick-title {
    font-size: 0.92rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 4px;
}

.quick-desc {
    font-size: 0.8rem;
    color: #475569;
}

.quick-card.highlight .quick-desc {
    color: #334155;
}

.quick-arrow {
    float: right;
    font-size: 1rem;
    color: #94a3b8;
    font-weight: 700;
}

.quick-card.highlight .quick-arrow {
    color: #334155;
}

.small-note {
    color: #64748b;
    font-size: 0.76rem;
    margin-top: 6px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# 헬퍼 렌더 함수
# -----------------------------
def render_metric_card(title, value, badge_text, accent, badge_bg, badge_fg, icon_bg, icon_fg, icon_symbol, large=False):
    value_class = "metric-value-lg" if large else "metric-value-md"
    st.markdown(
        f"""
        <div class="metric-card" style="border-left-color:{accent};">
            <div class="metric-top">
                <div>
                    <div class="metric-label">{title}</div>
                    <div class="{value_class}">{value}</div>
                    <span class="metric-badge" style="background:{badge_bg}; color:{badge_fg};">{badge_text}</span>
                </div>
                <div class="metric-icon" style="background:{icon_bg}; color:{icon_fg};">{icon_symbol}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_alert_box(title, desc, bg, border, title_color, desc_color, icon_symbol):
    st.markdown(
        f"""
        <div class="alert-box" style="background:{bg}; border-color:{border};">
            <div class="alert-title" style="color:{title_color};">{icon_symbol} {title}</div>
            <div class="alert-desc" style="color:{desc_color};">{desc}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_quick_card(title, desc, highlight=False):
    extra_class = "highlight" if highlight else ""
    st.markdown(
        f"""
        <div class="quick-card {extra_class}">
            <div class="quick-arrow">→</div>
            <div class="quick-title">{title}</div>
            <div class="quick-desc">{desc}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# -----------------------------
# 헤더
# -----------------------------
left, date_col, site_col, refresh_col = st.columns([3.7, 1.4, 1.2, 0.7])

with left:
    st.markdown('<div class="main-title">PPE 안전관리 대시보드</div>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">오늘 현장의 안전 상태를 실시간으로 모니터링하세요</p>', unsafe_allow_html=True)

with date_col:
    selected_date = st.date_input(
        "날짜",
        value=date(2026, 3, 15),
        label_visibility="collapsed"
    )

with site_col:
    selected_site = st.selectbox(
        "현장 선택",
        ["전체 현장", "현장 1", "현장 2", "현장 3"],
        label_visibility="collapsed"
    )

with refresh_col:
    st.write("")
    st.write("")
    if st.button("새로고침", use_container_width=True):
        st.rerun()

st.write("")

# -----------------------------
# KPI 카드
# -----------------------------
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    render_metric_card(
        title="위험노출 대비 PPE 준수율",
        value= compliance_rate_text,
        badge_text="실시간 집계",
        accent="#3b82f6",
        badge_bg="#eff6ff",
        badge_fg="#1d4ed8",
        icon_bg="#eff6ff",
        icon_fg="#2563eb",
        icon_symbol="🛡",
        large=True
    )

with kpi2:
    render_metric_card(
        title="오늘 가장 취약한 구역",
        value=weakest_zone_name,
        badge_text=f"위험도 {weakest_zone_score}%",
        accent="#ef4444",
        badge_bg="#fef2f2",
        badge_fg="#b91c1c",
        icon_bg="#fef2f2",
        icon_fg="#dc2626",
        icon_symbol="⚠"
    )

with kpi3:
    render_metric_card(
        title="반복 누락 PPE",
        value=most_missing_ppe_name,
        badge_text=f"{most_missing_ppe_count}회 반복",
        accent="#f97316",
        badge_bg="#fff7ed",
        badge_fg="#c2410c",
        icon_bg="#fff7ed",
        icon_fg="#ea580c",
        icon_symbol="⛑"
    )

with kpi4:
    render_metric_card(
        title="우선 개입 필요 작업",
        value=priority_task_text,
        badge_text="우선 확인",
        accent="#a855f7",
        badge_bg="#faf5ff",
        badge_fg="#7e22ce",
        icon_bg="#faf5ff",
        icon_fg="#9333ea",
        icon_symbol="⏱"
    )

st.write("")

# -----------------------------
# 메인 차트 + 우측 패널
# -----------------------------
main_col, side_col = st.columns([2.2, 1])

with main_col:
    st.markdown('<div class="panel-title">시간대별 PPE 이탈 건수</div>', unsafe_allow_html=True)

    fig_time = go.Figure()
    fig_time.add_trace(
        go.Bar(
            x=time_data["time"],
            y=time_data["count"],
            marker_color="#3b82f6",
            hovertemplate="시간대: %{x}<br>건수: %{y}건<extra></extra>",
        )
    )
    fig_time.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(
            title="",
            tickfont=dict(size=12),
            showgrid=False,
            zeroline=False
        ),
        yaxis=dict(
            title="",
            tickfont=dict(size=12),
            gridcolor="#e2e8f0",
            zeroline=False
        ),
        showlegend=False,
    )
    st.plotly_chart(fig_time, use_container_width=True, config={"displayModeBar": False})
    st.markdown('<div class="tip-text">시간대별 API 집계 결과입니다</div>', unsafe_allow_html=True)

    st.write("")

    st.markdown('<div class="panel-title">작업구역별 위험도</div>', unsafe_allow_html=True)

    fig_zone = go.Figure()
    fig_zone.add_trace(
        go.Bar(
            x=zone_data["risk"],
            y=zone_data["zone"],
            orientation="h",
            marker_color=[get_zone_color(v) for v in zone_data["risk"]],
            hovertemplate="구역: %{y}<br>위험도: %{x}%<extra></extra>",
        )
    )
    fig_zone.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(
            title="",
            tickfont=dict(size=12),
            gridcolor="#e2e8f0",
            zeroline=False,
            range=[0, 100]
        ),
        yaxis=dict(
            title="",
            tickfont=dict(size=12),
            autorange="reversed"
        ),
        showlegend=False,
    )
    st.plotly_chart(fig_zone, use_container_width=True, config={"displayModeBar": False})
    st.markdown(
    f'<div class="tip-text">{weakest_zone_name} 위험도 {weakest_zone_score}%</div>',
    unsafe_allow_html=True
)

with side_col:
    st.markdown('<div class="panel-title">오늘의 안전개입 포인트</div>', unsafe_allow_html=True)

    if safety_points:
        for point in safety_points:
            render_alert_box(
                title="안전 포인트",
                desc=point,
                bg="#fef2f2",
                border="#fecaca",
                title_color="#7f1d1d",
                desc_color="#b91c1c",
                icon_symbol="⚠"
        )
    else:
        render_alert_box(
            title="안전 포인트",
            desc="오늘 표시할 안전 포인트가 없습니다",
            bg="#f8fafc",
            border="#cbd5e1",
            title_color="#334155",
            desc_color="#475569",
            icon_symbol="ℹ"
    )

    st.markdown(
        """
        <div class="recommend-wrap">
            <div class="recommend-title">권장 조치사항</div>
            <div class="recommend-item">• 점심 직후 현장 순찰 강화</div>
            <div class="recommend-item">• 고소작업 전 안전대 체결 확인</div>
            <div class="recommend-item">• 절단작업 전 보호장갑 착용 점검</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    st.markdown(
        """
        <div class="ai-card">
            <div class="ai-icon-wrap">🛡</div>
            <div class="ai-title">AI 안전 분석</div>
            <div class="ai-desc">실시간 패턴 분석으로<br>더 안전한 현장을 만듭니다</div>
            <div class="ai-time">마지막 업데이트: 방금 전</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.write("")
st.write("")

# -----------------------------
# 하단 빠른 이동 카드
# 현재는 정적 카드로 구성
# 멀티페이지로 바꿀 때는 st.switch_page() 또는 st.page_link() 연결
# -----------------------------
nav1, nav2, nav3, nav4 = st.columns(4)

with nav1:
    render_quick_card("데이터 입력", "PPE 로그 업로드")

with nav2:
    render_quick_card("분석 상세 보기", "위험패턴 분석")

with nav3:
    render_quick_card("아침조회 리포트", "브리핑 자료")

with nav4:
    render_quick_card("인센티브 현황", "개선 현황 보기", highlight=True)

st.markdown(
    '<div class="small-note">하단 카드는 현재 UI 표시용입니다. Streamlit 멀티페이지로 확장할 때 pages 폴더와 연결하면 됩니다.</div>',
    unsafe_allow_html=True
)
