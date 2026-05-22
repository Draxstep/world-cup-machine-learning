"""
report_exporter.py
=================
RF-10 | Export results as HTML and PDF reports.
"""

import json
import os
import textwrap
from datetime import datetime
from typing import List, Optional

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image as RLImage,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def collect_report_images(output_dir: str) -> List[str]:
    """Return sorted list of PNG files in the output directory."""
    if not os.path.isdir(output_dir):
        return []
    images = [
        os.path.join(output_dir, name)
        for name in sorted(os.listdir(output_dir))
        if name.lower().endswith(".png")
    ]
    return images


def _wrap_text(text: str, width: int = 110) -> str:
    lines = []
    for line in text.splitlines():
        if not line:
            lines.append("")
            continue
        lines.extend(textwrap.wrap(line, width=width))
    return "\n".join(lines)


def export_html_report(
    output_dir: str,
    quality_report: dict,
    metrics_report: dict,
    cluster_summary: Optional[pd.DataFrame],
    images: List[str],
) -> str:
    """Generate an HTML report in the output directory."""
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    quality_json = json.dumps(quality_report, indent=2, ensure_ascii=True)
    metrics_json = json.dumps(metrics_report, indent=2, ensure_ascii=True)

    cluster_html = "<p>No cluster summary available.</p>"
    if cluster_summary is not None and not cluster_summary.empty:
        cluster_html = cluster_summary.to_html(border=1)

    if images:
        img_tags = "\n".join(
            f'<img src="{os.path.basename(path)}" alt="{os.path.basename(path)}" />'
            for path in images
        )
    else:
        img_tags = "<p>No images found in outputs.</p>"

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>ML Tactical Intelligence Report</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 24px; color: #222; }}
h1, h2 {{ color: #222; }}
pre {{ background: #f6f6f6; padding: 12px; overflow-x: auto; }}
img {{ max-width: 100%; margin: 12px 0; }}
table {{ border-collapse: collapse; }}
th, td {{ border: 1px solid #ccc; padding: 6px 8px; font-size: 12px; }}
</style>
</head>
<body>
<h1>ML Tactical Intelligence Report</h1>
<p>Generated: {timestamp}</p>

<h2>Quality Report</h2>
<pre>{quality_json}</pre>

<h2>Metrics Report</h2>
<pre>{metrics_json}</pre>

<h2>Cluster Summary</h2>
{cluster_html}

<h2>Charts</h2>
{img_tags}
</body>
</html>
"""

    path = os.path.join(output_dir, "report.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


def _add_text_page(pdf: PdfPages, title: str, content: str) -> None:
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.text(0.5, 0.97, title, ha="center", va="top", fontsize=14, fontweight="bold")
    wrapped = _wrap_text(content, width=110)
    fig.text(0.05, 0.92, wrapped, ha="left", va="top", fontsize=9, family="monospace")
    pdf.savefig(fig)
    plt.close(fig)


def _add_image_page(pdf: PdfPages, image_path: str) -> None:
    fig = plt.figure(figsize=(11.69, 8.27))
    ax = fig.add_subplot(1, 1, 1)
    img = plt.imread(image_path)
    ax.imshow(img)
    ax.axis("off")
    ax.set_title(os.path.basename(image_path), fontsize=10)
    pdf.savefig(fig)
    plt.close(fig)


def export_pdf_report(
    output_dir: str,
    quality_report: dict,
    metrics_report: dict,
    cluster_summary: Optional[pd.DataFrame],
    images: List[str],
) -> str:
    """Generate a structured PDF report in the output directory."""
    os.makedirs(output_dir, exist_ok=True)

    path = os.path.join(output_dir, "report.pdf")

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#0A472E'),
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        'ReportSubtitle',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor('#475569'),
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=8,
        spaceBefore=4,
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=8.8,
        leading=11,
        textColor=colors.HexColor('#1F2937'),
    )
    label_style = ParagraphStyle(
        'Label',
        parent=body_style,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#0F172A'),
    )
    small_style = ParagraphStyle(
        'Small',
        parent=body_style,
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#64748B'),
    )

    def p(text, style=body_style):
        return Paragraph(str(text), style)

    def value_or_na(value, decimals=2):
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return 'N/D'
        if isinstance(value, (int, float)):
            return f"{value:.{decimals}f}"
        return str(value)

    def pick(*values):
        for value in values:
            if value is not None and not (isinstance(value, float) and pd.isna(value)):
                return value
        return None

    rf = metrics_report.get('random_forest', {})
    clustering = metrics_report.get('clustering', {})
    test_set = rf.get('test_set', {})
    cross_validation = rf.get('cross_validation', {})

    rf_summary = [
        [p('Accuracy', label_style), p(value_or_na(_safe_float(test_set.get('accuracy')), 3)), p('Precisión global en test. Valores altos indican menor error de clasificación.')],
        [p('F1 Weighted', label_style), p(value_or_na(_safe_float(test_set.get('f1_weighted')), 3)), p('Balance entre precisión y recall, ponderado por clase.')],
        [p('AUC-ROC', label_style), p(value_or_na(_safe_float(test_set.get('auc_roc')), 3)), p('Capacidad de separar clases. 0.5 es azar; más alto es mejor.')],
        [p('F1 CV (media)', label_style), p(value_or_na(_safe_float(cross_validation.get('cv_f1_mean')), 3)), p('Promedio de F1 en validación cruzada k-fold.')],
        [p('F1 CV (desv.)', label_style), p(value_or_na(_safe_float(cross_validation.get('cv_f1_std')), 3)), p('Variabilidad entre folds. Más bajo sugiere mayor estabilidad.')],
    ]

    clustering_summary_rows = [
        [p('K', label_style), p(value_or_na(clustering.get('k'), 0)), p('Número de clusters definidos por K-Means.')],
        [p('Silhouette', label_style), p(value_or_na(_safe_float(clustering.get('silhouette')), 4)), p('Separación de clusters. Más cerca de 1 significa mejor separación.')],
        [p('Davies-Bouldin', label_style), p(value_or_na(_safe_float(clustering.get('davies_bouldin')), 4)), p('Menor es mejor: clusters más compactos y separados.')],
    ]

    dataset_rows = [
        [p('Registros', label_style), p(value_or_na(quality_report.get('total_rows'), 0))],
        [p('Partidos únicos', label_style), p(value_or_na(quality_report.get('matches'), 0))],
        [p('Selecciones', label_style), p(value_or_na(quality_report.get('teams'), 0))],
        [p('Penaltis', label_style), p(value_or_na(quality_report.get('penalties'), 0))],
    ]

    cluster_table = None
    if cluster_summary is not None and not cluster_summary.empty:
        display_columns = [
            ('cluster', 'Cluster'),
            ('matches_played', 'Partidos'),
            ('avg_goals_per_match', 'Goles/partido'),
            ('penalty_rate', 'Penalti'),
            ('mean_minute', 'Minuto prom.'),
            ('knockout_goal_ratio', 'Ratio KO'),
        ]
        existing = [column for column, _ in display_columns if column in cluster_summary.columns]
        headers = [label for column, label in display_columns if column in existing]
        rows = [headers]
        for _, row in cluster_summary.sort_values(by=existing[0] if existing else cluster_summary.columns[0]).iterrows():
            rows.append([
                value_or_na(row.get(column), 2 if column != 'cluster' else 0)
                for column, _ in display_columns if column in existing
            ])
        cluster_table = rows

    story = [
        p('ML Tactical Intelligence Report', title_style),
        p(f"Generado: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", subtitle_style),
        p('Resumen ejecutivo', section_style),
        p('Este informe resume el rendimiento del modelo de clasificación, el clustering K-Means y la calidad del dataset usado para el análisis táctico.', body_style),
        Spacer(1, 8),
        p('Random Forest', section_style),
        Table(rf_summary, colWidths=[3.4 * cm, 3.2 * cm, 10.0 * cm], style=TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0A472E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOX', (0, 0), (-1, -1), 0.7, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])),
        Spacer(1, 10),
        p('Clustering', section_style),
        Table(clustering_summary_rows, colWidths=[3.8 * cm, 2.8 * cm, 10.0 * cm], style=TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#199165')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOX', (0, 0), (-1, -1), 0.7, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])),
        Spacer(1, 10),
        p('Calidad del dataset', section_style),
        Table(dataset_rows, colWidths=[4.4 * cm, 11.2 * cm], style=TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 0.7, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])),
    ]

    if cluster_table:
        story.extend([
            Spacer(1, 10),
            p('Resumen por cluster', section_style),
            Table(cluster_table, style=TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#334155')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOX', (0, 0), (-1, -1), 0.7, colors.HexColor('#CBD5E1')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ])),
        ])

    if images:
        story.extend([
            PageBreak(),
            p('Gráficas generadas', section_style),
            p('Las siguientes imágenes complementan el resumen con gráficos exportados por el pipeline.', small_style),
            Spacer(1, 8),
        ])
        for image_path in images:
            story.extend([
                p(os.path.basename(image_path), label_style),
                RLImage(image_path, width=17.5 * cm, height=10.5 * cm),
                Spacer(1, 8),
            ])

    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
        title='ML Tactical Intelligence Report',
        author='ML Tactical Intelligence',
    )
    doc.build(story)
    return path


def export_team_csv(output_dir: str, team_report: dict) -> str:
    """Export team report data as a CSV containing intervals and probabilities."""
    os.makedirs(output_dir, exist_ok=True)
    filename = f"team_report_{team_report.get('team', 'team')}.csv"
    path = os.path.join(output_dir, filename)
    rows = []
    intervals = team_report.get('intervals', [])
    probs = team_report.get('probabilities', [])
    for i, iv in enumerate(intervals):
        rows.append({
            'team': team_report.get('team', ''),
            'interval': iv,
            'probability': probs[i] if i < len(probs) else None,
        })
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False, encoding='utf-8')
    return path


def _safe_float(value, default=0.0):
    try:
        if value is None or pd.isna(value):
            return float(default)
        return float(value)
    except Exception:
        return float(default)


def _format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _format_team_name(name: str) -> str:
    return str(name or '').replace('_', ' ').title()


def export_team_pdf(output_dir: str, team_report: dict, heatmap_path: str | None = None) -> str:
    """Generate a PDF for a single team's tactical report using the same fields shown in the web UI."""
    os.makedirs(output_dir, exist_ok=True)

    team = _format_team_name(team_report.get('team', 'team'))
    path = os.path.join(output_dir, f"team_report_{team_report.get('team', 'team')}.pdf")

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TeamTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0A472E'),
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor('#475569'),
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=8,
        spaceBefore=4,
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#1F2937'),
    )
    label_style = ParagraphStyle(
        'Label',
        parent=body_style,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#0F172A'),
    )
    small_style = ParagraphStyle(
        'Small',
        parent=body_style,
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#64748B'),
    )

    def p(text, style=body_style):
        return Paragraph(str(text), style)

    profile = team_report.get('profile') or {}
    stats = team_report.get('stats') or {}
    risk_map = team_report.get('risk_map') or team_report
    cluster = team_report.get('cluster_row') or {}
    similar_teams = team_report.get('similar_teams') or profile.get('similar_teams') or []
    intervals = risk_map.get('intervals', [])
    probabilities = risk_map.get('probabilities', [])
    baseline = (risk_map.get('baseline') or {}).get('probabilities', [])

    def value_or_na(value, decimals=2):
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return 'N/D'
        if isinstance(value, (int, float)):
            return f"{value:.{decimals}f}"
        return str(value)

    def pick(*values):
        for value in values:
            if value is not None and not (isinstance(value, float) and pd.isna(value)):
                return value
        return None

    summary_data = [
        [p('Equipo', label_style), p(team)],
        [p('Cluster', label_style), p(f"#{profile.get('cluster', risk_map.get('cluster', 'N/D'))}")],
        [p('Tipo de fase', label_style), p('Eliminatoria' if risk_map.get('is_knockout') else 'Fase de grupos')],
        [p('Localía', label_style), p('Local' if risk_map.get('is_home') else 'Visitante')],
    ]

    stats_data = [
        [p('Participaciones', label_style), p(value_or_na(stats.get('participations'), 0))],
        [p('Títulos', label_style), p(value_or_na(stats.get('titles'), 0))],
        [p('Mejor posición', label_style), p(value_or_na(stats.get('best_finish')))],
        [p('Última participación', label_style), p(value_or_na(stats.get('last_participation'), 0))],
        [p('Goles / partido', label_style), p(value_or_na(pick(profile.get('avg_goals_match'), team_report.get('avg_goals_match')), 2))],
        [p('Tasa penaltis', label_style), p(_format_percent(_safe_float(pick(profile.get('penalty_rate'), team_report.get('penalty_rate')), 0)))],
        [p('Minuto promedio', label_style), p(value_or_na(pick(profile.get('mean_minute'), team_report.get('mean_minute')), 1))],
        [p('Ratio eliminatoria', label_style), p(_format_percent(_safe_float(pick(profile.get('knockout_ratio'), team_report.get('knockout_ratio')), 0)))],
    ]

    radar_data = [
        ['Métrica', 'Equipo', 'Cluster'],
        ['Goles / partido', value_or_na(pick(profile.get('avg_goals_match'), team_report.get('avg_goals_match')), 2), value_or_na(cluster.get('avg_goals_per_match'), 2)],
        ['Penaltis', _format_percent(_safe_float(pick(profile.get('penalty_rate'), team_report.get('penalty_rate')), 0)), _format_percent(_safe_float(cluster.get('penalty_rate'), 0))],
        ['Autogoles', _format_percent(_safe_float(pick(profile.get('own_goal_rate'), team_report.get('own_goal_rate')), 0)), _format_percent(_safe_float(cluster.get('own_goal_rate'), 0))],
        ['Minuto promedio', value_or_na(pick(profile.get('mean_minute'), team_report.get('mean_minute')), 1), value_or_na(cluster.get('mean_minute'), 1)],
        ['Ratio eliminatoria', _format_percent(_safe_float(pick(profile.get('knockout_ratio'), team_report.get('knockout_ratio')), 0)), _format_percent(_safe_float(cluster.get('knockout_goal_ratio'), 0))],
    ]

    interval_rows = [[p('Intervalo', label_style), p('Equipo', label_style), p('Promedio cluster', label_style)]]
    for idx, interval in enumerate(intervals):
        team_prob = probabilities[idx] if idx < len(probabilities) else None
        cluster_prob = baseline[idx] if idx < len(baseline) else None
        interval_rows.append([
            p(interval),
            p(_format_percent(_safe_float(team_prob, 0))),
            p(_format_percent(_safe_float(cluster_prob, 0))) if cluster_prob is not None else p('N/D'),
        ])

    similar_text = ', '.join(_format_team_name(team_name) for team_name in sorted(similar_teams)) if similar_teams else 'Sin equipos similares registrados.'

    story = [
        p('Reporte táctico del equipo', title_style),
        p(f"{team} · Información unificada de perfil táctico y mapa de riesgo", subtitle_style),
        Table(summary_data, colWidths=[5.0 * cm, 10.5 * cm], style=TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
            ('BOX', (0, 0), (-1, -1), 0.7, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])),
        Spacer(1, 10),
        p('Resumen del perfil', section_style),
        Table(stats_data, colWidths=[6.0 * cm, 9.5 * cm], style=TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 0.7, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])),
        Spacer(1, 10),
        p('Comparación técnica con el cluster', section_style),
        Table(radar_data, colWidths=[5.5 * cm, 4.75 * cm, 4.75 * cm], style=TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0A472E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOX', (0, 0), (-1, -1), 0.7, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])),
        Spacer(1, 10),
        p('Mapa de riesgo por intervalos', section_style),
        Table(interval_rows, colWidths=[5.0 * cm, 4.0 * cm, 5.5 * cm], style=TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#199165')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOX', (0, 0), (-1, -1), 0.7, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])),
        Spacer(1, 10),
        p('Equipos históricos similares', section_style),
        p(similar_text, body_style),
        Spacer(1, 12),
        p(f"Generado: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", small_style),
    ]

    if heatmap_path and os.path.exists(heatmap_path):
        story.extend([
            PageBreak(),
            p('Mapa de riesgo visual', section_style),
            RLImage(heatmap_path, width=17.5 * cm, height=10.5 * cm),
        ])

    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        rightMargin=1.3 * cm,
        leftMargin=1.3 * cm,
        topMargin=1.3 * cm,
        bottomMargin=1.3 * cm,
        title=f'Reporte táctico {team}',
        author='ML Tactical Intelligence',
    )
    doc.build(story)
    return path
