from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
BACKGROUND_IMAGES = {
    "home": BASE_DIR / "assets" / "bg-home.webp",
    "map": BASE_DIR / "assets" / "bg-map.webp",
    "recommend": BASE_DIR / "assets" / "bg-recommend.webp",
    "material": BASE_DIR / "assets" / "bg-material.webp",
    "graph": BASE_DIR / "assets" / "bg-graph.webp",
    "validation": BASE_DIR / "assets" / "bg-validation.webp",
    "literature": BASE_DIR / "assets" / "bg-literature.webp",
}
FALLBACK_BG_PATH = BASE_DIR / "assets" / "coastal-material-bg.png"


@st.cache_data
def _asset_b64(path: str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode("utf-8")


def apply_theme(page: str = "home") -> None:
    """Apply page backgrounds and Uiverse-inspired UI components."""
    bg_path = BACKGROUND_IMAGES.get(page, FALLBACK_BG_PATH)
    if not bg_path.exists():
        bg_path = FALLBACK_BG_PATH
    bg = _asset_b64(str(bg_path)) if bg_path.exists() else ""
    image_css = f"url('data:image/webp;base64,{bg}')" if bg and bg_path.suffix == ".webp" else f"url('data:image/png;base64,{bg}')" if bg else "none"

    st.markdown(
        f"""
        <style>
        /*
        Uiverse-inspired UI layer.
        Uiverse states that its UI elements are published under the MIT License.
        Integrated patterns: glassmorphism cards, gradient buttons, CSS tooltip chips.
        Source: https://uiverse.io/
        */
        :root {{
            --coastal-bg-image: {image_css};
            --ui-font: "Microsoft YaHei", "PingFang SC", "Noto Sans SC", "Source Han Sans SC", Arial, sans-serif;
            --ui-blue: #1f77b4;
            --ui-blue-deep: #0b5f8a;
            --ui-cyan: #18a4b8;
            --ui-ink: #102a43;
            --ui-muted: #5f7488;
            --ui-line: rgba(123, 159, 184, 0.24);
            --ui-surface: rgba(255, 255, 255, 0.84);
        }}
        .stApp {{
            font-family: var(--ui-font);
            background:
                linear-gradient(180deg, rgba(246, 249, 252, 0.56), rgba(246, 249, 252, 0.82)),
                var(--coastal-bg-image);
            background-size: cover;
            background-position: center top;
            background-attachment: fixed;
        }}
        .stApp::before {{
            content: "";
            position: fixed;
            inset: 0;
            z-index: 0;
            pointer-events: none;
            background:
                radial-gradient(circle at 12% 8%, rgba(255,255,255,0.16), transparent 34%),
                linear-gradient(90deg, rgba(255,255,255,0.32), rgba(255,255,255,0.08)),
                var(--coastal-bg-image);
            background-size: cover;
            background-position: center top;
            opacity: 0.28;
        }}
        .stApp > header,
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        [data-testid="collapsedControl"],
        .stDeployButton,
        button[kind="header"] {{
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            min-height: 0 !important;
        }}
        .stApp [data-testid="stAppViewContainer"],
        .stApp .main {{
            position: relative;
            z-index: 1;
        }}
        [data-testid="stSidebar"] {{
            background: rgba(255, 255, 255, 0.92);
            border-right: 1px solid rgba(148, 163, 184, 0.26);
        }}
        [data-testid="stSidebarNav"] {{
            display: none;
        }}
        .block-container {{
            padding-top: 0.65rem !important;
            padding-bottom: 2rem;
        }}
        h1, h2, h3 {{
            font-family: var(--ui-font);
            color: var(--ui-ink);
            letter-spacing: 0;
        }}
        p,
        span,
        label,
        div,
        button,
        input,
        textarea,
        [data-testid="stMarkdownContainer"],
        [data-testid="stMetric"],
        [data-testid="stDataFrame"] {{
            font-family: var(--ui-font);
        }}
        .stButton > button {{
            border: 0;
            color: #ffffff;
            background: linear-gradient(135deg, var(--ui-blue-deep), var(--ui-blue) 52%, var(--ui-cyan));
            background-size: 180% 180%;
            box-shadow: 0 10px 24px rgba(31, 119, 180, 0.24);
            transition: transform 180ms ease, box-shadow 180ms ease, filter 180ms ease, background-position 240ms ease;
        }}
        .stButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 16px 34px rgba(31, 119, 180, 0.32);
            filter: saturate(1.08);
            background-position: 100% 50%;
        }}
        div[data-testid="stMetric"],
        div[data-testid="stDataFrame"],
        div[data-testid="stPlotlyChart"],
        div[data-testid="stExpander"] {{
            background: rgba(255, 255, 255, 0.9);
            border-radius: 8px;
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
        }}
        div[data-testid="stMetric"] {{
            border: 1px solid rgba(148, 163, 184, 0.24);
            transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
        }}
        div[data-testid="stMetric"]:hover {{
            transform: translateY(-2px);
            border-color: rgba(31, 119, 180, 0.42);
            box-shadow: 0 16px 36px rgba(15, 23, 42, 0.1);
        }}
        .top-nav-wrap {{
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 8px;
            margin: 0 0 1.25rem;
            padding: 8px 0 10px;
            flex-wrap: wrap;
            backdrop-filter: blur(10px);
        }}
        .top-nav-wrap a {{
            position: relative;
            overflow: hidden;
            color: #31556f;
            text-decoration: none;
            font-size: 0.92rem;
            padding: 7px 10px;
            border-radius: 6px;
            border: 1px solid rgba(148, 163, 184, 0.28);
            background: rgba(255, 255, 255, 0.72);
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
            transition: transform 180ms ease, color 180ms ease, border-color 180ms ease, background 180ms ease;
        }}
        .top-nav-wrap a::after {{
            content: "";
            position: absolute;
            inset: auto 10px 3px;
            height: 2px;
            border-radius: 999px;
            background: linear-gradient(90deg, var(--ui-blue), var(--ui-cyan));
            transform: scaleX(0);
            transform-origin: left;
            transition: transform 180ms ease;
        }}
        .top-nav-wrap a:hover {{
            color: #0b3954;
            border-color: rgba(31, 119, 180, 0.46);
            background: rgba(255, 255, 255, 0.94);
            transform: translateY(-1px);
        }}
        .top-nav-wrap a:hover::after {{
            transform: scaleX(1);
        }}
        .top-nav-wrap a.active {{
            color: #ffffff;
            background: linear-gradient(135deg, var(--ui-blue-deep), var(--ui-blue) 58%, var(--ui-cyan));
            border-color: rgba(31, 119, 180, 0.72);
            box-shadow: 0 12px 28px rgba(31, 119, 180, 0.26);
        }}
        .top-nav-wrap a.active::after {{
            background: rgba(255, 255, 255, 0.86);
            transform: scaleX(1);
        }}
        .metric-card,
        .flow-step,
        .notice {{
            position: relative;
            overflow: hidden;
            box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
            backdrop-filter: blur(8px);
            transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
        }}
        .metric-card::before,
        .flow-step::before {{
            content: "";
            position: absolute;
            inset: 0;
            border-radius: inherit;
            padding: 1px;
            background: linear-gradient(135deg, rgba(31,119,180,0.38), rgba(24,164,184,0.1), rgba(255,255,255,0.5));
            -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
            -webkit-mask-composite: xor;
            mask-composite: exclude;
            pointer-events: none;
        }}
        .metric-card:hover,
        .flow-step:hover {{
            transform: translateY(-3px);
            box-shadow: 0 18px 42px rgba(15, 23, 42, 0.12);
        }}
        .uiverse-chip-row {{
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
            margin-top: 18px;
        }}
        .uiverse-chip {{
            position: relative;
            display: inline-flex;
            align-items: center;
            gap: 7px;
            min-height: 32px;
            padding: 7px 11px;
            border-radius: 999px;
            color: #12344d;
            border: 1px solid rgba(31, 119, 180, 0.22);
            background: linear-gradient(180deg, rgba(255,255,255,0.88), rgba(236, 246, 251, 0.74));
            box-shadow: 0 10px 26px rgba(15, 23, 42, 0.08);
            backdrop-filter: blur(8px);
            font-size: 0.88rem;
            cursor: default;
            transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
        }}
        .uiverse-chip::before {{
            content: "";
            width: 7px;
            height: 7px;
            border-radius: 999px;
            background: linear-gradient(135deg, var(--ui-blue), var(--ui-cyan));
            box-shadow: 0 0 12px rgba(24, 164, 184, 0.72);
        }}
        .uiverse-chip:hover {{
            transform: translateY(-2px);
            border-color: rgba(31, 119, 180, 0.5);
            box-shadow: 0 16px 34px rgba(15, 23, 42, 0.12);
        }}
        .uiverse-chip[data-tip]::after {{
            content: attr(data-tip);
            position: absolute;
            right: 0;
            bottom: calc(100% + 10px);
            width: max-content;
            max-width: 280px;
            white-space: normal;
            color: #ffffff;
            background: rgba(16, 42, 67, 0.96);
            padding: 8px 10px;
            border-radius: 7px;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.18);
            opacity: 0;
            transform: translateY(6px);
            pointer-events: none;
            transition: opacity 160ms ease, transform 160ms ease;
            z-index: 50;
        }}
        .uiverse-chip[data-tip]:hover::after {{
            opacity: 1;
            transform: translateY(0);
        }}
        .compact-stat-grid {{
            display: grid;
            grid-template-columns: repeat(var(--compact-stat-cols, 4), minmax(0, 1fr));
            gap: 10px;
            margin: 12px 0 16px;
        }}
        .compact-stat-card {{
            min-height: 76px;
            padding: 12px 14px;
            border-radius: 8px;
            border: 1px solid rgba(148, 163, 184, 0.24);
            background: rgba(255, 255, 255, 0.82);
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.07);
            backdrop-filter: blur(10px);
        }}
        .compact-stat-card span {{
            display: block;
            color: var(--ui-muted);
            font-size: 0.82rem;
            line-height: 1.2;
            margin-bottom: 8px;
        }}
        .compact-stat-card strong {{
            display: block;
            color: #0b3954;
            font-size: 1.16rem;
            line-height: 1.25;
            font-weight: 800;
            overflow-wrap: anywhere;
        }}
        .uiverse-glass-panel {{
            position: relative;
            overflow: hidden;
            border-radius: 8px;
            padding: 18px;
            border: 1px solid rgba(148, 163, 184, 0.24);
            background: rgba(255, 255, 255, 0.78);
            box-shadow: 0 18px 44px rgba(15, 23, 42, 0.1);
            backdrop-filter: blur(12px);
        }}
        .uiverse-glass-panel::before {{
            content: "";
            position: absolute;
            inset: -40%;
            background: conic-gradient(from 180deg, rgba(31,119,180,0.0), rgba(31,119,180,0.16), rgba(24,164,184,0.16), rgba(31,119,180,0.0));
            animation: ui-spin 14s linear infinite;
            opacity: 0.38;
            pointer-events: none;
        }}
        .uiverse-glass-panel > * {{
            position: relative;
            z-index: 1;
        }}
        .landing-hero {{
            position: relative;
            display: grid;
            grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
            gap: 28px;
            align-items: stretch;
            overflow: hidden;
            border-radius: 8px;
            padding: 28px;
            min-height: 360px;
            border: 1px solid rgba(255, 255, 255, 0.38);
            background:
                linear-gradient(135deg, rgba(8, 42, 65, 0.92), rgba(21, 118, 142, 0.76)),
                var(--coastal-bg-image);
            background-size: cover;
            background-position: center;
            box-shadow: 0 26px 64px rgba(15, 23, 42, 0.18);
            margin-bottom: 18px;
        }}
        .landing-hero::before {{
            content: "";
            position: absolute;
            inset: 0;
            background:
                linear-gradient(90deg, rgba(255,255,255,0.12), transparent 34%),
                repeating-linear-gradient(90deg, rgba(255,255,255,0.045) 0 1px, transparent 1px 86px);
            pointer-events: none;
        }}
        .landing-hero-copy,
        .landing-hero-board {{
            position: relative;
            z-index: 1;
        }}
        .landing-hero-copy {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            gap: 18px;
        }}
        .landing-eyebrow {{
            width: fit-content;
            padding: 7px 10px;
            border-radius: 999px;
            color: rgba(240, 249, 255, 0.94);
            border: 1px solid rgba(255, 255, 255, 0.28);
            background: rgba(255, 255, 255, 0.12);
            font-size: 0.82rem;
            font-weight: 700;
        }}
        .landing-hero h1 {{
            margin: 0;
            color: #ffffff;
            font-size: 2.34rem;
            line-height: 1.12;
            max-width: 820px;
        }}
        .landing-hero p {{
            margin: 0;
            color: rgba(235, 248, 255, 0.9);
            max-width: 760px;
            font-size: 1.02rem;
            line-height: 1.72;
        }}
        .landing-actions {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .landing-action {{
            display: inline-flex;
            align-items: center;
            min-height: 38px;
            padding: 8px 13px;
            border-radius: 999px;
            color: #ffffff;
            text-decoration: none;
            font-weight: 700;
            border: 1px solid rgba(255, 255, 255, 0.28);
            background: rgba(255, 255, 255, 0.14);
            backdrop-filter: blur(10px);
            transition: transform 180ms ease, background 180ms ease, box-shadow 180ms ease;
        }}
        .landing-action.primary {{
            background: linear-gradient(135deg, #ffffff, #dff7ff);
            color: #08364f;
            box-shadow: 0 16px 38px rgba(6, 35, 52, 0.22);
        }}
        .landing-action:hover {{
            transform: translateY(-2px);
            background: rgba(255, 255, 255, 0.2);
        }}
        .landing-action.primary:hover {{
            background: #ffffff;
        }}
        .landing-hero-board {{
            display: grid;
            gap: 12px;
            align-content: center;
        }}
        .board-card {{
            border-radius: 8px;
            padding: 13px;
            color: #103047;
            border: 1px solid rgba(255,255,255,0.42);
            background: rgba(255,255,255,0.78);
            box-shadow: 0 18px 44px rgba(15, 23, 42, 0.14);
            backdrop-filter: blur(14px);
        }}
        .board-card strong {{
            display: block;
            color: #092f45;
            font-size: 1.1rem;
            margin-bottom: 4px;
        }}
        .board-card span {{
            color: #506b80;
            font-size: 0.88rem;
        }}
        .design-ref-strip {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            align-items: center;
            margin: 16px 0 18px;
        }}
        .design-ref-strip .label {{
            color: var(--ui-muted);
            font-size: 0.86rem;
            font-weight: 700;
        }}
        .design-ref {{
            display: inline-flex;
            align-items: center;
            min-height: 30px;
            padding: 6px 10px;
            border-radius: 999px;
            color: #17445f;
            border: 1px solid rgba(31, 119, 180, 0.22);
            background: rgba(255, 255, 255, 0.74);
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
            font-size: 0.82rem;
        }}
        .section-title-row {{
            display: flex;
            justify-content: space-between;
            gap: 18px;
            align-items: end;
            margin: 24px 0 12px;
        }}
        .section-title-row h2 {{
            margin: 0;
            font-size: 1.42rem;
        }}
        .section-title-row p {{
            margin: 0;
            max-width: 560px;
            color: var(--ui-muted);
            line-height: 1.65;
            font-size: 0.92rem;
        }}
        .feature-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 14px;
            margin: 12px 0 20px;
        }}
        .feature-card {{
            position: relative;
            overflow: hidden;
            min-height: 142px;
            border-radius: 8px;
            padding: 16px;
            border: 1px solid var(--ui-line);
            background: var(--ui-surface);
            box-shadow: 0 16px 42px rgba(15, 23, 42, 0.08);
            backdrop-filter: blur(12px);
            transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
        }}
        .feature-card:hover {{
            transform: translateY(-3px);
            border-color: rgba(24, 164, 184, 0.48);
            box-shadow: 0 22px 54px rgba(15, 23, 42, 0.12);
        }}
        .feature-card .num {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 30px;
            height: 30px;
            border-radius: 8px;
            color: #ffffff;
            background: linear-gradient(135deg, var(--ui-blue-deep), var(--ui-cyan));
            font-size: 0.82rem;
            font-weight: 800;
        }}
        .feature-card h3 {{
            margin: 12px 0 6px;
            font-size: 1rem;
        }}
        .feature-card p {{
            margin: 0;
            color: var(--ui-muted);
            font-size: 0.88rem;
            line-height: 1.55;
        }}
        .split-insight {{
            display: grid;
            grid-template-columns: 0.92fr 1.08fr;
            gap: 14px;
            margin: 16px 0 20px;
        }}
        .insight-panel {{
            border-radius: 8px;
            padding: 18px;
            border: 1px solid var(--ui-line);
            background: rgba(255,255,255,0.82);
            box-shadow: 0 18px 44px rgba(15, 23, 42, 0.08);
            backdrop-filter: blur(12px);
        }}
        .insight-panel.dark {{
            color: #ffffff;
            background: linear-gradient(135deg, rgba(8, 54, 83, 0.94), rgba(20, 133, 153, 0.82));
        }}
        .insight-panel.dark h3,
        .insight-panel.dark p {{
            color: #ffffff;
        }}
        .insight-panel h3 {{
            margin: 0 0 10px;
            font-size: 1.16rem;
        }}
        .insight-panel p {{
            margin: 0 0 8px;
            color: var(--ui-muted);
            line-height: 1.64;
            font-size: 0.92rem;
        }}
        .pipeline {{
            display: grid;
            gap: 10px;
        }}
        .pipeline-step {{
            display: grid;
            grid-template-columns: 34px 1fr;
            gap: 10px;
            align-items: center;
            padding: 10px;
            border-radius: 8px;
            background: rgba(255,255,255,0.72);
            border: 1px solid rgba(255,255,255,0.36);
        }}
        .pipeline-step b {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 30px;
            height: 30px;
            border-radius: 999px;
            background: #ffffff;
            color: #0b5f8a;
        }}
        .pipeline-step span {{
            color: #11384f;
            font-weight: 700;
        }}
        .recommend-hero {{
            position: relative;
            overflow: hidden;
            border-radius: 8px;
            padding: 28px 30px;
            margin-bottom: 18px;
            color: var(--ui-ink);
            border: 1px solid rgba(31, 119, 180, 0.18);
            background:
                linear-gradient(90deg, rgba(255, 255, 255, 0.96) 0%, rgba(238, 247, 251, 0.78) 52%, rgba(238, 247, 251, 0.24) 100%),
                var(--coastal-bg-image);
            background-size: cover;
            background-position: center;
            box-shadow: 0 18px 46px rgba(15, 23, 42, 0.10);
            backdrop-filter: blur(10px);
        }}
        .recommend-hero.compact {{
            min-height: 240px;
        }}
        .recommend-hero::before {{
            content: "";
            position: absolute;
            inset: -2px;
            background:
                linear-gradient(90deg, transparent, rgba(31,119,180,0.10), transparent);
            transform: translateX(-100%);
            animation: ui-sheen 7s ease-in-out infinite;
            pointer-events: none;
        }}
        .recommend-hero > * {{
            position: relative;
            z-index: 1;
        }}
        .recommend-hero h1 {{
            margin: 0 0 10px;
            color: #102a43;
            font-size: 2.12rem;
            line-height: 1.18;
        }}
        .recommend-hero p {{
            width: min(820px, 100%);
            margin: 0;
            color: #486581;
            font-size: 1rem;
            line-height: 1.7;
        }}
        .recommend-panel {{
            position: sticky;
            top: 58px;
            z-index: 90;
            margin: 0 0 18px;
            padding: 18px;
            border-radius: 8px;
            border: 1px solid rgba(31, 119, 180, 0.22);
            background: rgba(255, 255, 255, 0.82);
            box-shadow: 0 18px 48px rgba(15, 23, 42, 0.1);
            backdrop-filter: blur(14px);
        }}
        .recommend-panel-title {{
            display: flex;
            justify-content: space-between;
            gap: 14px;
            align-items: flex-end;
            margin-bottom: 12px;
        }}
        .recommend-panel-title h3 {{
            margin: 0;
            font-size: 1.05rem;
        }}
        .recommend-panel-title span {{
            color: #59758c;
            font-size: 0.86rem;
        }}
        .uiverse-result-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 14px;
            margin: 14px 0 20px;
        }}
        .uiverse-result-card {{
            position: relative;
            overflow: hidden;
            min-height: 154px;
            border-radius: 8px;
            padding: 16px;
            border: 1px solid rgba(31, 119, 180, 0.24);
            background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(234, 247, 252, 0.8));
            box-shadow: 0 16px 38px rgba(15, 23, 42, 0.09);
            transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
        }}
        .uiverse-result-card::before {{
            content: "";
            position: absolute;
            width: 130px;
            height: 130px;
            right: -58px;
            top: -58px;
            border-radius: 999px;
            background: radial-gradient(circle, rgba(24,164,184,0.22), transparent 68%);
        }}
        .uiverse-result-card:hover {{
            transform: translateY(-4px);
            border-color: rgba(24, 164, 184, 0.48);
            box-shadow: 0 24px 54px rgba(15, 23, 42, 0.14);
        }}
        .uiverse-result-card .rank {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            border-radius: 999px;
            color: #ffffff;
            background: linear-gradient(135deg, var(--ui-blue-deep), var(--ui-cyan));
            font-weight: 700;
            font-size: 0.82rem;
        }}
        .uiverse-result-card .card-title {{
            margin: 12px 0 3px;
            font-size: 1.35rem;
            color: #0b2f46;
            font-weight: 800;
        }}
        .uiverse-result-card .name {{
            color: #5d7284;
            font-size: 0.9rem;
        }}
        .uiverse-result-card .meta {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin: 12px 0;
        }}
        .uiverse-result-card .pill {{
            padding: 5px 8px;
            border-radius: 999px;
            color: #16435c;
            background: rgba(227, 244, 250, 0.82);
            border: 1px solid rgba(31, 119, 180, 0.18);
            font-size: 0.78rem;
        }}
        .uiverse-result-card .score {{
            color: #0b3954;
            font-weight: 700;
        }}
        .uiverse-result-card .bar {{
            position: relative;
            height: 7px;
            overflow: hidden;
            border-radius: 999px;
            background: rgba(31,119,180,0.12);
            margin-top: 12px;
        }}
        .uiverse-result-card .bar span {{
            display: block;
            height: 100%;
            border-radius: inherit;
            background: linear-gradient(90deg, var(--ui-blue), var(--ui-cyan));
        }}
        div[data-testid="stTextInput"] input {{
            min-height: 52px;
            border-radius: 8px;
            border: 1px solid rgba(31, 119, 180, 0.28);
            background: rgba(255, 255, 255, 0.94);
            box-shadow: inset 0 0 0 1px rgba(255,255,255,0.4), 0 12px 30px rgba(15,23,42,0.08);
            transition: box-shadow 160ms ease, border-color 160ms ease, transform 160ms ease;
        }}
        div[data-testid="stTextInput"] input:focus {{
            border-color: rgba(24, 164, 184, 0.72);
            box-shadow: 0 0 0 4px rgba(24, 164, 184, 0.12), 0 16px 36px rgba(15,23,42,0.1);
        }}
        div[data-testid="stSelectbox"] > div,
        div[data-testid="stCheckbox"] label {{
            border-radius: 8px;
        }}
        @keyframes ui-spin {{
            to {{ transform: rotate(360deg); }}
        }}
        @keyframes ui-sheen {{
            0%, 58% {{ transform: translateX(-120%); opacity: 0; }}
            68% {{ opacity: 1; }}
            100% {{ transform: translateX(120%); opacity: 0; }}
        }}
        @media (max-width: 900px) {{
            .top-nav-wrap {{
                justify-content: flex-start;
                margin-top: 0;
            }}
            .top-nav-wrap a {{
                font-size: 0.86rem;
                padding: 6px 8px;
            }}
            .recommend-hero {{
                padding: 22px;
            }}
            .recommend-hero h1 {{
                font-size: 1.75rem;
            }}
            .recommend-panel-title {{
                display: block;
            }}
            .uiverse-result-grid {{
                grid-template-columns: 1fr;
            }}
            .landing-hero,
            .split-insight {{
                grid-template-columns: 1fr;
            }}
            .landing-hero {{
                min-height: auto;
                padding: 22px;
            }}
            .landing-hero h1 {{
                font-size: 1.9rem;
            }}
            .feature-grid {{
                grid-template-columns: 1fr;
            }}
            .compact-stat-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
            .section-title-row {{
                display: block;
            }}
            .recommend-panel {{
                position: relative;
                top: auto;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_top_nav(active: str) -> None:
    pages = [
        ("首页", "/"),
        ("需求地图", "/山东材料需求地图"),
        ("智能推荐", "/材料智能推荐"),
        ("材料档案", "/材料详情页"),
        ("知识图谱", "/知识图谱"),
        ("验证路径", "/研发机会与验证路径"),
        ("文献证据", "/文献证据库"),
        ("公共数据", "/公共数据资产池"),
        ("方法边界", "/方法与数据边界"),
    ]
    links = []
    for label, href in pages:
        class_name = "active" if label == active else ""
        links.append(f'<a class="{class_name}" href="{href}" target="_self">{label}</a>')
    st.markdown(f'<nav class="top-nav-wrap">{"".join(links)}</nav>', unsafe_allow_html=True)
