from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import pandas as pd
from io import StringIO

from app.logic import (
    load_logs,
    calculate_compliance_rate,
    get_weakest_zone,
    get_most_missing_ppe,
    get_priority_task,
    get_today_date_str,
    filter_by_date,
    get_hourly_violations,
    get_zone_risk_scores,
    get_safety_points,
    load_input_logs,
    normalize_input_df,
    validate_input_columns,
    calculate_input_summary,
    calculate_input_quality,
    get_input_preview,
    append_manual_entry,
    filter_input_data,
    get_analysis_kpis,
    get_analysis_charts,
    get_recommend_action,
    get_yesterday_date_str,
    get_tbm_kpis,
    get_tbm_stats,
    get_tbm_checklist,
    get_tbm_briefing_text,
    get_tbm_focus_message,
    get_tbm_full_script,
    get_improvement_metrics,
    get_weekly_trend_charts,
    get_team_comparison_chart,
    get_team_incentive_summary,
)

app = FastAPI(title="PPE Dashboard Backend")

DATA_FILE_PATH = "app/data/sample_logs.csv"


class ManualEntry(BaseModel):
    date: str
    time: str
    worker_id: str
    team: str
    zone: str
    task_type: str
    ppe_type: str
    worn: str
    risk_exposure: str
    note: str = ""


@app.get("/")
def root():
    return {"message": "PPE Dashboard Backend Running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/dashboard/test-summary")
def test_summary():
    df = load_logs(DATA_FILE_PATH)

    compliance_rate = calculate_compliance_rate(filtered_df)
    weakest_zone = get_weakest_zone(filtered_df)
    most_missing_ppe = get_most_missing_ppe(df)
    priority_task = get_priority_task(df)

    return {
        "compliance_rate": compliance_rate,
        "weakest_zone": weakest_zone,
        "most_missing_ppe": most_missing_ppe,
        "priority_task": priority_task,
    }


@app.get("/dashboard/today")
def today_dashboard(
    target_date: str | None = None,
    site: str | None = None,
):
    df = load_logs(DATA_FILE_PATH)

    selected_date = target_date if target_date else get_today_date_str()
    filtered_df = filter_by_date(df, selected_date)

    if "site" in filtered_df.columns:
        filtered_df["site"] = filtered_df["site"].astype(str).str.strip()

    if site and site != "전체 현장" and "site" in filtered_df.columns:
        selected_site = (
            str(site)
            .strip()
            .replace("현장 1", "현장1")
            .replace("현장 2", "현장2")
            .replace("현장 3", "현장3")
        )
        filtered_df = filtered_df[filtered_df["site"] == selected_site].copy()

    compliance_rate = calculate_compliance_rate(filtered_df)
    weakest_zone = get_weakest_zone(filtered_df)
    most_missing_ppe = get_most_missing_ppe(filtered_df)
    priority_task = get_priority_task(filtered_df)

    hourly_violations = get_hourly_violations(filtered_df)
    zone_risk_scores = get_zone_risk_scores(filtered_df)
    safety_points = get_safety_points(filtered_df)

    weakest_zone_score = 0
    if zone_risk_scores and weakest_zone.get("zone"):
        for item in zone_risk_scores:
            if item["zone"] == weakest_zone["zone"]:
                weakest_zone_score = item["risk_score"]
                break

    return {
        "date": selected_date,
        "site": site if site else "전체 현장",
        "kpi": {
            "compliance_rate": compliance_rate,
            "compliance_rate_text": f"{compliance_rate}%",
            "weakest_zone_name": weakest_zone["zone"] if weakest_zone.get("zone") else "-",
            "weakest_zone_score": weakest_zone_score,
            "most_missing_ppe_name": most_missing_ppe["missed_ppe"] if most_missing_ppe.get("missed_ppe") else "-",
            "most_missing_ppe_count": most_missing_ppe["count"],
            "priority_task_text": priority_task["text"] if priority_task.get("text") else "-",
        },
        "charts": {
            "hourly_violations": hourly_violations,
            "zone_risk_scores": zone_risk_scores,
        },
        "safety_points": safety_points,
    }


