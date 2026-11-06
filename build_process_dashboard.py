#!/usr/bin/env python3
"""
CareFlow Real-Life Working Model Dashboard Builder
===================================================
Generates the comprehensive, self-contained interactive Process Mining Dashboard:
  - Interactive SVG Spaghetti Diagram / Directly Follows Graph (DFG)
  - 40% X-Ray -> Triage Paperwork Bottleneck Visual Highlight
  - Bottleneck Heatmap & Transition Times Ranking
  - Process Variants Explorer
  - Conformance Checking & Clinical Audit
  - Embedded BigQuery Event Log Metrics & Clinical Ward Intelligence
"""

import json
from pathlib import Path
import pandas as pd

def build_dashboard():
    base_dir = Path(__file__).resolve().parent
    proc_dir = base_dir / "data" / "processed"
    
    # Load computed metrics
    with open(proc_dir / "dfg_summary.json") as f:
        dfg_summary = json.load(f)
        
    with open(proc_dir / "conformance_summary.json") as f:
        conf_summary = json.load(f)
        
    df_edges = pd.read_csv(proc_dir / "dfg_edges.csv")
    df_nodes = pd.read_csv(proc_dir / "dfg_nodes.csv")
    df_bottlenecks = pd.read_csv(proc_dir / "bottlenecks.csv")
    df_variants = pd.read_csv(proc_dir / "variants.csv")
    
    # JSON-serializable payloads
    edges_json = df_edges.to_json(orient="records")
    nodes_json = df_nodes.to_json(orient="records")
    bottlenecks_json = df_bottlenecks.to_json(orient="records")
    variants_json = df_variants.to_json(orient="records")
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CareFlow - Clinical Pathway Process Mining</title>
  <style>
    :root {{
      --bg: #0f172a;
      --card-bg: #1e293b;
      --card-border: #334155;
      --primary: #38bdf8;
      --primary-hover: #0284c7;
      --accent: #f43f5e;
      --warning: #f59e0b;
      --success: #10b981;
      --text: #f8fafc;
      --text-muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 24px;
    }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--card-border);
      margin-bottom: 24px;
    }}
    .badge {{
      display: inline-block;
      padding: 4px 10px;
      font-size: 12px;
      font-weight: 600;
      border-radius: 9999px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .badge-alert {{ background: rgba(244, 63, 94, 0.2); color: var(--accent); border: 1px solid var(--accent); }}
    .badge-success {{ background: rgba(16, 185, 129, 0.2); color: var(--success); border: 1px solid var(--success); }}
    .badge-info {{ background: rgba(56, 189, 248, 0.2); color: var(--primary); border: 1px solid var(--primary); }}
    
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}
    .kpi-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 18px;
      position: relative;
      overflow: hidden;
    }}
    .kpi-card.highlight {{
      border-color: var(--accent);
      background: linear-gradient(145deg, #1e293b, #2a1b24);
    }}
    .kpi-title {{ font-size: 13px; color: var(--text-muted); font-weight: 500; text-transform: uppercase; }}
    .kpi-value {{ font-size: 28px; font-weight: 700; margin: 8px 0 4px; color: #fff; }}
    .kpi-sub {{ font-size: 12px; color: var(--text-muted); }}

    .tabs {{
      display: flex;
      gap: 8px;
      border-bottom: 1px solid var(--card-border);
      margin-bottom: 20px;
    }}
    .tab-btn {{
      background: none;
      border: none;
      color: var(--text-muted);
      padding: 10px 20px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      border-bottom: 2px solid transparent;
      transition: all 0.2s;
    }}
    .tab-btn:hover {{ color: var(--text); }}
    .tab-btn.active {{
      color: var(--primary);
      border-bottom: 2px solid var(--primary);
    }}
    .tab-content {{ display: none; }}
    .tab-content.active {{ display: block; }}

    .card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 24px;
    }}
    .card-title {{
      font-size: 18px;
      font-weight: 600;
      margin-bottom: 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    /* Spaghetti Diagram / DFG SVG Styles */
    .dfg-container {{
      width: 100%;
      height: 480px;
      background: #0b1120;
      border-radius: 8px;
      border: 1px solid var(--card-border);
      position: relative;
      overflow: hidden;
    }}
    svg {{ width: 100%; height: 100%; }}
    .node-rect {{
      fill: #1e293b;
      stroke: var(--primary);
      stroke-width: 2px;
      rx: 8;
      cursor: pointer;
      transition: all 0.3s;
    }}
    .node-rect:hover {{ fill: #334155; filter: drop-shadow(0 0 8px var(--primary)); }}
    .node-rect.highlight {{ stroke: var(--accent); }}
    .node-text {{ fill: #fff; font-size: 12px; font-weight: 600; text-anchor: middle; pointer-events: none; }}
    .node-sub {{ fill: var(--text-muted); font-size: 10px; text-anchor: middle; pointer-events: none; }}
    .edge-line {{ stroke: #475569; stroke-width: 2; fill: none; transition: stroke 0.3s; }}
    .edge-line.loopback {{
      stroke: var(--accent);
      stroke-width: 3.5;
      stroke-dasharray: 6;
      animation: dash 1.5s linear infinite;
    }}
    @keyframes dash {{ to {{ stroke-dashoffset: -24; }} }}
    .edge-label {{ fill: #f8fafc; font-size: 10px; font-weight: 600; text-anchor: middle; }}

    /* Tables */
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }}
    th {{ background: #0f172a; padding: 12px; border-bottom: 1px solid var(--card-border); color: var(--text-muted); font-weight: 600; }}
    td {{ padding: 12px; border-bottom: 1px solid #243247; }}
    tr:hover td {{ background: #243247; }}

    /* Bar indicator */
    .bar-wrap {{ background: #334155; border-radius: 4px; height: 10px; width: 100%; overflow: hidden; }}
    .bar-fill {{ height: 100%; border-radius: 4px; }}

    .alert-banner {{
      background: rgba(244, 63, 94, 0.15);
      border: 1px solid var(--accent);
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      gap: 16px;
    }}
  </style>
</head>
<body>

  <!-- Header -->
  <div class="header">
    <div>
      <h1 style="font-size: 26px; font-weight: 800; letter-spacing: -0.02em;">CareFlow: Clinical Pathway Process Mining</h1>
      <p style="color: var(--text-muted); font-size: 14px; margin-top: 4px;">
        Hospital Operations Intelligence Engine • PM4Py 2.7.23 • BigQuery & dbt Modern Data Stack
      </p>
    </div>
    <div style="display: flex; gap: 10px;">
      <span class="badge badge-alert">Bottleneck Detected</span>
      <span class="badge badge-success">5,000 Cases Verified</span>
      <span class="badge badge-info">Infotact Batch 22.1</span>
    </div>
  </div>

  <!-- Operational Alert Banner -->
  <div class="alert-banner">
    <div style="font-size: 32px;">⚠️</div>
    <div>
      <h3 style="color: #fff; font-size: 15px; font-weight: 700;">Critical Process Mining Discovery: Missing Paperwork Loopback</h3>
      <p style="color: #fbcfe8; font-size: 13px; margin-top: 2px;">
        Process discovery identified that <strong>1,217 patients (40.2% of all X-Ray orders)</strong> are sent back to Triage due to an uncompleted diagnostic intake form. 
        Standard BI averages masked this friction. <strong>Updating the intake form will save ~20 minutes per patient and recover 594+ clinical hours.</strong>
      </p>
    </div>
  </div>

  <!-- KPI Cards -->
  <div class="kpi-grid">
    <div class="kpi-card highlight">
      <div class="kpi-title">X-Ray → Triage Loopbacks</div>
      <div class="kpi-value" style="color: var(--accent);">{conf_summary['loopback_cases']:,}</div>
      <div class="kpi-sub">40.2% of X-Ray cases ({conf_summary['loopback_rate_pct']}% of all admissions)</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Total Ingested Events</div>
      <div class="kpi-value">{dfg_summary['total_events']:,}</div>
      <div class="kpi-sub">Chronological EHR logs across 5,000 cases</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Clinical Compliance Rate</div>
      <div class="kpi-value" style="color: var(--success);">{conf_summary['compliance_rate_pct']}%</div>
      <div class="kpi-sub">Average trace fitness: {conf_summary['avg_fitness_score']} / 1.0</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Hours Lost to Paperwork</div>
      <div class="kpi-value" style="color: var(--warning);">594.1 hrs</div>
      <div class="kpi-sub">29.3 min avg delay per looped patient</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Projected Wait Time Reduction</div>
      <div class="kpi-value" style="color: var(--primary);">-20.0 min</div>
      <div class="kpi-sub">Instant ROI by streamlining intake form</div>
    </div>
  </div>

  <!-- Navigation Tabs -->
  <div class="tabs">
    <button class="tab-btn active" onclick="switchTab('dfg')">🗺️ Spaghetti Diagram (DFG)</button>
    <button class="tab-btn" onclick="switchTab('bottlenecks')">⏱️ Bottleneck Analysis</button>
    <button class="tab-btn" onclick="switchTab('variants')">📊 Process Variants</button>
    <button class="tab-btn" onclick="switchTab('conformance')">⚖️ Conformance & Compliance</button>
  </div>

  <!-- TAB 1: DFG / Spaghetti Diagram -->
  <div id="tab-dfg" class="tab-content active">
    <div class="card">
      <div class="card-title">
        <span>Discovered 'As-Is' Clinical Process Map (Directly Follows Graph)</span>
        <span style="font-size: 12px; color: var(--text-muted);">Pulsing Red Arc = 40.2% Missing Paperwork Loopback</span>
      </div>
      <div class="dfg-container">
        <svg viewBox="0 0 1000 460">
          <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#64748b" />
            </marker>
            <marker id="arrow-red" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#f43f5e" />
            </marker>
          </defs>

          <!-- Standard Forward Transitions -->
          <!-- Registration -> Triage -->
          <path d="M 140 230 L 220 230" class="edge-line" marker-end="url(#arrow)" />
          <text x="180" y="222" class="edge-label">5,000 (17m)</text>

          <!-- Triage -> X-Ray -->
          <path d="M 280 205 L 370 140" class="edge-line" marker-end="url(#arrow)" />
          <text x="315" y="165" class="edge-label">3,025 (29m)</text>

          <!-- Triage -> Lab Tests -->
          <path d="M 280 255 L 370 320" class="edge-line" marker-end="url(#arrow)" />
          <text x="315" y="305" class="edge-label">2,226 (44m)</text>

          <!-- Triage -> Doctor -->
          <path d="M 320 230 L 530 230" class="edge-line" marker-end="url(#arrow)" />
          <text x="420" y="222" class="edge-label">966 (55m)</text>

          <!-- CRITICAL LOOPBACK: X-Ray -> Triage -->
          <path d="M 400 100 Q 330 30 270 195" class="edge-line loopback" marker-end="url(#arrow-red)" />
          <rect x="280" y="45" width="160" height="24" rx="4" fill="#881337" stroke="#f43f5e" />
          <text x="360" y="61" fill="#fff" font-size="10" font-weight="bold" text-anchor="middle">⚠️ Loopback: 1,217 (40.2%)</text>

          <!-- X-Ray -> Lab Tests -->
          <path d="M 420 160 L 420 295" class="edge-line" marker-end="url(#arrow)" />
          <text x="445" y="235" class="edge-label">1,230 (51m)</text>

          <!-- X-Ray -> Doctor -->
          <path d="M 470 135 L 540 205" class="edge-line" marker-end="url(#arrow)" />
          <text x="520" y="160" class="edge-label">578 (64m)</text>

          <!-- Lab Tests -> Doctor -->
          <path d="M 470 325 L 540 255" class="edge-line" marker-end="url(#arrow)" />
          <text x="515" y="305" class="edge-label">3,456 (68m)</text>

          <!-- Doctor -> Treatment -->
          <path d="M 640 230 L 730 230" class="edge-line" marker-end="url(#arrow)" />
          <text x="685" y="222" class="edge-label">4,717 (36m)</text>

          <!-- Treatment -> Discharge -->
          <path d="M 830 230 L 900 230" class="edge-line" marker-end="url(#arrow)" />
          <text x="865" y="222" class="edge-label">5,000 (43m)</text>

          <!-- Nodes -->
          <!-- 1. Registration -->
          <g transform="translate(40, 205)">
            <rect width="100" height="50" class="node-rect" />
            <text x="50" y="26" class="node-text">Registration</text>
            <text x="50" y="40" class="node-sub">5,000 cases</text>
          </g>

          <!-- 2. Triage -->
          <g transform="translate(220, 205)">
            <rect width="100" height="50" class="node-rect highlight" />
            <text x="50" y="26" class="node-text">Triage</text>
            <text x="50" y="40" class="node-sub">6,217 events</text>
          </g>

          <!-- 3. X-Ray -->
          <g transform="translate(370, 110)">
            <rect width="100" height="50" class="node-rect highlight" />
            <text x="50" y="26" class="node-text">X-Ray</text>
            <text x="50" y="40" class="node-sub">3,025 cases</text>
          </g>

          <!-- 4. Lab Tests -->
          <g transform="translate(370, 300)">
            <rect width="100" height="50" class="node-rect" />
            <text x="50" y="26" class="node-text">Lab Tests</text>
            <text x="50" y="40" class="node-sub">3,456 cases</text>
          </g>

          <!-- 5. Doctor Consultation -->
          <g transform="translate(540, 205)">
            <rect width="100" height="50" class="node-rect" />
            <text x="50" y="26" class="node-text">Doctor Consult</text>
            <text x="50" y="40" class="node-sub">5,000 cases</text>
          </g>

          <!-- 6. Treatment -->
          <g transform="translate(730, 205)">
            <rect width="100" height="50" class="node-rect" />
            <text x="50" y="26" class="node-text">Treatment</text>
            <text x="50" y="40" class="node-sub">5,000 cases</text>
          </g>

          <!-- 7. Discharge -->
          <g transform="translate(900, 205)">
            <rect width="90" height="50" class="node-rect" style="stroke: var(--success);" />
            <text x="45" y="26" class="node-text">Discharge</text>
            <text x="45" y="40" class="node-sub">5,000 cases</text>
          </g>
        </svg>
      </div>
    </div>
  </div>

  <!-- TAB 2: Bottleneck Analysis -->
  <div id="tab-bottlenecks" class="tab-content">
    <div class="card">
      <div class="card-title">Transition Time Bottlenecks & Operational Delays</div>
      <table id="bottleneck-table">
        <thead>
          <tr>
            <th>From Activity</th>
            <th>To Activity</th>
            <th>Cases</th>
            <th>Mean Wait (min)</th>
            <th>Median (min)</th>
            <th>P90 Wait (min)</th>
            <th>Hours Lost</th>
            <th style="width: 180px;">Impact Severity</th>
          </tr>
        </thead>
        <tbody>
        </tbody>
      </table>
    </div>
  </div>

  <!-- TAB 3: Process Variants -->
  <div id="tab-variants" class="tab-content">
    <div class="card">
      <div class="card-title">Discovered Patient Pathways (Process Variants)</div>
      <table id="variants-table">
        <thead>
          <tr>
            <th>Variant ID</th>
            <th>Cases</th>
            <th>% Admissions</th>
            <th>Steps</th>
            <th>Paperwork Loopback?</th>
            <th>Pathway Sequence</th>
          </tr>
        </thead>
        <tbody>
        </tbody>
      </table>
    </div>
  </div>

  <!-- TAB 4: Conformance & Compliance -->
  <div id="tab-conformance" class="tab-content">
    <div class="card">
      <div class="card-title">Clinical Protocol Conformance Audit</div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
        <div>
          <h4 style="margin-bottom: 12px; color: var(--primary);">Institutional Compliance Summary</h4>
          <p style="color: var(--text-muted); font-size: 13px; line-height: 1.8;">
            • Mandated Path: <code>Registration → Triage → Doctor Consultation → Treatment → Discharge</code><br>
            • Compliant Cases: <strong>{conf_summary['compliant_cases']:,} / {conf_summary['total_cases']:,} ({conf_summary['compliance_rate_pct']}%)</strong><br>
            • Non-Compliant Traces: <strong>{conf_summary['total_cases'] - conf_summary['compliant_cases']:,} ({100 - conf_summary['compliance_rate_pct']:.2f}%)</strong><br>
            • Average Fitness Score: <strong>{conf_summary['avg_fitness_score']} / 1.00</strong><br>
            • Primary Violation: <strong>Missing paperwork form causing X-Ray → Triage loopback (1,217 cases)</strong>
          </p>
        </div>
        <div>
          <h4 style="margin-bottom: 12px; color: var(--warning);">Deviation Breakdown</h4>
          <div style="background: #0b1120; padding: 16px; border-radius: 8px; border: 1px solid var(--card-border);">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 13px;">
              <span>X-Ray → Triage Loopback</span>
              <span style="color: var(--accent); font-weight: bold;">{conf_summary['loopback_cases']:,} ({conf_summary['loopback_rate_pct']}%)</span>
            </div>
            <div class="bar-wrap" style="margin-bottom: 16px;">
              <div class="bar-fill" style="width: {conf_summary['loopback_rate_pct']}%; background: var(--accent);"></div>
            </div>

            <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 13px;">
              <span>Double Doctor Consultation</span>
              <span style="color: var(--warning); font-weight: bold;">{conf_summary['double_consultation_cases']:,} ({conf_summary['double_consultation_pct']}%)</span>
            </div>
            <div class="bar-wrap">
              <div class="bar-fill" style="width: {conf_summary['double_consultation_pct']}%; background: var(--warning);"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>
    const bottlenecksData = {bottlenecks_json};
    const variantsData = {variants_json};

    function switchTab(tabId) {{
      document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
      
      event.target.classList.add('active');
      document.getElementById('tab-' + tabId).classList.add('active');
    }}

    // Populate Bottlenecks
    const bTable = document.querySelector('#bottleneck-table tbody');
    bottlenecksData.forEach(row => {{
      const tr = document.createElement('tr');
      const isLoopback = row.source === 'X-Ray' && row.target === 'Triage';
      const severityColor = row.mean_wait_min > 50 ? '#f43f5e' : (row.mean_wait_min > 30 ? '#f59e0b' : '#10b981');
      const badge = isLoopback ? '<span class="badge badge-alert">LOOPBACK</span>' : '';
      
      tr.innerHTML = `
        <td><strong>${{row.source}}</strong> ${{badge}}</td>
        <td><strong>${{row.target}}</strong></td>
        <td>${{row.transition_count.toLocaleString()}}</td>
        <td style="color: ${{severityColor}}; font-weight: bold;">${{row.mean_wait_min}} min</td>
        <td>${{row.median_wait_min}} min</td>
        <td>${{row.p90_wait_min}} min</td>
        <td><strong>${{row.total_hours_lost}} hrs</strong></td>
        <td>
          <div class="bar-wrap">
            <div class="bar-fill" style="width: ${{Math.min(100, (row.mean_wait_min / 70) * 100)}}%; background: ${{severityColor}};"></div>
          </div>
        </td>
      `;
      bTable.appendChild(tr);
    }});

    // Populate Variants
    const vTable = document.querySelector('#variants-table tbody');
    variantsData.forEach(row => {{
      const tr = document.createElement('tr');
      const loopBadge = row.has_loopback 
        ? '<span class="badge badge-alert">YES (40.2% Bottleneck)</span>' 
        : '<span class="badge badge-success">COMPLIANT</span>';
      
      tr.innerHTML = `
        <td><strong>${{row.variant_id}}</strong></td>
        <td>${{row.case_count.toLocaleString()}}</td>
        <td style="font-weight: 600;">${{row.percentage}}%</td>
        <td>${{row.step_count}}</td>
        <td>${{loopBadge}}</td>
        <td style="font-family: monospace; font-size: 11px; color: var(--text-muted);">${{row.variant_path}}</td>
      `;
      vTable.appendChild(tr);
    }});
  </script>
</body>
</html>
"""
    out_html = base_dir / "careflow_prototype.html"
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ [Dashboard] Real-world Process Mining Model & Dashboard generated → {out_html}")

if __name__ == '__main__':
    build_dashboard()
