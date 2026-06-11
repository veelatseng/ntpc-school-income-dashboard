from pathlib import Path
import re

import altair as alt
import pandas as pd
import streamlit as st


ROOT = Path(__file__).parent
INCOME_DIR = ROOT / "school"
ZONE_PATH = ROOT / "school" / "school_zones.csv"
RECENT_YEARS = [108, 109, 110, 111, 112]
BASIC_ZONE = "基本學區"
OPTIONAL_ZONES = ["自由學區", "共同學區"]
ZONE_TYPES = [BASIC_ZONE, "自由學區", "共同學區", "特殊規則"]

DISTRICT_CENTERS = {
    "板橋區": (25.011, 121.459),
    "三重區": (25.062, 121.487),
    "中和區": (24.999, 121.499),
    "新莊區": (25.035, 121.450),
    "新店區": (24.967, 121.542),
    "永和區": (25.010, 121.514),
    "汐止區": (25.064, 121.654),
    "土城區": (24.973, 121.443),
    "蘆洲區": (25.085, 121.471),
    "樹林區": (24.990, 121.421),
    "淡水區": (25.170, 121.440),
    "三峽區": (24.934, 121.369),
    "林口區": (25.079, 121.389),
    "鶯歌區": (24.956, 121.350),
    "五股區": (25.084, 121.438),
    "泰山區": (25.058, 121.432),
    "瑞芳區": (25.108, 121.806),
    "八里區": (25.146, 121.399),
    "深坑區": (25.001, 121.616),
    "三芝區": (25.258, 121.501),
    "金山區": (25.221, 121.638),
    "萬里區": (25.181, 121.689),
    "貢寮區": (25.021, 121.909),
    "石門區": (25.291, 121.568),
    "雙溪區": (25.038, 121.866),
    "石碇區": (24.991, 121.658),
    "坪林區": (24.935, 121.711),
    "平溪區": (25.026, 121.738),
    "烏來區": (24.865, 121.550),
}


st.set_page_config(
    page_title="新北市學區收入儀表板",
    page_icon="NTPC",
    layout="wide",
)


