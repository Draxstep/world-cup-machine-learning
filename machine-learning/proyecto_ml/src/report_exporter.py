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
    """Generate a PDF report in the output directory."""
    os.makedirs(output_dir, exist_ok=True)

    quality_json = json.dumps(quality_report, indent=2, ensure_ascii=True)
    metrics_json = json.dumps(metrics_report, indent=2, ensure_ascii=True)

    summary_lines = [
        "ML Tactical Intelligence Report",
        "",
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        "Outputs include quality report, metrics, cluster summary, and charts.",
    ]

    path = os.path.join(output_dir, "report.pdf")
    with PdfPages(path) as pdf:
        _add_text_page(pdf, "Report Summary", "\n".join(summary_lines))
        _add_text_page(pdf, "Quality Report", quality_json)
        _add_text_page(pdf, "Metrics Report", metrics_json)

        if cluster_summary is not None and not cluster_summary.empty:
            _add_text_page(pdf, "Cluster Summary", cluster_summary.to_string())

        for image_path in images:
            _add_image_page(pdf, image_path)

    return path


def export_team_pdf(output_dir: str, team_report: dict, heatmap_path: str | None = None) -> str:
    """Generate a PDF for a single team's tactical report.

    team_report: dict with keys like 'team', 'intervals', 'probabilities',
    profile fields, and optional metadata.
    """
    os.makedirs(output_dir, exist_ok=True)

    path = os.path.join(output_dir, f"team_report_{team_report.get('team', 'team')}.pdf")
    with PdfPages(path) as pdf:
        _add_text_page(pdf, f"Team Report - {team_report.get('team', '').title()}", json.dumps(team_report, indent=2, ensure_ascii=False))
        if heatmap_path and os.path.exists(heatmap_path):
            _add_image_page(pdf, heatmap_path)
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
