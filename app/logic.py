import pandas as pd
from pathlib import Path
from datetime import date, datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILE_PATH = DATA_DIR / "input_logs.csv"

INPUT_REQUIRED_COLUMNS = [
    "date",
    "time_slot",
    "site",
    "zone",
    "task_type",
    "missed_ppe",
    "is_violated",
    "team",
    "note",
]


# =========================
# 공통 / 페이지 1
# =========================
def load_logs(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df


def calculate_compliance_rate(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0

    compliant_count = (df["is_violated"] == 0).sum()
    total_count = len(df)

    return round((compliant_count / total_count) * 100, 2)


def get_weakest_zone(df: pd.DataFrame) -> dict:
    zone_risk_scores = get_zone_risk_scores(df)

    if not zone_risk_scores:
        return {"zone": None, "count": 0, "risk_score": 0.0}

    top_zone = zone_risk_scores[0]

    return {
        "zone": top_zone["zone"],
        "count": float(top_zone["risk_score"]),  # <- 프론트엔드가 읽을 수 있게 count에도 비율을 담아줍니다.
        "risk_score": float(top_zone["risk_score"])
    }


def get_most_missing_ppe(df: pd.DataFrame) -> dict:
    violated_df = df[df["is_violated"] == 1]

    if violated_df.empty:
        return {"missed_ppe": None, "count": 0}

    ppe_counts = violated_df["missed_ppe"].value_counts()
    most_missing = ppe_counts.idxmax()
    count = int(ppe_counts.max())

    return {"missed_ppe": most_missing, "count": count}


def get_priority_task(df: pd.DataFrame) -> dict:
    violated_df = df[df["is_violated"] == 1]

    if violated_df.empty:
        return {"time_slot": None, "zone": None, "text": None, "count": 0}

    combo_counts = (
        violated_df.groupby(["time_slot", "zone"])
        .size()
        .sort_values(ascending=False)
    )

    time_slot, zone = combo_counts.index[0]
    count = int(combo_counts.iloc[0])

    return {
        "time_slot": time_slot,
        "zone": zone,
        "text": f"{time_slot} {zone}",
        "count": count
    }


def get_today_date_str() -> str:
    return str(date.today())


def filter_by_date(df: pd.DataFrame, target_date: str) -> pd.DataFrame:
    return df[df["date"] == target_date].copy()


def get_hourly_violations(df: pd.DataFrame) -> list[dict]:
    violated_df = df[df["is_violated"] == 1]

    order = ["오전", "점심직후", "오후"]
    counts = violated_df["time_slot"].value_counts().to_dict()

    return [
        {"time_slot": slot, "count": int(counts.get(slot, 0))}
        for slot in order
    ]


def get_zone_risk_scores(df: pd.DataFrame) -> list[dict]:
    if df.empty or "zone" not in df.columns or "is_violated" not in df.columns:
        return []

    work_df = df.copy()
    work_df["zone"] = work_df["zone"].astype(str).str.strip()

    results = []

    for zone in work_df["zone"].dropna().unique():
        zone_df = work_df[work_df["zone"] == zone]
        zone_total = len(zone_df)

        if zone_total == 0:
            risk_score = 0.0
        else:
            violated_count = int((zone_df["is_violated"] == 1).sum())
            risk_score = round((violated_count / zone_total) * 100, 2)

        risk_score = max(0.0, min(100.0, risk_score))

        results.append({
            "zone": zone,
            "risk_score": risk_score
        })

    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return results


def get_safety_point(df: pd.DataFrame) -> str:
    violated_df = df[df["is_violated"] == 1]

    if violated_df.empty:
        return "오늘은 위반 데이터가 없어 전반적으로 양호합니다."

    combo_counts = (
        violated_df.groupby(["time_slot", "zone", "missed_ppe"])
        .size()
        .sort_values(ascending=False)
    )

    time_slot, zone, missed_ppe = combo_counts.index[0]
    return f"{time_slot} {zone}에서 {missed_ppe} 미착용이 증가했습니다."


def get_safety_points(df: pd.DataFrame) -> list[str]:
    violated_df = df[df["is_violated"] == 1]

    if violated_df.empty:
        return ["오늘은 위반 데이터가 없어 전반적으로 양호합니다."]

    points = []
    combo_counts = (
        violated_df.groupby(["time_slot", "zone", "missed_ppe"])
        .size()
        .sort_values(ascending=False)
    )

    top_items = combo_counts.head(3)

    for (time_slot, zone, missed_ppe), _count in top_items.items():
        points.append(f"{time_slot} {zone}에서 {missed_ppe} 미착용이 증가했습니다.")

    return points


# =========================
# 페이지 2 입력/업로드 공통
# =========================
def normalize_uploaded_df(df: pd.DataFrame) -> pd.DataFrame:
    return normalize_input_df(df)


def validate_required_columns(df: pd.DataFrame) -> dict:
    return validate_input_columns(df)


def calculate_data_summary(df: pd.DataFrame, today_str: str | None = None) -> dict:
    return calculate_input_summary(df, today_str or get_today_date_str())


def calculate_quality_metrics(df: pd.DataFrame) -> dict:
    return calculate_input_quality(df)

def get_input_preview(df: pd.DataFrame, n: int = 10) -> list[dict]:
    if df.empty:
        return []
    return df.tail(n).iloc[::-1].fillna("").to_dict(orient="records")

def get_recent_preview(df: pd.DataFrame, n: int = 10) -> list[dict]:
    return get_input_preview(df, n)


def load_input_logs() -> pd.DataFrame:
    if not INPUT_FILE_PATH.exists():
        return pd.DataFrame(columns=INPUT_REQUIRED_COLUMNS)

    df = pd.read_csv(INPUT_FILE_PATH)
    df = normalize_input_df(df)

    validation = validate_input_columns(df)
    if not validation["is_valid"]:
        return pd.DataFrame(columns=INPUT_REQUIRED_COLUMNS)

    return df


def normalize_input_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    rename_map = {
        "Date": "date",
        "date": "date",

        "Time_Slot": "time_slot",
        "time_slot": "time_slot",
        "TimeSlot": "time_slot",

        "Site": "site",
        "site": "site",

        "Zone": "zone",
        "zone": "zone",

        "Task_Type": "task_type",
        "TaskType": "task_type",
        "task_type": "task_type",

        "Missed_PPE": "missed_ppe",
        "MissedPPE": "missed_ppe",
        "missed_ppe": "missed_ppe",
        "PPE_Type": "missed_ppe",
        "PPEType": "missed_ppe",

        "Is_Violated": "is_violated",
        "IsViolated": "is_violated",
        "is_violated": "is_violated",
        "Risk_Exposure": "is_violated",
        "RiskExposure": "is_violated",

        "Team": "team",
        "team": "team",

        "Note": "note",
        "note": "note",
    }

    df = df.rename(columns=rename_map)

    for col in INPUT_REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df = df[INPUT_REQUIRED_COLUMNS]

    for col in ["date", "time_slot", "site", "zone", "task_type", "missed_ppe", "team", "note"]:
        df[col] = df[col].fillna("").astype(str).str.strip()

    if "is_violated" in df.columns:
        df["is_violated"] = (
            df["is_violated"]
            .fillna(0)
            .astype(str)
            .str.strip()
            .replace({
                "O": "1",
                "X": "0",
                "o": "1",
                "x": "0",
                "True": "1",
                "False": "0",
                "true": "1",
                "false": "0",
            })
        )
        df["is_violated"] = pd.to_numeric(df["is_violated"], errors="coerce").fillna(0).astype(int)

    if not df.empty:
        parsed = pd.to_datetime(df["date"], errors="coerce")
        df["date"] = parsed.dt.strftime("%Y-%m-%d").fillna(df["date"])

    return df


def validate_input_columns(df: pd.DataFrame) -> dict:
    missing_columns = [col for col in INPUT_REQUIRED_COLUMNS if col not in df.columns]

    return {
        "is_valid": len(missing_columns) == 0,
        "missing_columns": missing_columns
    }


def calculate_input_summary(df: pd.DataFrame, today_str: str) -> dict:
    if df.empty:
        return {
            "total_rows": 0,
            "today_rows": 0,
            "risk_rows": 0,
            "not_worn_rows": 0,
            "normal_rows": 0,
        }

    today_rows = df[df["date"] == today_str]
    risk_rows = df[df["risk_exposure"] == "O"]
    not_worn_rows = df[df["worn"] == "X"]
    normal_rows = df[df["worn"] == "O"]

    return {
        "total_rows": int(len(df)),
        "today_rows": int(len(today_rows)),
        "risk_rows": int(len(risk_rows)),
        "not_worn_rows": int(len(not_worn_rows)),
        "normal_rows": int(len(normal_rows)),
    }


def calculate_input_quality(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "completeness_rate": 0,
            "validity_rate": 0,
            "duplicate_count": 0,
            "error_count": 0,
        }

    required_without_note = [
        "date", "time", "worker_id", "team", "zone",
        "task_type", "ppe_type", "worn", "risk_exposure"
    ]

    total_cells = len(df) * len(required_without_note)
    filled_cells = df[required_without_note].replace("", pd.NA).notna().sum().sum()
    completeness_rate = round((filled_cells / total_cells) * 100, 2) if total_cells > 0 else 0

    valid_worn = df["worn"].isin(["O", "X"]).sum()
    valid_risk = df["risk_exposure"].isin(["O", "X"]).sum()
    validity_rate = round(((valid_worn + valid_risk) / (2 * len(df))) * 100, 2) if len(df) > 0 else 0

    duplicate_count = int(df.duplicated().sum())

    error_count = int(
        len(df[
            (~df["worn"].isin(["O", "X"])) |
            (~df["risk_exposure"].isin(["O", "X"]))
        ])
    )
def append_manual_entry(entry: dict) -> dict:
    try:
        if os.path.exists("data/input_logs.csv"):
            df = pd.read_csv("data/input_logs.csv")
        else:
            df = pd.DataFrame(columns=INPUT_REQUIRED_COLUMNS)
            
        new_row = pd.DataFrame([entry])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv("data/input_logs.csv", index=False)
        return {"status": "success", "message": "수동 입력 데이터가 저장되었습니다."}
    except Exception as e:
        return {"status": "error", "message": f"저장 실패: {str(e)}"}
# =========================
# 페이지 3 분석 상세
# =========================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests

st.set_page_config(page_title="위험패턴 분석", page_icon="📊", layout="wide")

API_BASE = "https://ppe-dashboard-backend.onrender.com"

# =========================
# 1. 스타일
# =========================
st.markdown("""
<style>
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1480px; }
.main-title { font-size: 2.15rem; font-weight: 800; color: #0f172a; margin-bottom: 0.25rem; }
.sub-title { color: #64748b; font-size: 1rem; margin-bottom: 1.1rem; }
.filter-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 24px; padding: 22px; box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05); margin-bottom: 1rem; }
.section-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 22px; padding: 20px; box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05); margin-bottom: 1rem; }
.section-title { font-size: 1.12rem; font-weight: 800; color: #0f172a; margin-bottom: 0.4rem; }
.section-sub { color: #64748b; font-size: 0.86rem; margin-bottom: 0.95rem; }

.metric-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 20px; padding: 18px 20px; height: 145px; box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05); }
.metric-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
.metric-label { color: #64748b; font-size: 0.9rem; margin-bottom: 10px; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.metric-value { color: #0f172a; font-size: 1.3rem; font-weight: 800; line-height: 1.2; margin-bottom: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.metric-badge { display: inline-block; padding: 6px 11px; border-radius: 999px; font-size: 0.75rem; font-weight: 800; }
.metric-icon { width: 45px; height: 45px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; flex-shrink: 0; }

.insight-box { border-radius: 14px; padding: 11px 13px; margin-top: 0.85rem; font-size: 0.87rem; border: 1px solid; }
.recommend-box { background: linear-gradient(135deg, #eef4ff 0%, #dbeafe 100%); border: 1px solid #bfdbfe; border-radius: 18px; padding: 18px; color: #1e3a8a; font-size: 0.96rem; font-weight: 700; }
.analysis-guide { background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 18px; padding: 18px; color: #475569; font-size: 0.92rem; text-align: center; }
.small-stat { color: #64748b; font-size: 0.9rem; margin: 0.2rem 0 0.9rem 0; }
.stButton > button { border-radius: 14px; font-weight: 800; min-height: 46px; }
</style>
""", unsafe_allow_html=True)

# =========================
# 2. 렌더링 함수들
# =========================
def render_metric_card(title, value, badge_text, accent, badge_bg, badge_fg, icon_bg, icon_fg, icon_symbol):
    st.markdown(f"""
        <div class="metric-card" style="border-left:6px solid {accent};">
            <div class="metric-top">
                <div style="width: 75%; overflow: hidden;">
                    <div class="metric-label" title="{title}">{title}</div>
                    <div class="metric-value" title="{value}">{value}</div>
                    <span class="metric-badge" style="background:{badge_bg}; color:{badge_fg};">{badge_text}</span>
                </div>
                <div class="metric-icon" style="background:{icon_bg}; color:{icon_fg};">{icon_symbol}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_empty_chart_message(message: str):
    st.markdown(f'<div class="analysis-guide">{message}</div>', unsafe_allow_html=True)

def fetch_analysis_data(params: dict):
    try:
        clean_params = {k: v for k, v in params.items() if v is not None and v != ""}
        res = requests.get(f"{API_BASE}/analysis/detail", params=clean_params, timeout=60)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"분석 데이터 조회 실패: {e}")
        return None

def _safe_counts_df(df_data, all_categories=None) -> pd.DataFrame:
    df = pd.DataFrame(df_data)
    if df.empty or "label" not in df.columns or "count" not in df.columns:
        df = pd.DataFrame(columns=["label", "count", "compliance_rate", "risk_rate"])
    else:
        df["label"] = df["label"].fillna("").astype(str)
        df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0).astype(int)

    if all_categories:
        cat_df = pd.DataFrame({"label": all_categories})
        df = pd.merge(cat_df, df, on="label", how="left").fillna(0)
        if "count" in df.columns: df["count"] = df["count"].astype(int)
        
    return df[df["label"] != ""].reset_index(drop=True)

def create_beautiful_chart(df, color, line_color, is_horizontal=False):
    x_data = df["label"].tolist()
    y_data = df["count"].tolist()
    
    max_val = max(y_data) if y_data else 0
    tick_step = 1 if max_val <= 10 else None
    y_max = max(max_val + (max_val*0.2), 4) 
    bar_width = 0.45

    if is_horizontal:
        fig = go.Figure(go.Bar(x=y_data, y=x_data, orientation="h", width=bar_width, marker=dict(color=color, line=dict(color=line_color, width=1.5))))
        fig.update_xaxes(showgrid=True, gridcolor="#f1f5f9", rangemode="tozero", dtick=tick_step, range=[0, y_max])
        fig.update_yaxes(autorange="reversed", type="category")
    else:
        fig = go.Figure(go.Bar(x=x_data, y=y_data, width=bar_width, marker=dict(color=color, line=dict(color=line_color, width=1.5))))
        fig.update_xaxes(type="category")
        fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9", rangemode="tozero", dtick=tick_step, range=[0, y_max])
        
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10), plot_bgcolor="white", paper_bgcolor="white", showlegend=False)
    return fig

# =========================
# 3. 화면 UI 및 필터
# =========================
if "p3_analysis_data" not in st.session_state:
    st.session_state["p3_analysis_data"] = None

st.markdown('<div class="main-title">위험패턴 분석</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">필터 조건에 맞는 반복 위험 패턴을 분석하고 개입 우선순위를 확인합니다</div>', unsafe_allow_html=True)

st.markdown('<div class="filter-card"><div class="section-title">분석 필터</div><div class="section-sub">현장, 날짜, 작업 조건에 따라 반복 위험 패턴을 좁혀서 볼 수 있습니다</div>', unsafe_allow_html=True)

f1, f2, f3 = st.columns(3)
f4, f5, f6 = st.columns(3)
f7, f8 = st.columns([1, 2])

with f1: start_date = st.text_input("시작 날짜", value="2026-03-01")
with f2: end_date = st.text_input("종료 날짜", value="2026-03-31")
with f3: site = st.selectbox("현장", ["", "현장1", "현장2", "현장3"])
with f4: zone = st.selectbox("작업구역", ["", "고소작업구역", "절단작업구역", "자재운반구역", "설비점검구역"])
with f5: task_type = st.selectbox("작업유형", ["", "고소작업", "절단작업", "자재운반", "설비점검"])
with f6: ppe_type = st.selectbox("PPE 종류", ["", "장갑", "안전모", "랜야드"])
with f7: risk_exposure = st.selectbox("위험노출 여부", ["", "O", "X"])
with f8:
    st.markdown("<div style='margin-top: 28.5px;'></div>", unsafe_allow_html=True)
    run_analysis = st.button("분석 실행", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

params = {
    "start_date": start_date or None, "end_date": end_date or None, "site": site or None,
    "zone": zone or None, "task_type": task_type or None, "ppe_type": ppe_type or None,
    "risk_exposure": (1 if risk_exposure == "O" else 0) if risk_exposure in ["O", "X"] else None,
}

if run_analysis:
    st.session_state["p3_analysis_data"] = fetch_analysis_data(params)

analysis_data = st.session_state["p3_analysis_data"]

if analysis_data:
    count = analysis_data.get("count", 0)
    kpis = analysis_data.get("kpis", {})
    charts = analysis_data.get("charts", {})
    recommend_action = analysis_data.get("recommend_action", "추천 조치가 없습니다.")
else:
    count, kpis, charts, recommend_action = 0, {}, {}, "필터를 설정한 뒤 '분석 실행' 버튼을 눌러주세요."

time_cats = ["오전", "점심직후", "오후"]
ppe_cats = ["안전모", "랜야드", "장갑"]
zone_cats = ["고소작업구역", "절단작업구역", "자재운반구역", "설비점검구역"]
task_cats = ["고소작업", "절단작업", "자재운반", "설비점검"]

time_df = _safe_counts_df(charts.get("time_chart", []), time_cats)
ppe_df = _safe_counts_df(charts.get("ppe_chart", []), ppe_cats)
zone_df = _safe_counts_df(charts.get("zone_chart", []), zone_cats)
task_df = _safe_counts_df(charts.get("task_chart", []), task_cats)

top_time, top_zone, top_task, top_ppe = kpis.get("top_time") or "-", kpis.get("top_zone") or "-", kpis.get("top_task_type") or "-", kpis.get("top_ppe") or "-"

# =========================
# 4. KPI 카드 & 통계
# =========================
c1, c2, c3, c4 = st.columns(4)
with c1: render_metric_card("가장 위험한 시간대", top_time, "위반 집중", "#ef4444", "#fef2f2", "#b91c1c", "#fef2f2", "#ef4444", "⏰")
with c2: render_metric_card("가장 취약한 구역", top_zone, "위험 패턴 상위", "#f97316", "#fff7ed", "#c2410c", "#fff7ed", "#f97316", "📍")
with c3: render_metric_card("반복 위험 작업유형", top_task, "반복 분석", "#eab308", "#fefce8", "#a16207", "#fefce8", "#ca8a04", "📉")
with c4: render_metric_card("가장 많이 누락된 PPE", top_ppe, "누락 상위", "#a855f7", "#faf5ff", "#7e22ce", "#faf5ff", "#9333ea", "⛑")

st.markdown(f'<div class="small-stat">현재 필터 조건에 맞는 데이터 건수: <b>{count}</b></div>', unsafe_allow_html=True)

# =========================
# 5. 차트 렌더링
# =========================
r1c1, r1c2 = st.columns(2)

with r1c1:
    st.markdown('<div class="section-card"><div class="section-title">시간대별 위반 건수</div><div class="section-sub">시간대별 반복 위반 분포를 확인합니다</div>', unsafe_allow_html=True)
    if analysis_data is None: render_empty_chart_message("필터를 설정하고 <b>분석 실행</b>을 누르면 데이터가 표시됩니다.")
    else:
        fig_time = create_beautiful_chart(time_df, "rgba(59, 130, 246, 0.65)", "#2563eb", False)
        st.plotly_chart(fig_time, use_container_width=True, config={"displayModeBar": False})
        st.markdown(f'<div class="insight-box" style="background:#eff6ff; border-color:#bfdbfe; color:#1e3a8a;">💡 패턴 해석: 위반이 집중된 시간대는 <b>{top_time}</b>입니다.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r1c2:
    st.markdown('<div class="section-card"><div class="section-title">PPE별 위반 건수</div><div class="section-sub">누락 빈도가 높은 보호구를 확인합니다</div>', unsafe_allow_html=True)
    if analysis_data is None: render_empty_chart_message("필터를 설정하고 <b>분석 실행</b>을 누르면 데이터가 표시됩니다.")
    else:
        fig_ppe = create_beautiful_chart(ppe_df, "rgba(139, 92, 246, 0.65)", "#7c3aed", False)
        st.plotly_chart(fig_ppe, use_container_width=True, config={"displayModeBar": False})
        st.markdown(f'<div class="insight-box" style="background:#fff7ed; border-color:#fed7aa; color:#9a3412;">💡 패턴 해석: 가장 많이 누락되는 보호구는 <b>{top_ppe}</b>입니다.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

r2c1, r2c2 = st.columns(2)

with r2c1:
    # 💡 [수술 부위] 기획서와 100% 동일한 준수율(초록) / 위험도(빨강) % 비교 차트!
    st.markdown('<div class="section-card"><div class="section-title">특정별 위험노출 준수율</div><div class="section-sub">구역별 준수율과 위험도를 100% 기준으로 비교합니다</div>', unsafe_allow_html=True)
    if analysis_data is None: render_empty_chart_message("필터를 설정하고 <b>분석 실행</b>을 누르면 데이터가 표시됩니다.")
    else:
        fig_zone = go.Figure()
        fig_zone.add_trace(go.Bar(x=zone_df["label"], y=zone_df["compliance_rate"], name="준수율 %", marker_color="#22c55e", width=0.35))
        fig_zone.add_trace(go.Bar(x=zone_df["label"], y=zone_df["risk_rate"], name="위험도 %", marker_color="#ef4444", width=0.35))
        
        fig_zone.update_layout(
            barmode='group', height=340, margin=dict(l=10, r=10, t=20, b=10), plot_bgcolor="white", paper_bgcolor="white", 
            showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5), # 범례(Legend)를 기획서처럼 바닥으로!
            yaxis=dict(range=[0, 100], dtick=25, showgrid=True, gridcolor="#f1f5f9") # y축은 % 니까 무조건 0~100 고정!
        )
        st.plotly_chart(fig_zone, use_container_width=True, config={"displayModeBar": False})
        st.markdown(f'<div class="insight-box" style="background:#fff7ed; border-color:#fed7aa; color:#9a3412;">💡 패턴 해석: 위험도가 가장 높은 취약 구역은 <b>{top_zone}</b>입니다.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with r2c2:
    st.markdown('<div class="section-card"><div class="section-title">작업유형별 반복 횟수</div><div class="section-sub">반복 개입 우선순위가 높은 작업유형을 확인합니다</div>', unsafe_allow_html=True)
    if analysis_data is None: render_empty_chart_message("필터를 설정하고 <b>분석 실행</b>을 누르면 데이터가 표시됩니다.")
    else:
        fig_task = create_beautiful_chart(task_df, "rgba(168, 85, 247, 0.65)", "#9333ea", True)
        st.plotly_chart(fig_task, use_container_width=True, config={"displayModeBar": False})
        st.markdown(f'<div class="insight-box" style="background:#faf5ff; border-color:#e9d5ff; color:#6b21a8;">💡 패턴 해석: 반복 개입 우선 작업은 <b>{top_task}</b>입니다.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-card"><div class="section-title">추천 개입 조치</div>', unsafe_allow_html=True)
st.markdown(f'<div class="recommend-box">{recommend_action}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# =========================
# 페이지 4 TBM
# =========================
def get_yesterday_date_str() -> str:
    return str(datetime.today().date() - timedelta(days=1))


def get_tbm_kpis(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "compliance_rate": 0.0,
            "top_zone": None,
            "top_ppe": None,
            "top_time": None,
        }

    total_rows = len(df)
    normal_rows = (df["worn"] == "O").sum()
    compliance_rate = round((normal_rows / total_rows) * 100, 2) if total_rows > 0 else 0.0

    violated_df = df[df["worn"] == "X"]

    if violated_df.empty:
        return {
            "compliance_rate": compliance_rate,
            "top_zone": None,
            "top_ppe": None,
            "top_time": None,
        }

    top_zone = violated_df["zone"].value_counts().idxmax()
    top_ppe = violated_df["ppe_type"].value_counts().idxmax()
    top_time = violated_df["time"].astype(str).str[:2].value_counts().idxmax() + "시"

    return {
        "compliance_rate": compliance_rate,
        "top_zone": top_zone,
        "top_ppe": top_ppe,
        "top_time": top_time,
    }


def get_tbm_stats(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "total_rows": 0,
            "risk_rows": 0,
            "not_worn_rows": 0,
            "normal_rows": 0,
        }

    return {
        "total_rows": int(len(df)),
        "risk_rows": int((df["risk_exposure"] == "O").sum()),
        "not_worn_rows": int((df["worn"] == "X").sum()),
        "normal_rows": int((df["worn"] == "O").sum()),
    }


def get_tbm_checklist(df: pd.DataFrame) -> list[str]:
    violated_df = df[df["worn"] == "X"]

    if violated_df.empty:
        return ["전일 위반 데이터가 없어 기본 PPE 점검만 수행하면 됩니다."]

    checklist = []

    top_zone = violated_df["zone"].value_counts().idxmax()
    top_ppe = violated_df["ppe_type"].value_counts().idxmax()

    checklist.append(f"{top_zone} 작업 전 현장 순찰 및 집중 점검")
    checklist.append(f"{top_ppe} 착용 여부 출입 전 확인")
    checklist.append("작업 시작 전 작업자 대상 PPE 재안내")

    if "고소작업구역" in violated_df["zone"].values:
        checklist.append("고소작업 전 랜야드 체결 상태 재확인")
    if "절단작업구역" in violated_df["zone"].values:
        checklist.append("절단작업 전 장갑·안전모 착용 점검")

    seen = set()
    result = []
    for item in checklist:
        if item not in seen:
            seen.add(item)
            result.append(item)

    return result[:5]


def get_tbm_briefing_text(df: pd.DataFrame, target_date: str) -> str:
    kpis = get_tbm_kpis(df)
    stats = get_tbm_stats(df)

    if stats["total_rows"] == 0:
        return f"{target_date} 전일 데이터가 없어 기본 안전수칙 중심으로 TBM을 진행하면 됩니다."

    if kpis["top_zone"] is None:
        return (
            f"{target_date} 전일 총 {stats['total_rows']}건의 작업 데이터가 기록되었고, "
            f"전반적 준수율은 {kpis['compliance_rate']}%였습니다. "
            "전일 미착용 위반이 없어 오늘도 현재 수준을 유지하는 것이 중요합니다."
        )

    return (
        f"{target_date} 전일 총 {stats['total_rows']}건의 작업 데이터가 기록되었고, "
        f"준수율은 {kpis['compliance_rate']}%였습니다. "
        f"가장 취약한 구역은 {kpis['top_zone']}이며, "
        f"가장 많이 누락된 PPE는 {kpis['top_ppe']}였습니다. "
        f"특히 {kpis['top_time']}대 위반이 집중되어 오늘 TBM에서는 해당 시간대와 구역을 중심으로 점검이 필요합니다."
    )


def get_tbm_focus_message(df: pd.DataFrame) -> str:
    violated_df = df[df["worn"] == "X"]

    if violated_df.empty:
        return "전일 위반이 없어 오늘은 현재의 착용 수준을 유지하는 데 집중하세요."

    top_zone = violated_df["zone"].value_counts().idxmax()
    top_ppe = violated_df["ppe_type"].value_counts().idxmax()

    return f"오늘은 {top_zone}에서 {top_ppe} 착용 여부를 최우선 관리사항으로 두고 작업 전 확인을 강화하세요."


def get_tbm_full_script(df: pd.DataFrame, target_date: str) -> str:
    briefing = get_tbm_briefing_text(df, target_date)
    checklist = get_tbm_checklist(df)
    focus = get_tbm_focus_message(df)

    checklist_text = " / ".join(checklist)

    return (
        f"[전일 브리핑] {briefing}\n\n"
        f"[오늘의 중점 관리사항] {focus}\n\n"
        f"[현장 체크리스트] {checklist_text}"
    )


# =========================
# =========================
# 페이지 5 개선 / 인센티브 (초강력 에러 방어 + 완벽 계산 버전)
# =========================
import pandas as pd

def get_violation_series(df: pd.DataFrame) -> pd.Series:
    """어떤 데이터가 들어와도 위반 여부를 찾아내는 함수"""
    if "is_violated" in df.columns:
        v = pd.to_numeric(df["is_violated"], errors="coerce").fillna(0)
        if v.sum() > 0: return v == 1
    
    if "missed_ppe" in df.columns:
        m = df["missed_ppe"].astype(str).str.strip().replace(["nan", "None", "NaN"], "")
        if (m != "").sum() > 0: return m != ""
    
    if "note" in df.columns:
        return df["note"].astype(str).str.contains("미흡")
    
    if "worn" in df.columns:
        return df["worn"].astype(str).str.strip().str.upper() == "X"
    
    return pd.Series(False, index=df.index)

def calculate_weekly_compliance(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return pd.DataFrame(columns=["week", "compliance_rate"])
    temp = df.copy()
    temp["week_num"] = pd.to_datetime(temp["date"], errors='coerce').dt.isocalendar().week.astype(int)
    temp["is_violation"] = get_violation_series(temp)
    temp["is_normal"] = ~temp["is_violation"]
    
    result = (
        temp.groupby("week_num")["is_normal"]
        .apply(lambda x: round((x.sum() / len(x)) * 100, 2) if len(x) > 0 else 0.0)
        .reset_index(name="compliance_rate")
        .sort_values("week_num")
    )
    result["week"] = result["week_num"].astype(str) + "주차"
    return result[["week", "compliance_rate"]]

def calculate_weekly_violation_counts(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return pd.DataFrame(columns=["week", "violation_count"])
    temp = df.copy()
    temp["week_num"] = pd.to_datetime(temp["date"], errors='coerce').dt.isocalendar().week.astype(int)
    temp["is_violation"] = get_violation_series(temp).astype(int)
    
    result = temp.groupby("week_num")["is_violation"].sum().reset_index(name="violation_count").sort_values("week_num")
    result["week"] = result["week_num"].astype(str) + "주차"
    return result[["week", "violation_count"]]

def calculate_weekly_ppe_missed_counts(df: pd.DataFrame) -> pd.DataFrame:
    return calculate_weekly_violation_counts(df).rename(columns={"violation_count": "ppe_missed_count"})

def get_team_comparison_chart(df: pd.DataFrame) -> list[dict]:
    if df.empty or "team" not in df.columns: return []
    temp = df.copy()
    temp["week_num"] = pd.to_datetime(temp["date"], errors='coerce').dt.isocalendar().week.astype(int)
    temp["is_normal"] = ~get_violation_series(temp)

    result = []
    for team in temp["team"].dropna().unique():
        t_df = temp[temp["team"] == team]
        t_weeks = sorted(t_df["week_num"].unique())
        if len(t_weeks) < 2: continue
        
        first_df = t_df[t_df["week_num"] == t_weeks[0]]
        last_df = t_df[t_df["week_num"] == t_weeks[-1]]
        
        first_rate = round((first_df["is_normal"].sum() / len(first_df)) * 100, 2) if len(first_df) > 0 else 0
        last_rate = round((last_df["is_normal"].sum() / len(last_df)) * 100, 2) if len(last_df) > 0 else 0
        result.append({"team": str(team), "initial_rate": first_rate, "current_rate": last_rate})
    return result

def get_team_incentive_summary(df: pd.DataFrame) -> list[str]:
    if df.empty or "team" not in df.columns: return ["팀 데이터가 없습니다."]
    temp = df.copy()
    temp["week_num"] = pd.to_datetime(temp["date"], errors='coerce').dt.isocalendar().week.astype(int)
    temp["is_violation"] = get_violation_series(temp)
    temp["is_normal"] = ~temp["is_violation"]

    summaries = []
    for team in temp["team"].dropna().unique():
        t_df = temp[temp["team"] == team]
        t_weeks = sorted(t_df["week_num"].unique())
        if len(t_weeks) < 2: continue
        
        first_df = t_df[t_df["week_num"] == t_weeks[0]]
        last_df = t_df[t_df["week_num"] == t_weeks[-1]]
        
        first_rate = round((first_df["is_normal"].sum() / len(first_df)) * 100, 2) if len(first_df) > 0 else 0
        last_rate = round((last_df["is_normal"].sum() / len(last_df)) * 100, 2) if len(last_df) > 0 else 0
        first_missed = int(first_df["is_violation"].sum())
        last_missed = int(last_df["is_violation"].sum())
        
        reduction = round(((first_missed - last_missed) / first_missed) * 100, 2) if first_missed > 0 else 0.0
        summaries.append(f"{team}: 초기 준수율 {first_rate}% → 현재 {last_rate}%, PPE 미착용 {reduction}% 감소")
    
    return summaries if summaries else ["팀별 비교 데이터가 부족합니다."]

def get_improvement_metrics(df: pd.DataFrame) -> dict:
    weekly_compliance = calculate_weekly_compliance(df)
    weekly_violations = calculate_weekly_violation_counts(df)
    weekly_ppe = calculate_weekly_ppe_missed_counts(df)
    
    best_team = "-"
    team_chart = get_team_comparison_chart(df)
    if team_chart:
        best_item = max(team_chart, key=lambda x: x["current_rate"] - x["initial_rate"])
        best_team = best_item["team"]

    if len(weekly_compliance) < 2:
        return {"improvement_rate": 0.0, "repeat_ppe_reduction_rate": 0.0, "risk_recurrence_reduction_rate": 0.0, "best_team": best_team}
    
    first_compliance = float(weekly_compliance.iloc[0]["compliance_rate"])
    last_compliance = float(weekly_compliance.iloc[-1]["compliance_rate"])
    improvement_rate = round(last_compliance - first_compliance, 2)
    
    first_ppe = int(weekly_ppe.iloc[0]["ppe_missed_count"]) if not weekly_ppe.empty else 0
    last_ppe = int(weekly_ppe.iloc[-1]["ppe_missed_count"]) if not weekly_ppe.empty else 0
    repeat_ppe_reduction_rate = round(((first_ppe - last_ppe) / first_ppe) * 100, 2) if first_ppe > 0 else 0.0
    
    first_violation = int(weekly_violations.iloc[0]["violation_count"]) if not weekly_violations.empty else 0
    last_violation = int(weekly_violations.iloc[-1]["violation_count"]) if not weekly_violations.empty else 0
    risk_recurrence_reduction_rate = round(((first_violation - last_violation) / first_violation) * 100, 2) if first_violation > 0 else 0.0
    
    return {"improvement_rate": improvement_rate, "repeat_ppe_reduction_rate": repeat_ppe_reduction_rate, "risk_recurrence_reduction_rate": risk_recurrence_reduction_rate, "best_team": best_team}

def get_weekly_trend_charts(df: pd.DataFrame) -> dict:
    weekly_violations = calculate_weekly_violation_counts(df)
    weekly_ppe = calculate_weekly_ppe_missed_counts(df)
    violation_chart = weekly_violations.rename(columns={"week": "label", "violation_count": "count"}).to_dict(orient="records")
    ppe_chart = weekly_ppe.rename(columns={"week": "label", "ppe_missed_count": "count"}).to_dict(orient="records")
    return {"violation_trend_chart": violation_chart, "ppe_trend_chart": ppe_chart}