def add_design_system():
    st.markdown(
        """
        <style>
        :root {
          --od-ink: #f4f7fb;
          --od-muted: #9fb0c3;
          --od-line: #243247;
          --od-surface: #111827;
          --od-panel: #172033;
          --od-panel-strong: #1f2b43;
          --od-accent: #38bdf8;
          --od-accent-2: #22c55e;
          --od-accent-soft: rgba(56, 189, 248, 0.13);
          --od-warn: #f59e0b;
        }
        .stApp {
          background:
            radial-gradient(circle at 15% 0%, rgba(56, 189, 248, 0.16), transparent 34rem),
            linear-gradient(180deg, #0b1220 0%, #0f172a 56%, #111827 100%);
          color: var(--od-ink);
        }
        .stApp h1, .stApp h2, .stApp h3, .stApp h4,
        .stApp label, .stApp p, .stApp span {
          color: inherit;
        }
        .od-kicker {
          color: var(--od-accent);
          font-size: 0.78rem;
          font-weight: 700;
          letter-spacing: 0.04em;
          text-transform: uppercase;
        }
        .od-title {
          font-size: clamp(1.8rem, 3vw, 3rem);
          line-height: 1.05;
          font-weight: 760;
          margin: 0.15rem 0 0.3rem;
        }
        .od-subtitle {
          color: var(--od-muted);
          max-width: 920px;
          font-size: 1.02rem;
          margin-bottom: 16px;
        }
        .od-kpi {
          background: linear-gradient(180deg, rgba(31, 43, 67, 0.96), rgba(23, 32, 51, 0.96));
          border: 1px solid var(--od-line);
          border-radius: 8px;
          padding: 15px 16px 17px;
          min-height: 108px;
          box-shadow: 0 18px 50px rgba(0, 0, 0, 0.18);
        }
        .od-kpi-label {
          color: #d7e3f4;
          font-size: 18px;
          font-weight: 600;
          line-height: 1.25;
          margin-bottom: 12px;
        }
        .od-kpi-value {
          color: var(--od-accent);
          font-size: 34px;
          font-weight: 700;
          line-height: 1;
          letter-spacing: 0;
        }
        .od-kpi-unit {
          color: var(--od-accent);
          font-size: 20px;
          font-weight: 700;
          margin-left: 6px;
          vertical-align: baseline;
        }
        .od-mini-kpi {
          background: rgba(23, 32, 51, 0.72);
          border: 1px solid var(--od-line);
          border-radius: 8px;
          padding: 13px 14px;
          min-height: 96px;
        }
        .od-mini-kpi-label {
          color: #d7e3f4;
          font-size: 15px;
          font-weight: 650;
          line-height: 1.2;
          margin-bottom: 10px;
        }
        .od-mini-kpi-value {
          color: var(--od-accent);
          font-size: 30px;
          font-weight: 750;
          line-height: 1;
        }
        .od-mini-kpi-unit {
          color: var(--od-accent);
          font-size: 18px;
          font-weight: 750;
          margin-left: 4px;
        }
        .od-table-title {
          color: var(--od-accent);
          font-size: 18px;
          font-weight: 700;
          line-height: 1.25;
          margin: 0.2rem 0 0.75rem;
        }
        .od-status-note {
          color: #9fb0c3;
          font-size: 14px;
          line-height: 1.25;
          margin: 0 0 0.85rem;
        }
        .od-note {
          background: rgba(23, 32, 51, 0.92);
          border: 1px solid var(--od-line);
          border-left: 4px solid var(--od-accent);
          border-radius: 8px;
          padding: 0.8rem 1rem;
          color: #cdd8e8;
          margin: 0.7rem 0 1.2rem;
        }
        .od-warning {
          border-left-color: var(--od-warn);
        }
        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
          background-color: rgba(23, 32, 51, 0.95);
          border-color: var(--od-line);
          color: var(--od-ink);
        }
        div[data-testid="stSelectbox"] div[data-baseweb="select"] span,
        div[data-testid="stSelectbox"] div[data-baseweb="select"] svg {
          color: var(--od-ink);
          fill: var(--od-ink);
        }
        div[data-testid="stSelectbox"] label,
        div[data-testid="stSegmentedControl"] label {
          color: #d7e3f4;
        }
        div[data-testid="stSegmentedControl"] {
          background-color: rgba(23, 32, 51, 0.88);
        }
        div[data-testid="stSegmentedControl"] p,
        div[data-testid="stSegmentedControl"] span,
        div[data-testid="stSegmentedControl"] button p,
        div[data-testid="stSegmentedControl"] * ,
        div[role="radiogroup"] p,
        div[role="radiogroup"] span,
        div[role="radiogroup"] button,
        div[data-baseweb="button-group"] p,
        div[data-baseweb="button-group"] span,
        div[data-baseweb="button-group"] button {
          font-size: 14px !important;
          line-height: 1.2 !important;
        }
        div[data-baseweb="popover"],
        div[data-baseweb="menu"] {
          background-color: #172033;
          color: var(--od-ink);
        }
        div[data-baseweb="menu"] li,
        div[data-baseweb="menu"] li div {
          color: var(--od-ink);
          background-color: #172033;
        }
        div[data-baseweb="menu"] li:hover {
          background-color: #243247;
        }
        div[data-testid="stDataFrame"],
        div[data-testid="stDataFrameResizable"] {
          background: #172033;
          border-color: var(--od-line);
        }
        div[data-testid="stTable"] {
          background: #172033;
          color: var(--od-ink);
        }
        div[data-testid="stTabs"] button {
          font-weight: 650;
        }
        div[data-testid="stTabs"] button p {
          font-size: 18px;
        }
        @media (max-width: 720px) {
          div[data-testid="stHorizontalBlock"] {
            flex-direction: column;
          }
          div[data-testid="stHorizontalBlock"] > div {
            width: 100% !important;
            flex: 1 1 100% !important;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def normalize_district(value: str) -> str:
    value = str(value).replace("新北市", "").strip()
    return value


@st.cache_data(show_spinner=False)
def load_income() -> pd.DataFrame:
    frames = []
    for path in sorted(INCOME_DIR.glob("*_165-F.csv")):
        match = re.match(r"(\d+)_165-F\.csv$", path.name)
        if not match:
            continue
        year = int(match.group(1))
        df = pd.read_csv(path, encoding="utf-8-sig")
        df.columns = [
            str(col).replace("\ufeff", "").replace("鄉鎮市區", "縣市別")
            for col in df.columns
        ]
        df["年度"] = year
        frames.append(df)

    if not frames:
        return pd.DataFrame()

    data = pd.concat(frames, ignore_index=True)
    data["行政區"] = data["縣市別"].map(normalize_district)
    data["村里"] = data["村里"].astype(str).str.replace("\u3000", "", regex=False).str.strip()
    numeric_cols = [
        "納稅單位(戶)",
        "綜合所得總額",
        "平均數",
        "中位數",
        "第一分位數",
        "第三分位數",
        "標準差",
        "變異係數",
    ]
    for col in numeric_cols:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data["正式里"] = ~data["村里"].isin(["合計", "其他"])
    data["平均所得_萬元"] = data["平均數"] / 10
    data["中位數所得_萬元"] = data["中位數"] / 10
    data["第一分位數_萬元"] = data["第一分位數"] / 10
    data["第三分位數_萬元"] = data["第三分位數"] / 10
    data["所得總額_億元"] = data["綜合所得總額"] / 100000
    return data


@st.cache_data(show_spinner=False)
def load_zones() -> pd.DataFrame:
    columns = ["學年度", "學制", "行政區", "學校名稱", "學區類型", "村里", "鄰里備註", "資料來源"]
    if not ZONE_PATH.exists():
        return pd.DataFrame(columns=columns)

    zones = pd.read_csv(ZONE_PATH, encoding="utf-8-sig").fillna("")
    zones = zones[columns]
    zones["學制"] = zones["學制"].astype(str).str.strip()
    zones["行政區"] = zones["行政區"].astype(str).map(normalize_district)
    zones["學校名稱"] = zones["學校名稱"].astype(str).str.strip()
    zones["學區類型"] = zones["學區類型"].astype(str).str.strip()
    zones["村里"] = zones["村里"].astype(str).str.replace("\u3000", "", regex=False).str.strip()
    zones = zones[zones["學區類型"].isin(ZONE_TYPES)]
    return zones.drop_duplicates()


def fmt_money(value) -> str:
    if pd.isna(value):
        return "資料不足"
    return f"{value:,.1f} 萬元"


def fmt_rank(value) -> str:
    if pd.isna(value):
        return "資料不足"
    return f"{int(value):,}"


def render_kpi_card(container, label: str, value: str, unit: str):
    container.markdown(
        f"""
        <div class="od-kpi">
          <div class="od-kpi-label">{label}</div>
          <div class="od-kpi-value">{value}<span class="od-kpi-unit">{unit}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_mini_kpi(container, label: str, value: str):
    match = re.match(r"^(.+?)(\s*(萬元|%))$", str(value))
    if match:
        main_value = match.group(1).strip()
        unit = match.group(2).strip()
    else:
        main_value = str(value)
        unit = ""
    container.markdown(
        f"""
        <div class="od-mini-kpi">
          <div class="od-mini-kpi-label">{label}</div>
          <div class="od-mini-kpi-value">{main_value}<span class="od-mini-kpi-unit">{unit}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def weighted_median_estimate(group: pd.DataFrame) -> float:
    weights = group["納稅單位(戶)"].fillna(0)
    if weights.sum() == 0:
        return float("nan")
    return (group["中位數所得_萬元"] * weights).sum() / weights.sum()


def summarize_school_year(income_year: pd.DataFrame, zones: pd.DataFrame, zone_types) -> pd.DataFrame:
    scoped_zones = zones[zones["學區類型"].isin(zone_types)]
    if scoped_zones.empty or income_year.empty:
        return pd.DataFrame()

    merged = scoped_zones.merge(
        income_year[income_year["正式里"]],
        on=["行政區", "村里"],
        how="left",
        indicator=True,
    )

    def one_school(group: pd.DataFrame) -> pd.Series:
        matched = group[group["_merge"] == "both"].drop_duplicates(["年度", "行政區", "村里"])
        total_tax = matched["納稅單位(戶)"].sum()
        total_income = matched["綜合所得總額"].sum()
        avg_income = (total_income / total_tax / 10) if total_tax else float("nan")
        median_est = weighted_median_estimate(matched) if not matched.empty else float("nan")
        return pd.Series(
            {
                "學年度": group["學年度"].iloc[0],
                "學制": group["學制"].iloc[0],
                "行政區": group["行政區"].iloc[0],
                "學校名稱": group["學校名稱"].iloc[0],
                "納稅單位(戶)": total_tax,
                "學區里數": group[["行政區", "村里"]].drop_duplicates().shape[0],
                "可對應里數": matched[["行政區", "村里"]].drop_duplicates().shape[0],
                "未對應里數": (group["_merge"] != "both").sum(),
                "平均所得_萬元": avg_income,
                "中位數估算_萬元": median_est,
            }
        )

    summary = (
        merged.groupby(["學制", "行政區", "學校名稱"], dropna=False)
        .apply(one_school)
        .reset_index(drop=True)
    )
    summary = summary[summary["可對應里數"] > 0].copy()
    return summary


def add_ranks(summary: pd.DataFrame) -> pd.DataFrame:
    if summary.empty:
        return summary
    ranked = summary.copy()
    for metric, rank_col, pct_col in [
        ("平均所得_萬元", "平均所得排名", "平均所得百分位"),
        ("中位數估算_萬元", "中位數估算排名", "中位數估算百分位"),
    ]:
        ranked[rank_col] = ranked.groupby("學制")[metric].rank(method="min", ascending=False)
        counts = ranked.groupby("學制")[metric].transform("count")
        ranked[pct_col] = (1 - (ranked[rank_col] - 1) / counts) * 100
    return ranked


def school_timeseries(income: pd.DataFrame, zones: pd.DataFrame, school_row: pd.Series, zone_types) -> pd.DataFrame:
    scoped = zones[
        (zones["學制"] == school_row["學制"])
        & (zones["行政區"] == school_row["行政區"])
        & (zones["學校名稱"] == school_row["學校名稱"])
        & (zones["學區類型"].isin(zone_types))
    ]
    rows = []
    for year in RECENT_YEARS:
        summary = summarize_school_year(income[income["年度"] == year], scoped, zone_types)
        if summary.empty:
            continue
        item = summary.iloc[0].to_dict()
        item["年度"] = year
        rows.append(item)
    return pd.DataFrame(rows)


def village_detail(income_latest: pd.DataFrame, zones: pd.DataFrame, school_row: pd.Series) -> pd.DataFrame:
    scoped = zones[
        (zones["學制"] == school_row["學制"])
        & (zones["行政區"] == school_row["行政區"])
        & (zones["學校名稱"] == school_row["學校名稱"])
    ].copy()
    if scoped.empty:
        return scoped
    details = scoped.merge(
        income_latest[income_latest["正式里"]],
        on=["行政區", "村里"],
        how="left",
    )
    details["部分鄰或估算"] = details["鄰里備註"].str.contains("鄰|估算|除外|限額", regex=True, na=False)
    return details[
        [
            "學區類型",
            "行政區",
            "村里",
            "鄰里備註",
            "納稅單位(戶)",
            "平均所得_萬元",
            "中位數所得_萬元",
            "第一分位數_萬元",
            "第三分位數_萬元",
            "部分鄰或估算",
            "資料來源",
        ]
    ].sort_values(["學區類型", "行政區", "村里"])


def render_header(income: pd.DataFrame, zones: pd.DataFrame):
    latest_year = int(income["年度"].max()) if not income.empty else None
    min_year = int(income["年度"].min()) if not income.empty else None
    school_count = zones[["學制", "行政區", "學校名稱"]].drop_duplicates().shape[0]
    st.markdown(
        """
        <div class="od-kicker">Open data decision dashboard</div>
        <div class="od-title">新北市學區收入儀表板</div>
        <div class="od-subtitle">
        以里級綜所稅資料連結公立國中小學區，提供平均所得、中位數估算、趨勢與資料口徑。
        主排名只採基本學區；自由與共同學區採分層情境呈現。
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    render_kpi_card(c1, "收入資料年度", f"{min_year}-{latest_year}" if latest_year else "無資料", "年")
    render_kpi_card(c2, "近五年趨勢", f"{RECENT_YEARS[0]}-{RECENT_YEARS[-1]}", "年")
    render_kpi_card(c3, "載入學校數", f"{school_count:,}", "所")
    render_kpi_card(c4, "學區資料列", f"{len(zones):,}", "筆")
    if school_count < 50:
        st.markdown(
            """
            <div class="od-note od-warning">
            目前 <code>school/school_zones.csv</code> 是種子資料，尚非全新北完整學區表。
            首頁排行榜只反映已載入學校；補齊全新北公立國中小學區後，排名會自動更新。
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_rankings(basic_summary: pd.DataFrame, optional_summary: pd.DataFrame):
    st.subheader("收入排序")
    if basic_summary.empty:
        st.info("尚無可排名的學區資料。請補齊 school/school_zones.csv。")
        return

    district_options = ["全新北"] + sorted(basic_summary["行政區"].dropna().unique())

    def sync_school_district(scope_key: str):
        selected = st.session_state.get(scope_key)
        if selected and selected != "全新北":
            st.session_state["school_district"] = selected

    tabs = st.tabs(["國中", "國小"])
    for tab, level in zip(tabs, ["國中", "國小"]):
        with tab:
            scope_key = f"ranking_scope_{level}"
            selected_district = st.selectbox(
                "排行榜範圍",
                district_options,
                key=scope_key,
                label_visibility="collapsed",
                on_change=sync_school_district,
                args=(scope_key,),
            )
            title_left, title_right = st.columns(2)
            title_left.markdown(
                '<div class="od-table-title">平均所得榜</div>',
                unsafe_allow_html=True,
            )
            title_right.markdown(
                '<div class="od-table-title">中位數估算榜</div>',
                unsafe_allow_html=True,
            )
            def scoped_for_basis(selected_basis: str) -> pd.DataFrame:
                summary = basic_summary if selected_basis == "基本學區" else optional_summary
                scoped_summary = summary.copy()
                if selected_district != "全新北":
                    scoped_summary = scoped_summary[scoped_summary["行政區"] == selected_district].copy()
                    scoped_summary = add_ranks(scoped_summary)
                return scoped_summary[scoped_summary["學制"] == level]

            left, right = st.columns(2)
            with left:
                avg_basis = st.segmented_control(
                    "平均所得榜口徑",
                    options=["基本學區", "基本 + 自由/共同"],
                    default="基本學區",
                    key=f"ranking_basis_avg_{level}",
                    label_visibility="collapsed",
                )
                scoped = scoped_for_basis(avg_basis)
                if scoped.empty:
                    st.info(f"{selected_district} 尚無可排名的{level}學區資料。")
                    continue
                row_limit = 10 if selected_district == "全新北" else len(scoped)
                st.caption(f"口徑：{avg_basis}，共 {len(scoped):,} 所{level}可排序")
                if avg_basis != "基本學區":
                    st.caption("含自由/共同學區，僅供參考。")
                table = scoped.nlargest(row_limit, "平均所得_萬元")[
                    ["平均所得排名", "行政區", "學校名稱", "平均所得_萬元", "納稅單位(戶)", "可對應里數"]
                ].rename(columns={"平均所得排名": "排名"}).copy()
                table["平均所得_萬元"] = table["平均所得_萬元"].round(1)
                table = table.rename(columns={"平均所得_萬元": "平均所得(萬元)"})
                st.dataframe(table, hide_index=True, use_container_width=True)
            with right:
                median_basis = st.segmented_control(
                    "中位數估算榜口徑",
                    options=["基本學區", "基本 + 自由/共同"],
                    default="基本學區",
                    key=f"ranking_basis_median_{level}",
                    label_visibility="collapsed",
                )
                scoped = scoped_for_basis(median_basis)
                if scoped.empty:
                    st.info(f"{selected_district} 尚無可排名的{level}學區資料。")
                    continue
                row_limit = 10 if selected_district == "全新北" else len(scoped)
                st.caption(f"口徑：{median_basis}，共 {len(scoped):,} 所{level}可排序")
                if median_basis != "基本學區":
                    st.caption("含自由/共同學區，僅供參考。")
                table = scoped.nlargest(row_limit, "中位數估算_萬元")[
                    ["中位數估算排名", "行政區", "學校名稱", "中位數估算_萬元", "納稅單位(戶)", "可對應里數"]
                ].rename(columns={"中位數估算排名": "排名"}).copy()
                table["中位數估算_萬元"] = table["中位數估算_萬元"].round(1)
                table = table.rename(columns={"中位數估算_萬元": "中位數估算(萬元)"})
                st.dataframe(table, hide_index=True, use_container_width=True)


def render_map(selected_district: str):
    st.subheader("行政區地圖")
    center = DISTRICT_CENTERS.get(selected_district)
    if not center:
        st.info("此行政區尚無地圖座標。")
        return
    map_df = pd.DataFrame(
        [{"行政區": selected_district, "lat": center[0], "lon": center[1], "size": 1200}]
    )
    st.map(map_df, latitude="lat", longitude="lon", size="size", zoom=10)


def render_school_detail(income: pd.DataFrame, zones: pd.DataFrame, basic_summary: pd.DataFrame):
    st.subheader("學校查詢")
    if zones.empty:
        st.info("請先建立 school/school_zones.csv。")
        return

    districts = sorted(zones["行政區"].dropna().unique())
    if "school_district" not in st.session_state or st.session_state["school_district"] not in districts:
        st.session_state["school_district"] = districts[0]
    district_col, level_col, school_col = st.columns([0.28, 0.22, 0.5])
    selected_district = district_col.selectbox("行政區", districts, key="school_district")
    levels = sorted(zones[zones["行政區"] == selected_district]["學制"].dropna().unique())
    if "school_level" not in st.session_state or st.session_state["school_level"] not in levels:
        st.session_state["school_level"] = levels[0]
    selected_level = level_col.selectbox("學制", levels, key="school_level")
    schools = sorted(
        zones[(zones["行政區"] == selected_district) & (zones["學制"] == selected_level)][
            "學校名稱"
        ].unique()
    )
    if "school_name" not in st.session_state or st.session_state["school_name"] not in schools:
        st.session_state["school_name"] = schools[0]
    selected_school = school_col.selectbox("學校", schools, key="school_name")

    latest_year = int(income["年度"].max())
    latest = income[income["年度"] == latest_year]
    selected = pd.Series({"學制": selected_level, "行政區": selected_district, "學校名稱": selected_school})
    school_summary = basic_summary[
        (basic_summary["學制"] == selected_level)
        & (basic_summary["行政區"] == selected_district)
        & (basic_summary["學校名稱"] == selected_school)
    ]
    scenario_summary = summarize_school_year(latest, zones[
        (zones["學制"] == selected_level)
        & (zones["行政區"] == selected_district)
        & (zones["學校名稱"] == selected_school)
    ], [BASIC_ZONE] + OPTIONAL_ZONES)

    left, right = st.columns([0.62, 0.38])
    with left:
        if school_summary.empty:
            st.warning("這所學校沒有可對應到收入資料的基本學區。")
        else:
            row = school_summary.iloc[0]
            c1, c2, c3, c4 = st.columns(4)
            render_mini_kpi(c1, "基本平均所得", fmt_money(row["平均所得_萬元"]))
            render_mini_kpi(c2, "基本中位數估算", fmt_money(row["中位數估算_萬元"]))
            render_mini_kpi(c3, "平均所得排名", fmt_rank(row["平均所得排名"]))
            render_mini_kpi(c4, "百分位", f"{row['平均所得百分位']:.1f}%")

        if not scenario_summary.empty and not school_summary.empty:
            scenario = scenario_summary.iloc[0]
            base = school_summary.iloc[0]
            st.markdown("##### 分層統計")
            compare = pd.DataFrame(
                [
                    {
                        "口徑": "基本學區（排名用）",
                        "平均所得（萬元）": base["平均所得_萬元"],
                        "中位數估算（萬元）": base["中位數估算_萬元"],
                        "可對應里數": base["可對應里數"],
                        "納稅單位(戶)": base["納稅單位(戶)"],
                    },
                    {
                        "口徑": "基本 + 自由/共同（參考）",
                        "平均所得（萬元）": scenario["平均所得_萬元"],
                        "中位數估算（萬元）": scenario["中位數估算_萬元"],
                        "可對應里數": scenario["可對應里數"],
                        "納稅單位(戶)": scenario["納稅單位(戶)"],
                    },
                ]
            )
            st.dataframe(compare.round(1), hide_index=True, use_container_width=True)

    with right:
        render_map(selected_district)

    st.markdown("##### 近五年趨勢")
    trend = school_timeseries(income, zones, selected, [BASIC_ZONE])
    if trend.empty:
        st.info("沒有足夠資料顯示趨勢。")
    else:
        chart_data = trend[["年度", "平均所得_萬元", "中位數估算_萬元"]].melt(
            id_vars="年度", var_name="指標", value_name="萬元"
        )
        chart = (
            alt.Chart(chart_data)
            .mark_line(point=True)
            .encode(
                x=alt.X("年度:O", title="年度"),
                y=alt.Y("萬元:Q", title="萬元"),
                color=alt.Color(
                    "指標:N",
                    title="",
                    scale=alt.Scale(range=["#38bdf8", "#22c55e"]),
                ),
                tooltip=["年度", "指標", alt.Tooltip("萬元:Q", format=",.1f")],
            )
            .properties(height=280)
            .configure(background="transparent")
            .configure_view(stroke="#243247")
            .configure_axis(
                labelColor="#cdd8e8",
                titleColor="#d7e3f4",
                gridColor="#243247",
                domainColor="#334155",
                tickColor="#334155",
            )
            .configure_legend(labelColor="#d7e3f4", titleColor="#d7e3f4")
        )
        st.altair_chart(chart, use_container_width=True)

    st.markdown("##### 各里收入明細")
    details = village_detail(latest, zones, selected)
    if details.empty:
        st.info("沒有學區明細。")
    else:
        display = details.copy()
        for col in ["平均所得_萬元", "中位數所得_萬元", "第一分位數_萬元", "第三分位數_萬元"]:
            display[col] = display[col].round(1)
        display = display.rename(
            columns={
                "平均所得_萬元": "平均所得(萬元)",
                "中位數所得_萬元": "中位數所得(萬元)",
                "第一分位數_萬元": "第一分位數(萬元)",
                "第三分位數_萬元": "第三分位數(萬元)",
            }
        )
        st.dataframe(display, hide_index=True, use_container_width=True)
        st.download_button(
            "下載此校明細 CSV",
            data=display.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"{selected_district}_{selected_level}_{selected_school}_income_detail.csv",
            mime="text/csv",
        )


def render_quality_checks(income: pd.DataFrame, zones: pd.DataFrame):
    st.subheader("資料口徑與檢查")
    checks = []
    for year, group in income.groupby("年度"):
        checks.append(
            {
                "年度": year,
                "行政區數": group["行政區"].nunique(),
                "合計列": (group["村里"] == "合計").sum(),
                "其他列": (group["村里"] == "其他").sum(),
                "正式里": group["正式里"].sum(),
            }
        )
    st.dataframe(pd.DataFrame(checks).sort_values("年度"), hide_index=True, use_container_width=True)

    st.markdown(
        """
        <div class="od-note">
        平均所得以「綜合所得總額 ÷ 納稅單位」計算；中位數估算為各里中位數依納稅單位加權，
        不是可精確還原的學區真實中位數。自由/共同學區只作參考情境，不進首頁排名。
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.download_button(
        "下載目前學區對照表",
        data=zones.to_csv(index=False).encode("utf-8-sig"),
        file_name="school_zones.csv",
        mime="text/csv",
    )


def main():
    add_design_system()
    income = load_income()
    zones = load_zones()
    if income.empty:
        st.error("找不到收入 CSV。請確認 school/*_165-F.csv 存在。")
        return

    latest_year = int(income["年度"].max())
    latest_income = income[income["年度"] == latest_year]
    basic_summary = add_ranks(summarize_school_year(latest_income, zones, [BASIC_ZONE]))
    optional_summary = add_ranks(
        summarize_school_year(latest_income, zones, [BASIC_ZONE] + OPTIONAL_ZONES)
    )

    render_header(income, zones)
    render_rankings(basic_summary, optional_summary)
    st.divider()
    render_school_detail(income, zones, basic_summary)
    st.divider()
    render_quality_checks(income, zones)


if __name__ == "__main__":
    main()
