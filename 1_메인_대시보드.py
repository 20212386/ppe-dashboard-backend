import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import date

st.set_page_config(page_title="PPE 안전관리 대시보드", page_icon="🦺", layout="wide")

API_BASE_URL = "https://ppe-dashboard-backend.onrender.com"

# =========================
# API
# =========================
def fetch_dashboard_data(target_date: str, site: str):
    try:
        params = {"target_date": target_date}
        if site and site != "전체 현장":
            params["site"] = site
        res = requests.get(f"{API_BASE_URL}/dashboard/today", params=params, timeout=20)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"대시보드 데이터 조회 실패: {e}")
        return None

# =========================
# 유틸
# =========================
def safe_text(value, default="-"):
    if value is None: return default
    text = str(value).strip()
    if text == "" or text.lower() in ["none", "nan", "null"]: return default
    return text

def build_ai_summary(report_date, weakest_zone_name, weakest_zone_score, most_missing_ppe_name, priority_task_text):
    w_name, p_name, t_text = safe_text(weakest_zone_name), safe_text(most_missing_ppe_name), safe_text(priority_task_text)
    items = []
    if w_name != "-": items.append(f"{report_date} 기준 가장 취약한 구역은 <b>{w_name}</b>이며 해당 구역 내 위반비율은 <b>{weakest_zone_score}%</b>입니다.")
    if p_name != "-": items.append(f"반복 누락 PPE는 <b>{p_name}</b>입니다. 해당 보호구 착용 확인을 우선 강화해야 합니다.")
    if t_text != "-": items.append(f"우선 개입 필요 작업은 <b>{t_text}</b>입니다.")
    return items if items else ["오늘은 위반 데이터가 없어 전반적으로 양호합니다."]

