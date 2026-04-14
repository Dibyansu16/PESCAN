import subprocess, sys, os

if not os.path.exists('./ember'):
    subprocess.run(['git', 'clone',
        'https://github.com/elastic/ember.git', './ember'], check=True)
    
    with open('./ember/ember/features.py', 'r') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if 'entry_name_hashed' in line and "transform([raw_obj" in line:
            lines[i] = line.replace(
                "transform([raw_obj['entry']])",
                "transform([[raw_obj['entry']]])"
            )
    
    for i, line in enumerate(lines):
        if 'lief_errors = ' in line:
            lines[i] = '        lief_errors = (Exception,)\n'
        if line.strip() == 'RuntimeError)':
            lines[i] = ''
    
    with open('./ember/ember/features.py', 'w') as f:
        f.writelines(lines)
    
    with open('./ember/ember/features.py', 'r') as f:
        content = f.read()
    for old, new in [
        ('np.int,','int,'), ('np.int)','int)'), ('np.int ','int '),
        ('np.float,','float,'), ('np.float)','float)'),
    ]:
        content = content.replace(old, new)
    with open('./ember/ember/features.py', 'w') as f:
        f.write(content)

    subprocess.run([sys.executable, '-m', 'pip',
        'install', './ember', '--quiet'], check=True)
import streamlit as st
import numpy as np
import xgboost as xgb
import sys
import os
import math
import shap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="PESCAN",
    page_icon="🔬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600&family=Syne:wght@400;500;700&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"], .stApp {
    background: #080808 !important;
    color: #c8c8c8;
    font-family: 'JetBrains Mono', monospace;
}

#MainMenu, footer, header, .stDeployButton { display: none !important; }
.block-container { padding: 2.5rem 1.5rem 4rem !important; max-width: 760px !important; }

