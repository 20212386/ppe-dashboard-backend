import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import date

st.set_page_config(page_title="PPE 안전관리 대시보드", page_icon="🦺", layout="wide")

API_BASE_URL = "https://ppe-dashboard-backend.onrender.com"

# =========================
# API & 유틸
# =========================
def fetch_dashboard_data(target_date: str, site: str):
    try:
        params = {"target_date": target_date}
        if site and site != "전체 현장": params["site"] = site
        res = requests.get(f"{API_BASE_URL}/dashboard/today", params=params, timeout=60)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"대시보드 데이터 조회 실패: {e}")
        return None

def safe_text(value, default="-"):
    if value is None: return default
    text = str(value).strip()
    return default if text == "" or text.lower() in ["none", "nan", "null"] else text

def build_ai_summary(report_date, weakest_zone_name, weakest_zone_score, most_missing_ppe_name, priority_task_text):
    w_name, p_name, t_text = safe_text(weakest_zone_name), safe_text(most_missing_ppe_name), safe_text(priority_task_text)
    items = [f"<b>[AI 종합 진단]</b> {report_date} 기준, 현장 센서 및 비전 데이터를 종합 분석한 결과입니다."]
    if w_name != "-": items.append(f"<b>[취약 구역]</b> <b>{w_name}</b>의 위험 노출(위반율 <b>{weakest_zone_score}%</b>)이 가장 높게 측정되었습니다. 해당 구역 재점검을 권장합니다.")
    if p_name != "-": items.append(f"<b>[행동 패턴]</b> <b>{p_name}</b> 미착용 사례가 반복 감지되었습니다. 보호구 상태 결함 여부를 확인하시기 바랍니다.")
    if t_text != "-": items.append(f"<b>[고위험 작업]</b> <b>{t_text}</b> 투입 인원의 위반이 두드러집니다. TBM을 통한 집중 교육이 시급합니다.")
    items.append("<b>[예측 조치]</b> 취약 시간대 순찰 빈도를 상향하고 맞춤형 교육을 진행할 경우 위험도를 유의미하게 낮출 수 있습니다.")
    return items

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
# 스타일 
# =========================
st.markdown("""
<style>
.block-container { padding-top: 1.7rem; padding-bottom: 2rem; max-width: 1500px; }
.main-title { font-size: 2.15rem; font-weight: 800; color: #0f172a; margin-bottom: 0.25rem; }
.main-subtitle { font-size: 0.98rem; color: #64748b; margin-bottom: 1.1rem; }
.section-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 22px; padding: 22px 22px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05); margin-bottom: 1rem; }
.section-title { font-size: 1.16rem; font-weight: 800; color: #0f172a; margin-bottom: 0.35rem; }
.section-sub { color: #64748b; font-size: 0.88rem; margin-bottom: 1.2rem; }
.metric-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 20px; padding: 18px 20px; min-height: 158px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05); }
.metric-top { display: flex; justify-content: space-between; gap: 10px; }
.metric-left { flex: 1; }
.metric-title { color: #64748b; font-size: 0.92rem; font-weight: 700; margin-bottom: 10px; }
.metric-value { color: #0f172a; font-size: 1.72rem; font-weight: 800; margin-bottom: 10px; }
.metric-badge { display: inline-block; padding: 7px 11px; border-radius: 999px; font-size: 0.76rem; font-weight: 800; }
.metric-icon { width: 52px; height: 52px; border-radius: 15px; display: flex; align-items: center; justify-content: center; font-size: 1.28rem; }
.insight-box { border-radius: 16px; padding: 16px 18px; margin-top: 0.5rem; font-size: 0.92rem; font-weight: 700; border: 1px solid; line-height: 1.6; }
.ai-title-row { display: flex; align-items: center; gap: 10px; margin-bottom: 0.25rem; }
.ai-emoji { font-size: 1.4rem; }
.ai-title { font-size: 1.1rem; font-weight: 800; color: #0f172a; }
.ai-sub { color: #64748b; font-size: 0.88rem; margin-bottom: 1rem; }
.ai-list { margin: 0; padding-left: 1.2rem; }
.ai-list li { margin-bottom: 0.9rem; color: #334155; line-height: 1.6; font-size: 0.95rem; }
.ai-updated { color: #94a3b8; font-size: 0.84rem; font-weight: 600; margin-top: 1.5rem; }
.caption-note { color: #64748b; font-size: 0.88rem; margin-top: 0.3rem; margin-bottom: 1.5rem; }
.stButton > button { border-radius: 14px; font-weight: 800; min-height: 44px; }
</style>
""", unsafe_allow_html=True)