def render_metric_card(title, value, badge_text, accent, badge_bg, badge_fg, icon_bg, icon_fg, icon_symbol):
    st.markdown(
        f"""
        <div class="metric-card" style="border-left: 6px solid {accent};">
            <div class="metric-top">
                <div class="metric-left">
                    <div class="metric-title">{title}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-badge" style="background:{badge_bg}; color:{badge_fg};">{badge_text}</div>
                </div>
                <div class="metric-icon" style="background:{icon_bg}; color:{icon_fg};">{icon_symbol}</div>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

# =========================
# 스타일 (토스/애플 감성 100% 이식)
# =========================
st.markdown("""
<style>
.block-container { padding-top: 1.7rem; padding-bottom: 2rem; max-width: 1500px; }
.main-title { font-size: 2.15rem; font-weight: 800; color: #0f172a; line-height: 1.2; letter-spacing: -0.02em; margin-bottom: 0.25rem; }
.main-subtitle { font-size: 0.98rem; color: #64748b; margin-bottom: 1.1rem; }
.section-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 22px; padding: 22px 22px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05); margin-bottom: 1rem; }
.section-title { font-size: 1.16rem; font-weight: 800; color: #0f172a; margin-bottom: 0.35rem; }
.section-sub { color: #64748b; font-size: 0.88rem; margin-bottom: 1.2rem; }
.metric-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 20px; padding: 18px 20px; min-height: 158px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05); }
.metric-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; }
.metric-left { flex: 1; min-width: 0; }
.metric-title { color: #64748b; font-size: 0.92rem; font-weight: 700; margin-bottom: 10px; line-height: 1.45; word-break: keep-all; }
.metric-value { color: #0f172a; font-size: 1.72rem; font-weight: 800; line-height: 1.18; letter-spacing: -0.02em; margin-bottom: 10px; word-break: keep-all; white-space: normal; }
.metric-badge { display: inline-block; padding: 7px 11px; border-radius: 999px; font-size: 0.76rem; font-weight: 800; }
.metric-icon { width: 52px; height: 52px; border-radius: 15px; display: flex; align-items: center; justify-content: center; font-size: 1.28rem; flex-shrink: 0; }
.insight-box { border-radius: 16px; padding: 16px 18px; margin-top: 0.5rem; font-size: 0.92rem; font-weight: 700; border: 1px solid; line-height: 1.6; }
.ai-title-row { display: flex; align-items: center; gap: 10px; margin-bottom: 0.25rem; }
.ai-emoji { font-size: 1.4rem; line-height: 1; }
.ai-title { font-size: 1.1rem; font-weight: 800; color: #0f172a; }
.ai-sub { color: #64748b; font-size: 0.88rem; margin-bottom: 1rem; }
.ai-list { margin: 0; padding-left: 1.2rem; }
.ai-list li { margin-bottom: 0.8rem; color: #334155; line-height: 1.7; font-size: 0.95rem; word-break: keep-all; font-weight: 500; }
.ai-updated { color: #94a3b8; font-size: 0.84rem; font-weight: 600; margin-top: 1.5rem; }
.caption-note { color: #64748b; font-size: 0.88rem; margin-top: 0.3rem; margin-bottom: 1.5rem; }
.stButton > button { border-radius: 14px; font-weight: 800; min-height: 44px; }
div[data-testid="stDateInput"] label, div[data-testid="stSelectbox"] label { font-weight: 700; color: #334155; }
</style>
""", unsafe_allow_html=True)

# =========================
# 헤더 & 필터
# =========================
st.markdown('<div class="main-title">PPE 안전관리 대시보드</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">날짜와 현장 조건에 맞는 실시간 안전 현황을 확인하세요</div>', unsafe_allow_html=True)

fc1, fc2, fc3 = st.columns([1.2, 1.1, 0.55])
with fc1: target_date = st.date_input("기준일", value=date.today())
with fc2: site = st.selectbox("현장", ["전체 현장", "현장1", "현장2", "현장3"])
with fc3:
    st.write(""); st.write("")
    st.button("새로고침", use_container_width=True)

selected_date = str(target_date)
dashboard_data = fetch_dashboard_data(selected_date, site)
if dashboard_data is None: st.stop()

kpi = dashboard_data.get("kpi", {})
charts = dashboard_data.get("charts", {})
safety_points = dashboard_data.get("safety_points", [])

compliance_rate = float(kpi.get("compliance_rate", 0) or 0)
compliance_rate_text = kpi.get("compliance_rate_text", f"{round(compliance_rate, 2)}%")
weakest_zone_name = safe_text(kpi.get("weakest_zone_name"))
weakest_zone_score = round(float(kpi.get("weakest_zone_score", 0) or 0), 2)
most_missing_ppe_name = safe_text(kpi.get("most_missing_ppe_name"))
most_missing_ppe_count = int(kpi.get("most_missing_ppe_count", 0) or 0)
priority_task_text = safe_text(kpi.get("priority_task_text"))

# 💡 [핵심 스마트 처리 1] 시간대 3개 무조건 고정
base_time = pd.DataFrame({"time_slot": ["오전", "점심직후", "오후"]})
hourly_df = pd.DataFrame(charts.get("hourly_violations", []))
if not hourly_df.empty:
    hourly_df = pd.merge(base_time, hourly_df, on="time_slot", how="left").fillna(0)
else:
    hourly_df = base_time.copy()
    hourly_df["count"] = 0

# 💡 [핵심 스마트 처리 2] 구역 4개 무조건 고정 & 데이터 없으면 0% 0%로 세팅!
base_zones = pd.DataFrame({"zone": ["고소작업구역", "절단작업구역", "자재운반구역", "설비점검구역"]})
zone_data = pd.DataFrame(charts.get("zone_risk_scores", []))

if not zone_data.empty:
    zone_data = zone_data.rename(columns={"risk_score": "risk"})
    zone_data = pd.merge(base_zones, zone_data, on="zone", how="left")
    # 데이터가 없던(NaN) 구역은 100%가 아니라 0%로 처리
    zone_data["compliance"] = zone_data["risk"].apply(lambda x: 100.0 - x if pd.notna(x) else 0.0)
    zone_data["risk"] = zone_data["risk"].fillna(0.0)
else:
    zone_data = base_zones.copy()
    zone_data["risk"], zone_data["compliance"] = 0.0, 0.0

if not safety_points: safety_points = ["오늘은 위반 데이터가 없어 전반적으로 양호합니다."]
ai_summary_items = build_ai_summary(selected_date, weakest_zone_name, weakest_zone_score, most_missing_ppe_name, priority_task_text)

# =========================
# KPI 카드
# =========================
c1, c2, c3, c4 = st.columns(4)
with c1: render_metric_card("위험노출 대비 PPE 준수율", compliance_rate_text, "실시간 집계", "#3b82f6", "#eff6ff", "#1d4ed8", "#eff6ff", "#3b82f6", "🛡️")
with c2: render_metric_card("오늘 가장 취약한 구역", weakest_zone_name, f"위험도 {weakest_zone_score}%", "#ef4444", "#fef2f2", "#b91c1c", "#fef2f2", "#ef4444", "⚠️")
with c3: render_metric_card("반복 누락 PPE", most_missing_ppe_name, f"{most_missing_ppe_count}회 반복", "#f97316", "#fff7ed", "#c2410c", "#fff7ed", "#f97316", "🦺")
with c4: render_metric_card("우선 개입 필요 작업", priority_task_text, "우선 확인", "#a855f7", "#faf5ff", "#7e22ce", "#faf5ff", "#9333ea", "⏱️")
st.markdown(f'<div class="caption-note">기준일: {selected_date} · 현장: {site}</div>', unsafe_allow_html=True)

# =========================
# 1행 (시간대별 이탈 건수)
# =========================
row1_col1, row1_col2 = st.columns([1.7, 1.3])
with row1_col1:
    st.markdown('<div class="section-card"><div class="section-title">시간대별 PPE 이탈 건수</div><div class="section-sub">시간대별 위반 분포를 확인합니다</div>', unsafe_allow_html=True)
    fig_time = go.Figure()
    fig_time.add_trace(go.Bar(x=hourly_df["time_slot"].tolist(), y=hourly_df["count"].tolist(), orientation="v", marker=dict(color=["#60a5fa", "#3b82f6", "#1e3a8a"]), width=0.45, hovertemplate="시간대: %{x}<br>건수: %{y}건<extra></extra>"))
    y_max = max(4, int(hourly_df["count"].max()) + 2)
    fig_time.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white", paper_bgcolor="white", showlegend=False, xaxis=dict(showgrid=False, tickfont=dict(size=12, color="#334155")), yaxis=dict(showgrid=True, gridcolor="#f1f5f9", zeroline=False, tickfont=dict(size=11, color="#94a3b8"), range=[0, y_max], dtick=2))
    try: fig_time.update_layout(barcornerradius=12)
    except Exception: pass
    st.plotly_chart(fig_time, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with row1_col2:
    st.markdown('<div class="section-card"><div class="section-title">오늘의 안전개입 포인트</div><div class="section-sub">현장에서 즉시 개입해야 할 요소입니다</div>', unsafe_allow_html=True)
    for point in safety_points[:3]: st.markdown(f'<div class="insight-box" style="background:#fff7ed; border-color:#fed7aa; color:#9a3412;">⚠️ {point}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 2행 (작업구역별 위험노출 준수율 - 기획서처럼 수직형 100% 그룹 차트!)
# =========================
row2_col1, row2_col2 = st.columns([1.7, 1.3])
with row2_col1:
    st.markdown('<div class="section-card"><div class="section-title">특정별 위험노출 준수율</div><div class="section-sub">구역별 준수율과 위험도를 100% 기준으로 비교합니다</div>', unsafe_allow_html=True)
    fig_zone = go.Figure()
    
    # 💡 세로 방향(수직)으로 변경 완료!
    fig_zone.add_trace(go.Bar(x=zone_data["zone"].tolist(), y=zone_data["compliance"].tolist(), name="준수율 %", marker=dict(color="#22c55e"), width=0.35, hovertemplate="구역: %{x}<br>준수율: %{y}%<extra></extra>"))
    fig_zone.add_trace(go.Bar(x=zone_data["zone"].tolist(), y=zone_data["risk"].tolist(), name="위험도 %", marker=dict(color="#ef4444"), width=0.35, hovertemplate="구역: %{x}<br>위험도: %{y}%<extra></extra>"))

    fig_zone.update_layout(
        barmode="group", height=360, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white", paper_bgcolor="white", 
        showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        bargap=0.35, bargroupgap=0.05,
        yaxis=dict(range=[0, 100], dtick=25, gridcolor="#f1f5f9", zeroline=False, tickfont=dict(size=11, color="#94a3b8"), ticksuffix="%"),
        xaxis=dict(showgrid=False, tickfont=dict(size=12, color="#334155"))
    )
    
    try: fig_zone.update_layout(barcornerradius=12)
    except Exception: pass
    
    st.plotly_chart(fig_zone, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with row2_col2:
    st.markdown('<div class="section-card" style="height: 485px;">', unsafe_allow_html=True)
    st.markdown('<div class="ai-title-row"><div class="ai-emoji">🧠</div><div class="ai-title">AI 안전 분석</div></div><div class="ai-sub">실시간 패턴 분석 기반 요약</div><ul class="ai-list">', unsafe_allow_html=True)
    for item in ai_summary_items: st.markdown(f"<li>{item}</li>", unsafe_allow_html=True)
    st.markdown('</ul><div class="ai-updated">마지막 업데이트: 방금 전</div></div>', unsafe_allow_html=True)