.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid #151515;
    margin-bottom: 2rem;
}
.topbar-left { display: flex; align-items: baseline; gap: 0.75rem; }
.logo {
    font-family: 'Syne', sans-serif;
    font-size: 1.35rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: 0.04em;
}
.logo span { color: #e63333; }
.tagline {
    font-size: 0.6rem;
    color: #333;
    letter-spacing: 0.18em;
    text-transform: uppercase;
}

.stat-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1px;
    background: #111;
    border: 1px solid #111;
    border-radius: 6px;
    overflow: hidden;
    margin-bottom: 2rem;
}
.stat-cell { background: #0c0c0c; padding: 0.75rem 1rem; }
.stat-key {
    font-size: 0.55rem;
    color: #333;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 0.25rem;
}
.stat-val { font-size: 0.9rem; font-weight: 500; color: #888; }

.upload-hint {
    font-size: 0.6rem;
    color: #2a2a2a;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
div[data-testid="stFileUploadDropzone"] {
    background: #0c0c0c !important;
    border: 1px dashed #1e1e1e !important;
    border-radius: 6px !important;
}
div[data-testid="stFileUploadDropzone"]:hover { border-color: #333 !important; }
div[data-testid="stFileUploadDropzone"] p,
div[data-testid="stFileUploadDropzone"] span {
    color: #2e2e2e !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.75rem !important;
}
.stFileUploader label { display: none !important; }

.sec-head {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 2rem 0 1rem;
}
.sec-line { flex: 1; height: 1px; background: #111; }
.sec-label {
    font-size: 0.55rem;
    color: #2a2a2a;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    white-space: nowrap;
}

.verdict-wrap {
    background: #0c0c0c;
    border: 1px solid #141414;
    border-radius: 6px;
    padding: 1.5rem;
    position: relative;
    overflow: hidden;
}
.verdict-wrap::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
}
.verdict-wrap.mal::before { background: #e63333; }
.verdict-wrap.ben::before { background: #22c55e; }
.verdict-wrap.unc::before { background: #f59e0b; }

.verdict-main {
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 0.4rem;
}
.verdict-main.mal { color: #e63333; }
.verdict-main.ben { color: #22c55e; }
.verdict-main.unc { color: #f59e0b; }

.verdict-filename {
    font-size: 0.7rem;
    color: #333;
    margin-bottom: 1.2rem;
    word-break: break-all;
}

.meta-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1px;
    background: #111;
    border-radius: 4px;
    overflow: hidden;
    margin-top: 1rem;
}
.meta-cell { background: #0f0f0f; padding: 0.6rem 0.75rem; }
.meta-key {
    font-size: 0.55rem;
    color: #2a2a2a;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 0.2rem;
}
.meta-val { font-size: 0.8rem; color: #666; }

.score-track {
    height: 3px;
    background: #111;
    border-radius: 2px;
    margin-top: 1rem;
    overflow: hidden;
}
.score-fill { height: 100%; border-radius: 2px; }
.score-fill.mal { background: #e63333; }
.score-fill.ben { background: #22c55e; }
.score-fill.unc { background: #f59e0b; }
.score-labels {
    display: flex;
    justify-content: space-between;
    margin-top: 0.3rem;
    font-size: 0.55rem;
    color: #222;
    letter-spacing: 0.1em;
}

.feat-table { width: 100%; border-collapse: collapse; }
.feat-table thead tr { border-bottom: 1px solid #111; }
.feat-table th {
    font-size: 0.55rem;
    color: #2a2a2a;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    padding: 0.5rem 0.75rem;
    text-align: left;
    font-weight: 400;
}
.feat-table td {
    font-size: 0.75rem;
    padding: 0.45rem 0.75rem;
    border-bottom: 1px solid #0e0e0e;
    color: #555;
    vertical-align: middle;
}
.feat-table tr:hover td { background: #0d0d0d; }
.feat-name { color: #888 !important; }
.shap-pos { color: #e63333 !important; }
.shap-neg { color: #22c55e !important; }
.shap-bar-wrap {
    width: 80px; height: 4px;
    background: #111; border-radius: 2px;
    overflow: hidden; display: inline-block; vertical-align: middle;
}
.shap-bar-inner { height: 100%; border-radius: 2px; }

.plot-wrap {
    background: #0c0c0c;
    border: 1px solid #111;
    border-radius: 6px;
    padding: 0.5rem;
    overflow: hidden;
}

.foot {
    margin-top: 4rem;
    padding-top: 1rem;
    border-top: 1px solid #0e0e0e;
    display: flex;
    justify-content: space-between;
    font-size: 0.55rem;
    color: #1e1e1e;
    letter-spacing: 0.15em;
}
</style>
""", unsafe_allow_html=True)


def get_feature_name(idx):
    groups = [
        (256, "histogram"),    (256, "byteentropy"),
        (8,   "strings"),      (10,  "general"),
        (3,   "header_coff"),  (14,  "header_opt"),
        (50,  "section_name"), (50,  "section_rawsize"),
        (50,  "section_entropy"), (50, "section_vsize"),
        (50,  "section_props"),(256, "imports_lib"),
        (1024,"imports_func"), (128, "exports"),
        (30,  "datadirs"),
    ]
    pos = 0
    for size, name in groups:
        if idx < pos + size:
            return f"{name}_{idx - pos}"
        pos += size
    return f"feat_{idx}"

FEATURE_NAMES = [get_feature_name(i) for i in range(2381)]


@st.cache_resource
def load_model():
    model = xgb.XGBClassifier()
    model.load_model("xgb_ember.json")
    return model

@st.cache_resource
def load_extractor():
    sys.path.insert(0, './ember')
    import ember
    return ember.PEFeatureExtractor(2)

@st.cache_resource
def load_explainer(_model):
    return shap.TreeExplainer(_model)

def file_entropy(data):
    if not data: return 0.0
    c = [0]*256
    for b in data: c[b] += 1
    return -sum((v/len(data))*math.log2(v/len(data)) for v in c if v)


# ── UI ────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="topbar">
  <div class="topbar-left">
    <span class="logo">PE<span>SCAN</span>-X</span>
    <span class="tagline">Static PE Malware Classifier</span>
  </div>
</div>

<div class="stat-row">
  <div class="stat-cell">
    <div class="stat-key">ROC-AUC</div>
    <div class="stat-val">0.9949</div>
  </div>
  <div class="stat-cell">
    <div class="stat-key">Accuracy</div>
    <div class="stat-val">97.0%</div>
  </div>
  <div class="stat-cell">
    <div class="stat-key">Train set</div>
    <div class="stat-val">~600k</div>
  </div>
  <div class="stat-cell">
    <div class="stat-key">Features</div>
    <div class="stat-val">2381</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="upload-hint">— Drop PE file</div>', unsafe_allow_html=True)
uploaded = st.file_uploader("drop", type=["exe","dll","sys","bin"], label_visibility="collapsed")

if uploaded:
    bytez   = uploaded.read()
    entropy = file_entropy(bytez)
    size_kb = len(bytez) / 1024

    try:
        model     = load_model()
        extractor = load_extractor()

        with st.spinner(""):
            features     = extractor.feature_vector(bytez)
            features_arr = np.array(features).reshape(1, -1)
            prob         = float(model.predict_proba(features_arr)[0][1])

        conf = max(prob, 1-prob) * 100

        if prob >= 0.7:
            cls, label = "mal", "MALICIOUS"
        elif prob <= 0.3:
            cls, label = "ben", "BENIGN"
        else:
            cls, label = "unc", "UNCERTAIN"

        fill_pct = int(prob * 100)

        st.markdown(f"""
        <div class="sec-head">
          <div class="sec-line"></div>
          <div class="sec-label">Result</div>
          <div class="sec-line"></div>
        </div>

        <div class="verdict-wrap {cls}">
          <div class="verdict-main {cls}">{label}</div>
          <div class="verdict-filename">{uploaded.name}</div>
          <div style="display:flex;align-items:baseline;gap:0.5rem">
            <span style="font-size:1.1rem;font-weight:500;color:#ccc">{prob:.4f}</span>
            <span style="font-size:0.6rem;color:#333;letter-spacing:0.15em">MALICIOUS SCORE</span>
          </div>
          <div class="score-track">
            <div class="score-fill {cls}" style="width:{fill_pct}%"></div>
          </div>
          <div class="score-labels">
            <span>0 — BENIGN</span><span>MALICIOUS — 1</span>
          </div>
          <div class="meta-grid">
            <div class="meta-cell">
              <div class="meta-key">Confidence</div>
              <div class="meta-val">{conf:.1f}%</div>
            </div>
            <div class="meta-cell">
              <div class="meta-key">Entropy</div>
              <div class="meta-val">{entropy:.3f}</div>
            </div>
            <div class="meta-cell">
              <div class="meta-key">Size</div>
              <div class="meta-val">{size_kb:.1f} KB</div>
            </div>
            <div class="meta-cell">
              <div class="meta-key">Type</div>
              <div class="meta-val">{uploaded.name.split('.')[-1].upper()}</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # SHAP waterfall
        st.markdown("""
        <div class="sec-head">
          <div class="sec-line"></div>
          <div class="sec-label">SHAP explanation</div>
          <div class="sec-line"></div>
        </div>
        """, unsafe_allow_html=True)

        with st.spinner(""):
            explainer = load_explainer(model)
            sv        = explainer.shap_values(features_arr)[0]

        fig = plt.figure(figsize=(8, 5.5))
        fig.patch.set_facecolor('#0c0c0c')
        shap.plots.waterfall(
            shap.Explanation(
                values=sv,
                base_values=explainer.expected_value,
                data=features_arr[0],
                feature_names=FEATURE_NAMES,
            ),
            max_display=14, show=False,
        )
        for ax in fig.axes:
            ax.set_facecolor('#0c0c0c')
            ax.tick_params(colors='#444', labelsize=7)
            ax.xaxis.label.set_color('#333')
            ax.xaxis.label.set_size(8)
            for spine in ax.spines.values():
                spine.set_edgecolor('#151515')
        plt.tight_layout(pad=0.5)
        st.markdown('<div class="plot-wrap">', unsafe_allow_html=True)
        st.pyplot(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        plt.close()

        # Feature table
        st.markdown("""
        <div class="sec-head">
          <div class="sec-line"></div>
          <div class="sec-label">Top features</div>
          <div class="sec-line"></div>
        </div>
        """, unsafe_allow_html=True)

        top_idx  = np.argsort(np.abs(sv))[::-1][:12]
        max_shap = float(np.abs(sv[top_idx[0]])) or 1.0
        rows = ""
        for rank, idx in enumerate(top_idx):
            fname   = FEATURE_NAMES[idx]
            sv_val  = float(sv[idx])
            fv_val  = float(features_arr[0][idx])
            is_pos  = sv_val >= 0
            scls    = "shap-pos" if is_pos else "shap-neg"
            sign    = "+" if is_pos else ""
            barpct  = int(abs(sv_val) / max_shap * 100)
            barcol  = "#e63333" if is_pos else "#22c55e"
            rows += f"""
            <tr>
              <td style="color:#222;font-size:0.6rem;width:1.5rem">{rank+1:02d}</td>
              <td class="feat-name">{fname}</td>
              <td class="{scls}">{sign}{sv_val:.4f}</td>
              <td style="color:#2a2a2a">{fv_val:.3f}</td>
              <td>
                <div class="shap-bar-wrap">
                  <div class="shap-bar-inner" style="width:{barpct}%;background:{barcol}"></div>
                </div>
              </td>
            </tr>"""

        st.markdown(f"""
        <table class="feat-table">
          <thead><tr>
            <th>#</th><th>Feature</th><th>SHAP</th><th>Value</th><th>Impact</th>
          </tr></thead>
          <tbody>{rows}</tbody>
        </table>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.markdown(f"""
        <div class="sec-head">
          <div class="sec-line"></div>
          <div class="sec-label">Error</div>
          <div class="sec-line"></div>
        </div>
        <div class="verdict-wrap mal">
          <div style="font-size:0.8rem;color:#e63333;margin-bottom:0.5rem">{str(e)}</div>
          <div style="font-size:0.65rem;color:#2a2a2a">
            Ensure xgb_ember.json and ember/ are in the same directory as app.py
          </div>
        </div>
        """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="padding:4rem 0;text-align:center">
      <div style="font-size:0.6rem;color:#1a1a1a;letter-spacing:0.3em;text-transform:uppercase">
        Awaiting PE file
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="foot">
  <span>PESCAN · XGBoost + SHAP · EMBER 2018</span>
  <span>97% ACC · 0.9949 AUC</span>
</div>
""", unsafe_allow_html=True)