# =========================
# 필터 & 데이터
# =========================
st.markdown('<div class="main-title">PPE 안전관리 대시보드</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">날짜와 현장 조건에 맞는 실시간 안전 현황을 확인하세요</div>', unsafe_allow_html=True)

fc1, fc2, fc3 = st.columns([1.2, 1.1, 0.55])
with fc1: target_date = st.date_input("기준일", value=date.today())
with fc2: site = st.selectbox("현장", ["전체 현장", "현장1", "현장2", "현장3"])
with fc3:
    st.write(""); st.write("")
    st.button("새로고침", use_container_width=True)

dashboard_data = fetch_dashboard_data(str(target_date), site)
if dashboard_data is None: st.stop()

kpi, charts, safety_points = dashboard_data.get("kpi", {}), dashboard_data.get("charts", {}), dashboard_data.get("safety_points", [])

compliance_rate = float(kpi.get("compliance_rate", 0) or 0)
weakest_zone_name = safe_text(kpi.get("weakest_zone_name"))
weakest_zone_score = round(float(kpi.get("weakest_zone_score", 0) or 0), 2)
most_missing_ppe_name = safe_text(kpi.get("most_missing_ppe_name"))
most_missing_ppe_count = int(kpi.get("most_missing_ppe_count", 0) or 0)
priority_task_text = safe_text(kpi.get("priority_task_text"))

base_time = pd.DataFrame({"time_slot": ["오전", "점심직후", "오후"]})
hourly_df = pd.merge(base_time, pd.DataFrame(charts.get("hourly_violations", [])), on="time_slot", how="left").fillna(0) if charts.get("hourly_violations") else base_time.assign(count=0)

base_zones = pd.DataFrame({"zone": ["고소작업구역", "절단작업구역", "자재운반구역", "설비점검구역"]})
zone_data = pd.DataFrame(charts.get("zone_risk_scores", []))
if not zone_data.empty:
    zone_data = pd.merge(base_zones, zone_data.rename(columns={"risk_score": "risk"}), on="zone", how="left")
    zone_data["compliance"] = zone_data["risk"].apply(lambda x: 100.0 - x if pd.notna(x) else 0.0)
    zone_data["risk"] = zone_data["risk"].fillna(0.0)
else:
    zone_data = base_zones.assign(risk=0.0, compliance=0.0)

ai_summary_items = build_ai_summary(str(target_date), weakest_zone_name, weakest_zone_score, most_missing_ppe_name, priority_task_text)

# =========================
# KPI 카드
# =========================
c1, c2, c3, c4 = st.columns(4)
with c1: render_metric_card("위험노출 대비 PPE 준수율", kpi.get("compliance_rate_text", f"{round(compliance_rate, 2)}%"), "실시간 집계", "#3b82f6", "#eff6ff", "#1d4ed8", "#eff6ff", "#3b82f6", "🛡️")
with c2: render_metric_card("오늘 가장 취약한 구역", weakest_zone_name, f"위험도 {weakest_zone_score}%", "#ef4444", "#fef2f2", "#b91c1c", "#fef2f2", "#ef4444", "⚠️")
with c3: render_metric_card("반복 누락 PPE", most_missing_ppe_name, f"{most_missing_ppe_count}회 반복", "#f97316", "#fff7ed", "#c2410c", "#fff7ed", "#f97316", "🦺")
with c4: render_metric_card("우선 개입 필요 작업", priority_task_text, "우선 확인", "#a855f7", "#faf5ff", "#7e22ce", "#faf5ff", "#9333ea", "⏱️")
st.markdown(f'<div class="caption-note">기준일: {target_date} · 현장: {site}</div>', unsafe_allow_html=True)

