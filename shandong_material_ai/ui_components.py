from __future__ import annotations

from html import escape

import streamlit as st


def render_compact_stats(items: list[tuple[str, object]], columns: int = 4) -> None:
    cards = []
    for label, value in items:
        cards.append(
            f"""
            <div class="compact-stat-card">
                <span>{escape(str(label))}</span>
                <strong>{escape(str(value))}</strong>
            </div>
            """
        )

    st.html(
        f"""
        <style>
        .compact-stat-grid {{
            display: grid;
            grid-template-columns: repeat({columns}, minmax(0, 1fr));
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
            color: #5f7488;
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
        @media (max-width: 900px) {{
            .compact-stat-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
        }}
        </style>
        <section class="compact-stat-grid">{"".join(cards)}</section>
        """
    )