@app.post("/data/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="CSV 파일만 업로드 가능합니다.")

    content = await file.read()

    try:
        decoded = content.decode("utf-8-sig")
        df = pd.read_csv(StringIO(decoded))
        df = normalize_input_df(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV 읽기 실패: {e}")

    validation = validate_input_columns(df)
    if not validation["is_valid"]:
        raise HTTPException(
            status_code=400,
            detail=f"필수 컬럼 누락: {validation['missing_columns']}"
        )

    df.to_csv("app/data/input_logs.csv", index=False, encoding="utf-8-sig")

    return {
        "message": "CSV 업로드 완료",
        "file_name": file.filename,
        "rows": int(len(df)),
    }


@app.get("/data/summary")
def data_summary():
    df = load_input_logs()
    today_str = get_today_date_str()

    return {
        "date": today_str,
        "summary": calculate_input_summary(df, today_str),
        "quality": calculate_input_quality(df),
    }


@app.get("/data/preview")
def data_preview():
    df = load_input_logs()
    preview = get_input_preview(df, 10)

    return {
        "count": len(preview),
        "rows": preview,
    }


@app.post("/data/manual-entry")
def save_manual_entry(entry: ManualEntry):
    row = {
    "date": entry.date,
    "time": entry.time,
    "worker_id": entry.worker_id,
    "team": entry.team,
    "zone": entry.zone,
    "task_type": entry.task_type,
    "ppe_type": entry.ppe_type,
    "worn": entry.worn,
    "risk_exposure": entry.risk_exposure,
    "note": entry.note,
}

    append_manual_entry(row)

    return {
        "message": "수기 입력 저장 완료",
        "saved": row,
    }

@app.get("/analysis/detail")
def analysis_detail(
    start_date: str | None = None,
    end_date: str | None = None,
    site: str | None = None,
    zone: str | None = None,
    task_type: str | None = None,
    ppe_type: str | None = None,
    risk_exposure: str | None = None,
):
    df = load_input_logs()

    filtered_df = filter_input_data(
        df,
        start_date=start_date,
        end_date=end_date,
        site=site,
        zone=zone,
        task_type=task_type,
        ppe_type=ppe_type,
        risk_exposure=risk_exposure,
    )

    kpis = get_analysis_kpis(filtered_df)
    charts = get_analysis_charts(filtered_df)
    recommend_action = get_recommend_action(filtered_df)

    return {
        "filters": {
            "start_date": start_date,
            "end_date": end_date,
            "site": site,
            "zone": zone,
            "task_type": task_type,
            "ppe_type": ppe_type,
            "risk_exposure": risk_exposure
        },
        "count": int(len(filtered_df)),
        "kpis": kpis,
        "charts": charts,
        "recommend_action": recommend_action,

            # 디버그용
        "debug_columns": filtered_df.columns.tolist(),
        "debug_preview": filtered_df.head(10).to_dict(orient="records"),

    }

@app.get("/report/tbm")
def report_tbm(target_date: str | None = None):
    df = load_input_logs()

    selected_date = target_date if target_date else get_yesterday_date_str()
    day_df = filter_by_date(df, selected_date)

    kpis = get_tbm_kpis(day_df)
    stats = get_tbm_stats(day_df)
    checklist = get_tbm_checklist(day_df)
    briefing_text = get_tbm_briefing_text(day_df, selected_date)
    focus_message = get_tbm_focus_message(day_df)
    full_script = get_tbm_full_script(day_df, selected_date)

    return {
        "date": selected_date,
        "kpis": kpis,
        "stats": stats,
        "briefing_text": briefing_text,
        "checklist": checklist,
        "focus_message": focus_message,
        "full_script": full_script,
    }

@app.get("/improvement/summary")
def improvement_summary():
    df = load_input_logs()

    metrics = get_improvement_metrics(df)
    charts = get_weekly_trend_charts(df)
    team_chart = get_team_comparison_chart(df)
    team_summary = get_team_incentive_summary(df)

    return {
        "kpis": metrics,
        "charts": charts,
        "team_comparison_chart": team_chart,
        "team_summary": team_summary,
    }