# =========================
# 1행 (시간대별 이탈 건수) - 5페이지 감성!
# =========================
row1_col1, row1_col2 = st.columns([1.7, 1.3])
with row1_col1:
    st.markdown('<div class="section-card"><div class="section-title">시간대별 PPE 이탈 건수</div><div class="section-sub">시간대별 위반 분포를 확인합니다</div>', unsafe_allow_html=True)
    fig_time = go.Figure()
    
    # 💡 5페이지 스타일: 각진 모서리, 반투명 컬러, 외곽선, 텍스트 표시
    fig_time.add_trace(go.Bar(
        x=hourly_df["time_slot"].tolist(), 
        y=hourly_df["count"].tolist(), 
        text=hourly_df["count"].tolist(), # 막대 위에 숫자 띄우기
        textposition="outside",
        marker=dict(color="rgba(59, 130, 246, 0.65)", line=dict(color="#2563eb", width=1.5)), 
        width=0.4
    ))
    
    # 글자가 잘리지 않게 Y축 상단을 30% 더 높게 여유줌
    y_max = max(4, int(hourly_df["count"].max()) * 1.3)
    
    fig_time.update_layout(
        height=340, margin=dict(l=10, r=10, t=20, b=10), plot_bgcolor="white", paper_bgcolor="white", 
        showlegend=False, xaxis=dict(showgrid=False, tickfont=dict(size=12, color="#334155")), 
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9", zeroline=False, tickfont=dict(size=11, color="#94a3b8"), range=[0, y_max])
    )
    # 💡 둥근 모서리 코드 영원히 삭제!!
    st.plotly_chart(fig_time, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with row1_col2:
    st.markdown('<div class="section-card"><div class="section-title">오늘의 안전개입 포인트</div><div class="section-sub">현장에서 즉시 개입해야 할 요소입니다</div>', unsafe_allow_html=True)
    for point in safety_points[:3]: st.markdown(f'<div class="insight-box" style="background:#fff7ed; border-color:#fed7aa; color:#9a3412;">⚠️ {point}</div>', unsafe_allow_html=True)
    if not safety_points: st.markdown(f'<div class="insight-box" style="background:#f0fdf4; border-color:#86efac; color:#166534;">✅ 오늘은 위반 데이터가 없어 전반적으로 양호합니다.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 2행 (작업구역별 위험노출 준수율) - 5페이지 감성!
# =========================
row2_col1, row2_col2 = st.columns([1.7, 1.3])
with row2_col1:
    st.markdown('<div class="section-card"><div class="section-title">특정별 위험노출 준수율</div><div class="section-sub">구역별 준수율과 위험도를 100% 기준으로 비교합니다</div>', unsafe_allow_html=True)
    fig_zone = go.Figure()
    
    # 💡 5페이지 스타일: 초록색 반투명 + 외곽선 + 텍스트 표시
    fig_zone.add_trace(go.Bar(
        x=zone_data["zone"].tolist(), 
        y=zone_data["compliance"].tolist(), 
        name="준수율 %", 
        text=zone_data["compliance"].round(1).tolist(),
        texttemplate="%{text}%",
        textposition="outside",
        marker=dict(color="rgba(34, 197, 94, 0.65)", line=dict(color="#16a34a", width=1.5)), 
        width=0.35
    ))
    # 💡 5페이지 스타일: 빨간색 반투명 + 외곽선 + 텍스트 표시
    fig_zone.add_trace(go.Bar(
        x=zone_data["zone"].tolist(), 
        y=zone_data["risk"].tolist(), 
        name="위험도 %", 
        text=zone_data["risk"].round(1).tolist(),
        texttemplate="%{text}%",
        textposition="outside",
        marker=dict(color="rgba(239, 68, 68, 0.65)", line=dict(color="#dc2626", width=1.5)), 
        width=0.35
    ))

    fig_zone.update_layout(
        barmode="group", height=360, margin=dict(l=10, r=10, t=20, b=10), plot_bgcolor="white", paper_bgcolor="white", 
        showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        bargap=0.4, bargroupgap=0.05, # 막대끼리 겹치지 않게 간격 세밀 조정
        # 글자 안 잘리게 Y축을 115%까지 늘림
        yaxis=dict(range=[0, 115], showgrid=True, gridcolor="#f1f5f9", zeroline=False, tickfont=dict(size=11, color="#94a3b8"), ticksuffix="%"),
        xaxis=dict(showgrid=False, tickfont=dict(size=12, color="#334155"))
    )
    # 💡 둥근 모서리 코드 영원히 삭제!!
    st.plotly_chart(fig_zone, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with row2_col2:
    ai_html = f"""
    <div class="section-card">
        <div class="ai-title-row">
            <div class="ai-emoji">🧠</div>
            <div class="ai-title">AI 안전 분석 요약</div>
        </div>
        <div class="ai-sub">실시간 비전 데이터 및 센서 기반 패턴 분석 결과</div>
        <ul class="ai-list">
    """
    for item in ai_summary_items: ai_html += f"<li>{item}</li>"
    ai_html += """
        </ul>
        <div class="ai-updated">마지막 업데이트: 실시간 알고리즘 동기화 완료</div>
    </div>
    """
    st.markdown(ai_html, unsafe_allow_html=True)