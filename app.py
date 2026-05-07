import os, subprocess
from flask import Flask, render_template_string, request, redirect, url_for, flash, jsonify
from jinja2 import DictLoader, ChoiceLoader
from dotenv import load_dotenv
from attendance_engine import load_attendance, compute_scores, session_summary
from email_sender import send_warning

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "aikr-2024")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ══════════════════════════════════════════════════════════════════════════════
#  BASE LAYOUT
# ══════════════════════════════════════════════════════════════════════════════

BASE = """<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AIKR — {{ page_title }}</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
:root{
  --bg:#06060f;--bg2:#0d0d1f;--panel:#0f0f24;--border:#1e1e4a;
  --accent:#4d4dff;--cyan:#00d4ff;--green:#00ff88;--yellow:#ffcc00;
  --red:#ff3366;--orange:#ff7b00;--text:#c8c8f0;--dim:#5a5a8a;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:'Rajdhani',sans-serif;min-height:100vh;overflow-x:hidden}
body::before{content:'';position:fixed;inset:0;z-index:0;
  background-image:linear-gradient(rgba(77,77,255,.04) 1px,transparent 1px),
  linear-gradient(90deg,rgba(77,77,255,.04) 1px,transparent 1px);
  background-size:40px 40px;pointer-events:none}
.sb{position:fixed;top:0;left:0;bottom:0;width:230px;background:var(--bg2);
    border-right:1px solid var(--border);display:flex;flex-direction:column;z-index:100}
.sb-logo{padding:26px 22px 18px;border-bottom:1px solid var(--border)}
.logo-t{font-family:'Orbitron',monospace;font-size:22px;font-weight:900;
        background:linear-gradient(90deg,var(--accent),var(--cyan));
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:3px}
.logo-s{font-family:'Share Tech Mono',monospace;font-size:10px;color:var(--dim);margin-top:4px;letter-spacing:2px}
.sb-nav{flex:1;padding:18px 0;display:flex;flex-direction:column;gap:2px}
.nav-lbl{font-family:'Share Tech Mono',monospace;font-size:10px;color:var(--dim);letter-spacing:3px;padding:8px 22px 4px}
.nav-a{display:flex;align-items:center;gap:11px;padding:11px 22px;color:var(--dim);
       text-decoration:none;font-size:14px;font-weight:600;letter-spacing:1px;
       transition:.2s;border-left:2px solid transparent}
.nav-a:hover{color:var(--text);background:rgba(77,77,255,.08);border-left-color:var(--accent)}
.nav-a.on{color:var(--cyan);background:rgba(0,212,255,.08);border-left-color:var(--cyan)}
.nav-a i{width:15px;font-size:13px}
.sb-foot{padding:14px 22px;border-top:1px solid var(--border)}
.dot-row{display:flex;align-items:center;gap:8px;font-family:'Share Tech Mono',monospace;font-size:11px;color:var(--green)}
.dot{width:6px;height:6px;border-radius:50%;background:var(--green);animation:blink 2s infinite}
@keyframes blink{0%,100%{opacity:1;box-shadow:0 0 6px var(--green)}50%{opacity:.3;box-shadow:none}}
.main{margin-left:230px;min-height:100vh;position:relative;z-index:1}
.topbar{display:flex;align-items:center;justify-content:space-between;
        padding:16px 32px;border-bottom:1px solid var(--border);
        background:rgba(6,6,15,.85);backdrop-filter:blur(10px);position:sticky;top:0;z-index:50}
.topbar-title{font-family:'Orbitron',monospace;font-size:12px;font-weight:700;color:var(--cyan);letter-spacing:3px}
.topbar-r{display:flex;align-items:center;gap:14px}
.clock{font-family:'Share Tech Mono',monospace;font-size:12px;color:var(--dim)}
.cam-btn{display:flex;align-items:center;gap:7px;padding:8px 16px;
         background:linear-gradient(135deg,var(--accent),#2222cc);
         border:none;border-radius:6px;color:#fff;font-family:'Orbitron',monospace;
         font-size:11px;font-weight:700;letter-spacing:1px;cursor:pointer;
         transition:.2s;box-shadow:0 0 18px rgba(77,77,255,.35)}
.cam-btn:hover{transform:translateY(-1px);box-shadow:0 0 28px rgba(77,77,255,.6)}
.pg{padding:30px 32px}
.flashes{padding:0 32px 4px}
.flash{padding:11px 18px;border-radius:8px;margin-bottom:6px;font-size:14px;font-weight:600;border:1px solid}
.flash.success{background:rgba(0,255,136,.1);border-color:var(--green);color:var(--green)}
.flash.error{background:rgba(255,51,102,.1);border-color:var(--red);color:var(--red)}
.stat-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin-bottom:24px}
.stat{background:var(--panel);border:1px solid var(--border);border-radius:11px;padding:20px;position:relative;overflow:hidden;transition:.3s}
.stat::before{content:'';position:absolute;top:0;left:0;right:0;height:2px}
.stat.bl::before{background:linear-gradient(90deg,var(--accent),transparent)}
.stat.cy::before{background:linear-gradient(90deg,var(--cyan),transparent)}
.stat.gr::before{background:linear-gradient(90deg,var(--green),transparent)}
.stat.yl::before{background:linear-gradient(90deg,var(--yellow),transparent)}
.stat.or::before{background:linear-gradient(90deg,var(--orange),transparent)}
.stat.rd::before{background:linear-gradient(90deg,var(--red),transparent)}
.stat:hover{transform:translateY(-2px);border-color:rgba(77,77,255,.4)}
.stat-lbl{font-family:'Share Tech Mono',monospace;font-size:10px;color:var(--dim);letter-spacing:2px;margin-bottom:10px}
.stat-val{font-family:'Orbitron',monospace;font-size:32px;font-weight:900;line-height:1}
.stat.bl .stat-val,.stat.cy .stat-val{color:var(--cyan)}
.stat.gr .stat-val{color:var(--green)}.stat.yl .stat-val{color:var(--yellow)}
.stat.or .stat-val{color:var(--orange)}.stat.rd .stat-val{color:var(--red)}
.stat-sub{font-size:12px;color:var(--dim);margin-top:6px}
.panel{background:var(--panel);border:1px solid var(--border);border-radius:11px;overflow:hidden}
.ph{display:flex;align-items:center;justify-content:space-between;padding:16px 22px;border-bottom:1px solid var(--border)}
.ph-title{font-family:'Orbitron',monospace;font-size:11px;font-weight:700;color:var(--cyan);letter-spacing:2px}
.pb{padding:22px}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:18px}
table{width:100%;border-collapse:collapse}
th{padding:11px 14px;font-family:'Share Tech Mono',monospace;font-size:10px;color:var(--dim);letter-spacing:2px;text-align:left;border-bottom:1px solid var(--border)}
td{padding:13px 14px;font-size:14px;border-bottom:1px solid rgba(30,30,74,.5);transition:.2s}
tbody tr:hover td{background:rgba(77,77,255,.05)}
tbody tr:last-child td{border-bottom:none}
.badge{display:inline-block;padding:3px 9px;border-radius:20px;font-family:'Share Tech Mono',monospace;font-size:10px;font-weight:700;letter-spacing:1px}
.bg{background:rgba(0,255,136,.12);color:var(--green);border:1px solid rgba(0,255,136,.3)}
.by{background:rgba(255,204,0,.12);color:var(--yellow);border:1px solid rgba(255,204,0,.3)}
.bo{background:rgba(255,123,0,.12);color:var(--orange);border:1px solid rgba(255,123,0,.3)}
.br{background:rgba(255,51,102,.12);color:var(--red);border:1px solid rgba(255,51,102,.3)}
.bb{background:rgba(0,212,255,.12);color:var(--cyan);border:1px solid rgba(0,212,255,.3)}
.bar-wrap{background:var(--bg);border-radius:3px;height:5px;overflow:hidden;margin-top:5px}
.bar{height:100%;border-radius:3px;transition:width 1s ease}
.bar.g{background:var(--green)}.bar.y{background:var(--yellow)}.bar.r{background:var(--red)}
.btn{display:inline-flex;align-items:center;gap:7px;padding:9px 18px;border-radius:7px;border:1px solid;font-family:'Rajdhani',sans-serif;font-size:14px;font-weight:700;letter-spacing:1px;cursor:pointer;transition:.2s;text-decoration:none}
.btn-p{background:rgba(77,77,255,.15);border-color:var(--accent);color:var(--cyan)}
.btn-p:hover{background:rgba(77,77,255,.3);box-shadow:0 0 18px rgba(77,77,255,.4)}
.btn-d{background:rgba(255,51,102,.12);border-color:var(--red);color:var(--red)}
.btn-d:hover{background:rgba(255,51,102,.28);box-shadow:0 0 18px rgba(255,51,102,.35)}
.btn-s{background:rgba(0,255,136,.12);border-color:var(--green);color:var(--green)}
.btn-s:hover{background:rgba(0,255,136,.28)}
.flbl{font-family:'Share Tech Mono',monospace;font-size:10px;color:var(--dim);letter-spacing:2px;display:block;margin-bottom:6px}
.fi,.fsel{width:100%;padding:9px 12px;background:var(--bg);border:1px solid var(--border);border-radius:7px;color:var(--text);font-family:'Rajdhani',sans-serif;font-size:14px;outline:none;transition:.2s}
.fi:focus,.fsel:focus{border-color:var(--accent);box-shadow:0 0 0 2px rgba(77,77,255,.2)}
.fg{margin-bottom:14px}
.sh{display:flex;align-items:center;justify-content:space-between;margin-bottom:22px}
.sh-title{font-family:'Orbitron',monospace;font-size:15px;font-weight:700;color:var(--text)}
.sh-title span{color:var(--cyan)}
#toast{position:fixed;bottom:22px;right:22px;z-index:9999;background:var(--panel);border:1px solid var(--accent);border-radius:9px;padding:13px 18px;font-size:14px;font-weight:600;color:var(--cyan);box-shadow:0 0 18px rgba(77,77,255,.4);transform:translateY(70px);opacity:0;transition:.3s;max-width:300px}
#toast.show{transform:translateY(0);opacity:1}
::-webkit-scrollbar{width:5px}::-webkit-scrollbar-track{background:var(--bg2)}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--accent)}
</style>
{% block css %}{% endblock %}
</head><body>
<aside class="sb">
  <div class="sb-logo"><div class="logo-t">AIKR</div><div class="logo-s">ATTENDANCE v2.0</div></div>
  <nav class="sb-nav">
    <div class="nav-lbl">MENU</div>
    <a href="/dashboard" class="nav-a {{ 'on' if active=='dashboard' }}"><i class="fas fa-chart-line"></i>DASHBOARD</a>
    <a href="/records"   class="nav-a {{ 'on' if active=='records'   }}"><i class="fas fa-table"></i>RECORDS</a>
    <a href="/scores"    class="nav-a {{ 'on' if active=='scores'    }}"><i class="fas fa-trophy"></i>SCORES</a>
    <a href="/warn"      class="nav-a {{ 'on' if active=='warn'      }}"><i class="fas fa-exclamation-triangle"></i>WARNINGS</a>
  </nav>
  <div class="sb-foot"><div class="dot-row"><div class="dot"></div>SYSTEM ONLINE</div></div>
</aside>
<main class="main">
  <div class="topbar">
    <div class="topbar-title">{{ topbar }}</div>
    <div class="topbar-r">
      <div class="clock" id="clk"></div>
      <button class="cam-btn" onclick="startCam()"><i class="fas fa-camera"></i>START SESSION</button>
    </div>
  </div>
  {% with msgs = get_flashed_messages(with_categories=true) %}
    {% if msgs %}<div class="flashes" style="padding-top:14px">
      {% for cat,msg in msgs %}<div class="flash {{cat}}">{{msg}}</div>{% endfor %}
    </div>{% endif %}
  {% endwith %}
  <div class="pg">{% block body %}{% endblock %}</div>
</main>
<div id="toast"></div>
<script>
function tick(){const n=new Date();document.getElementById('clk').textContent=n.toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric'})+'  '+n.toLocaleTimeString('en-US',{hour12:false});}
tick();setInterval(tick,1000);
function toast(msg,c){const t=document.getElementById('toast');t.textContent=msg;t.style.borderColor=c||'var(--accent)';t.style.color=c||'var(--cyan)';t.classList.add('show');setTimeout(()=>t.classList.remove('show'),3500);}
async function startCam(){toast('⏳ Initializing Engine...','var(--cyan)');const d=await fetch('/start-camera').then(r=>r.json());toast(d.status==='ok'?'✅ '+d.message:'❌ '+d.message,d.status==='ok'?'var(--green)':'var(--red)');}
</script>
{% block js %}{% endblock %}
</body></html>"""

app.jinja_loader = ChoiceLoader([DictLoader({"base": BASE}), app.jinja_loader])

# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD — session trend removed, score distribution fixed
# ══════════════════════════════════════════════════════════════════════════════

DASHBOARD_HTML = """{% extends "base" %}
{% block css %}
<style>
.donut-wrap{position:relative;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.donut-lbl{position:absolute;text-align:center;font-family:'Orbitron',monospace}
.donut-lbl .dv{font-size:26px;font-weight:900;color:var(--cyan)}
.donut-lbl .ds{font-size:9px;color:var(--dim);letter-spacing:2px;margin-top:2px}
.top-row{display:flex;align-items:center;gap:14px;padding:11px 0;border-bottom:1px solid rgba(30,30,74,.4)}
.top-row:last-child{border-bottom:none}
.rank{font-family:'Orbitron',monospace;font-size:16px;font-weight:900;width:30px}
</style>
{% endblock %}
{% block body %}
<div class="sh">
  <div><div class="sh-title">SYSTEM <span>OVERVIEW</span></div>
  <div style="font-size:12px;color:var(--dim);font-family:'Share Tech Mono',monospace;margin-top:3px">Real-time analytics</div></div>
</div>

<div class="stat-grid">
  <div class="stat bl"><div class="stat-lbl">STUDENTS</div><div class="stat-val">{{total_students}}</div><div class="stat-sub">registered</div></div>
  <div class="stat cy"><div class="stat-lbl">SESSIONS</div><div class="stat-val">{{total_sessions}}</div><div class="stat-sub">total classes</div></div>
  <div class="stat gr"><div class="stat-lbl">ON TIME</div><div class="stat-val">{{on_time_pct}}<span style="font-size:16px">%</span></div><div class="stat-sub">≤5 min · 100pts</div></div>
  <div class="stat yl"><div class="stat-lbl">LATE</div><div class="stat-val">{{late_pct}}<span style="font-size:16px">%</span></div><div class="stat-sub">5-10 min · 75pts</div></div>
  <div class="stat or"><div class="stat-lbl">TOO LATE</div><div class="stat-val">{{too_late_pct}}<span style="font-size:16px">%</span></div><div class="stat-sub">10-15 min · 50pts</div></div>
  <div class="stat rd"><div class="stat-lbl">MISS</div><div class="stat-val">{{miss_pct}}<span style="font-size:16px">%</span></div><div class="stat-sub">>15 min · 0pts</div></div>
</div>

<!-- Score distribution now takes full width; session trend removed -->
<div style="margin-bottom:18px">
  <div class="panel">
    <div class="ph"><div class="ph-title">SCORE DISTRIBUTION</div><div id="dist-status" style="font-family:'Share Tech Mono',monospace;font-size:10px;color:var(--dim)">LOADING...</div></div>
    <div class="pb" style="display:flex;align-items:center;gap:36px">
      <div class="donut-wrap">
        <canvas id="donut" width="180" height="180"></canvas>
        <div class="donut-lbl"><div class="dv" id="dtotal">—</div><div class="ds">TOTAL</div></div>
      </div>
      <div style="flex:1">
        {% for lbl,cvar,bid,bbid in [('ON TIME (100)','var(--green)','l-ot','b-ot'),
                                     ('LATE (75)','var(--yellow)','l-late','b-late'),
                                     ('TOO LATE (50)','var(--orange)','l-tl','b-tl'),
                                     ('MISS (0)','var(--red)','l-ms','b-ms')] %}
        <div style="margin-bottom:14px">
          <div style="display:flex;justify-content:space-between;margin-bottom:4px">
            <span style="font-size:13px;font-weight:700;color:{{cvar}}">● {{lbl}}</span>
            <span style="font-family:'Share Tech Mono',monospace;font-size:13px;color:{{cvar}}" id="{{bid}}">—</span>
          </div>
          <div class="bar-wrap" style="height:7px"><div class="bar" id="{{bbid}}" style="width:0%;background:{{cvar}}"></div></div>
        </div>
        {% endfor %}
      </div>
    </div>
  </div>
</div>

<div class="g2">
  <div class="panel">
    <div class="ph"><div class="ph-title">RECENT SESSIONS</div><a href="/records" class="btn btn-p" style="padding:5px 12px;font-size:11px">VIEW ALL →</a></div>
    <div class="pb" style="padding:14px 20px">
      {% if sessions %}
      <div style="display:grid;grid-template-columns:1fr 60px 60px 60px 60px 60px;gap:6px;padding-bottom:8px;border-bottom:1px solid var(--border)">
        {% for lbl in ['DATE','TOTAL','OK','LATE','LATE+','MISS'] %}
        <span style="font-family:'Share Tech Mono',monospace;font-size:9px;color:var(--dim);letter-spacing:2px;text-align:{% if loop.first %}left{% else %}center{% endif %}">{{lbl}}</span>
        {% endfor %}
      </div>
      {% for s in sessions[:7] %}
      <div style="display:grid;grid-template-columns:1fr 60px 60px 60px 60px 60px;gap:6px;padding:11px 0;border-bottom:1px solid rgba(30,30,74,.4);font-size:14px">
        <span style="font-family:'Share Tech Mono',monospace;color:var(--cyan)">{{s.date}}</span>
        <span style="text-align:center;font-weight:700;color:var(--cyan)">{{s.total}}</span>
        <span style="text-align:center;color:var(--green)">{{s.on_time}}</span>
        <span style="text-align:center;color:var(--yellow)">{{s.late}}</span>
        <span style="text-align:center;color:var(--orange)">{{s.too_late}}</span>
        <span style="text-align:center;color:var(--red)">{{s.absent}}</span>
      </div>
      {% endfor %}
      {% else %}
      <div style="text-align:center;padding:32px;color:var(--dim);font-family:'Share Tech Mono',monospace;font-size:12px">NO DATA YET</div>
      {% endif %}
    </div>
  </div>

  <div class="panel">
    <div class="ph"><div class="ph-title">TOP ATTENDEES</div><a href="/scores" class="btn btn-p" style="padding:5px 12px;font-size:11px">ALL →</a></div>
    <div class="pb" style="padding:14px 20px">
      {% if top %}
        {% for s in top %}
        <div class="top-row">
          <div class="rank" style="color:{% if loop.index==1 %}var(--yellow){% elif loop.index==2 %}#aaa{% elif loop.index==3 %}#cd7f32{% else %}var(--dim){% endif %}">
            {{['🥇','🥈','🥉'][loop.index0] if loop.index<=3 else '#'+loop.index|string}}
          </div>
          <div style="flex:1">
            <div style="font-weight:700;font-size:15px">{{s.name}}</div>
            <div style="font-size:11px;color:var(--dim);font-family:'Share Tech Mono',monospace">{{s.sessions}} sessions</div>
          </div>
          <div style="text-align:right">
            <div style="font-family:'Orbitron',monospace;font-size:20px;font-weight:900;
              color:{% if s.avg_score>=90 %}var(--green){% elif s.avg_score>=75 %}var(--yellow){% else %}var(--red){% endif %}">
              {{s.avg_score}}
            </div>
            <div style="font-size:9px;color:var(--dim);font-family:'Share Tech Mono',monospace">AVG</div>
          </div>
        </div>
        {% endfor %}
      {% else %}
      <div style="text-align:center;padding:32px;color:var(--dim);font-family:'Share Tech Mono',monospace;font-size:12px">NO DATA YET</div>
      {% endif %}
    </div>
  </div>
</div>
{% endblock %}

{% block js %}
<script>
async function loadDash(){
  try {
    const dist = await fetch('/api/dist').then(r=>r.json());
    const tot  = dist.on_time + dist.late + dist.too_late + dist.miss;

    document.getElementById('dtotal').textContent = tot || '0';
    document.getElementById('dist-status').textContent = tot ? tot + ' RECORDS' : 'NO DATA YET';

    if(tot > 0){
      // Update labels
      document.getElementById('l-ot').textContent   = dist.on_time;
      document.getElementById('l-late').textContent  = dist.late;
      document.getElementById('l-tl').textContent    = dist.too_late;
      document.getElementById('l-ms').textContent    = dist.miss;
      // Update bars — use requestAnimationFrame so CSS transition fires
      requestAnimationFrame(()=>{
        requestAnimationFrame(()=>{
          document.getElementById('b-ot').style.width   = (dist.on_time  /tot*100).toFixed(1)+'%';
          document.getElementById('b-late').style.width = (dist.late     /tot*100).toFixed(1)+'%';
          document.getElementById('b-tl').style.width   = (dist.too_late /tot*100).toFixed(1)+'%';
          document.getElementById('b-ms').style.width   = (dist.miss     /tot*100).toFixed(1)+'%';
        });
      });
      drawDonut(dist.on_time, dist.late, dist.too_late, dist.miss, tot);
    } else {
      // Draw empty grey ring when no data
      drawEmpty();
    }
  } catch(e){
    document.getElementById('dist-status').textContent = 'ERROR';
    console.error('loadDash:', e);
  }
}

function drawDonut(ot, l, tl, ms, tot){
  const cv  = document.getElementById('donut');
  const ctx = cv.getContext('2d');
  const cx=90, cy=90, r=75, ir=54;
  ctx.clearRect(0, 0, 180, 180);

  const segs = [
    {v:ot, c:'#00ff88'},
    {v:l,  c:'#ffcc00'},
    {v:tl, c:'#ff9933'},
    {v:ms, c:'#ff3366'},
  ];

  let a = -Math.PI / 2;
  segs.forEach(s => {
    if(!s.v) return;
    const sw = s.v / tot * 2 * Math.PI;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, a, a + sw);
    ctx.closePath();
    ctx.fillStyle = s.c;
    ctx.fill();
    a += sw;
  });

  // Inner hole
  ctx.beginPath();
  ctx.arc(cx, cy, ir, 0, 2*Math.PI);
  ctx.fillStyle = '#0f0f24';
  ctx.fill();
}

function drawEmpty(){
  const cv  = document.getElementById('donut');
  const ctx = cv.getContext('2d');
  ctx.clearRect(0, 0, 180, 180);
  ctx.beginPath();
  ctx.arc(90, 90, 75, 0, 2*Math.PI);
  ctx.fillStyle = 'rgba(77,77,255,.1)';
  ctx.fill();
  ctx.beginPath();
  ctx.arc(90, 90, 54, 0, 2*Math.PI);
  ctx.fillStyle = '#0f0f24';
  ctx.fill();
}

loadDash();
</script>
{% endblock %}
"""

# ══════════════════════════════════════════════════════════════════════════════
#  RECORDS
# ══════════════════════════════════════════════════════════════════════════════

RECORDS_HTML = """{% extends "base" %}
{% block css %}
<style>
.filter-bar{background:var(--panel);border:1px solid var(--border);border-radius:11px;
            padding:18px 22px;margin-bottom:22px;display:grid;
            grid-template-columns:2fr 1fr 1fr 1.4fr auto;gap:14px;align-items:flex-end}
</style>
{% endblock %}
{% block body %}
<div class="sh">
  <div><div class="sh-title">ATTENDANCE <span>RECORDS</span></div>
  <div style="font-size:12px;color:var(--dim);font-family:'Share Tech Mono',monospace;margin-top:3px">Filter and inspect every session entry</div></div>
  <div style="font-family:'Orbitron',monospace;font-size:24px;font-weight:900;color:var(--cyan)">
    {{records|length}} <span style="font-size:11px;color:var(--dim);font-family:'Share Tech Mono',monospace">ENTRIES</span>
  </div>
</div>
<form method="GET" action="/records">
<div class="filter-bar">
  <div class="fg" style="margin:0"><label class="flbl">STUDENT NAME</label>
    <input class="fi" type="text" name="name" placeholder="Search..." value="{{f.name}}"></div>
  <div class="fg" style="margin:0"><label class="flbl">DATE FROM</label>
    <input class="fi" type="date" name="date_from" value="{{f.date_from}}"></div>
  <div class="fg" style="margin:0"><label class="flbl">DATE TO</label>
    <input class="fi" type="date" name="date_to" value="{{f.date_to}}"></div>
  <div class="fg" style="margin:0"><label class="flbl">SCORE</label>
    <select class="fsel" name="score">
      <option value="all" {{'selected' if f.score=='all'}}>All Scores</option>
      <option value="100" {{'selected' if f.score=='100'}}>100 — On Time</option>
      <option value="75"  {{'selected' if f.score=='75' }}>75 — Late</option>
      <option value="50"  {{'selected' if f.score=='50' }}>50 — Too Late</option>
      <option value="0"   {{'selected' if f.score=='0'  }}>0 — Miss</option>
    </select></div>
  <div style="display:flex;gap:7px">
    <button type="submit" class="btn btn-p"><i class="fas fa-search"></i>FILTER</button>
    <a href="/records" class="btn" style="background:var(--bg);border-color:var(--border);color:var(--dim)"><i class="fas fa-times"></i></a>
  </div>
</div>
</form>
<div class="panel">
  <div class="ph"><div class="ph-title">RESULTS</div></div>
  <div style="overflow-x:auto">
    <table>
      <thead><tr><th>#</th><th>NAME</th><th>EMAIL</th><th>DATE</th><th>TIME</th><th>SCORE</th><th>STATUS</th></tr></thead>
      <tbody>
      {% if records %}
        {% for r in records %}
        <tr>
          <td style="color:var(--dim);font-family:'Share Tech Mono',monospace;font-size:12px">{{loop.index}}</td>
          <td style="font-weight:700">{{r.name}}</td>
          <td style="font-family:'Share Tech Mono',monospace;font-size:12px;color:var(--dim)">{{r.email}}</td>
          <td style="font-family:'Share Tech Mono',monospace;color:var(--cyan)">{{r.date}}</td>
          <td style="font-family:'Share Tech Mono',monospace;color:var(--dim)">{{r.time}}</td>
          <td style="font-family:'Orbitron',monospace;font-size:17px;font-weight:900;
            color:{{'var(--green)' if r.score==100 else 'var(--yellow)' if r.score==75 else 'var(--orange)' if r.score==50 else 'var(--red)'}}">
            {{r.score}}</td>
          <td><span class="badge {{'bg' if r.score==100 else 'by' if r.score==75 else 'bo' if r.score==50 else 'br'}}">
            {{'ON TIME' if r.score==100 else 'LATE' if r.score==75 else 'TOO LATE' if r.score==50 else 'MISS'}}
          </span></td>
        </tr>
        {% endfor %}
      {% else %}
      <tr><td colspan="7" style="text-align:center;padding:44px;color:var(--dim);font-family:'Share Tech Mono',monospace;font-size:12px">NO RECORDS MATCH YOUR FILTERS</td></tr>
      {% endif %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
"""

# ══════════════════════════════════════════════════════════════════════════════
#  SCORES
# ══════════════════════════════════════════════════════════════════════════════

SCORES_HTML = """{% extends "base" %}
{% block css %}
<style>
.sc-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;margin-top:20px}
.sc-card{background:var(--panel);border:1px solid var(--border);border-radius:11px;padding:20px;position:relative;overflow:hidden;transition:.3s;cursor:default}
.sc-card::after{content:'';position:absolute;bottom:0;left:0;right:0;height:3px}
.sc-card.excellent::after{background:var(--green);box-shadow:0 0 10px var(--green)}
.sc-card.good::after{background:var(--yellow);box-shadow:0 0 10px var(--yellow)}
.sc-card.warning::after{background:var(--orange);box-shadow:0 0 10px var(--orange)}
.sc-card.danger::after{background:var(--red);box-shadow:0 0 10px var(--red)}
.sc-card:hover{transform:translateY(-3px);border-color:rgba(77,77,255,.5)}
.sc-h{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px}
.sc-num{font-family:'Orbitron',monospace;font-size:30px;font-weight:900;line-height:1}
.sc-card.excellent .sc-num{color:var(--green)}.sc-card.good .sc-num{color:var(--yellow)}
.sc-card.warning .sc-num{color:var(--orange)}.sc-card.danger .sc-num{color:var(--red)}
.sum-bar{background:var(--panel);border:1px solid var(--border);border-radius:11px;padding:18px 26px;display:flex;gap:36px;align-items:center;margin-bottom:8px}
.si{text-align:center}.sv{font-family:'Orbitron',monospace;font-size:26px;font-weight:900}
.sl{font-family:'Share Tech Mono',monospace;font-size:9px;color:var(--dim);letter-spacing:2px;margin-top:3px}
.div{width:1px;height:44px;background:var(--border)}
.sort-btns{display:flex;gap:7px;align-items:center}
.sb2{padding:6px 12px;border-radius:5px;border:1px solid var(--border);background:transparent;color:var(--dim);font-family:'Share Tech Mono',monospace;font-size:10px;letter-spacing:1px;cursor:pointer;transition:.2s}
.sb2:hover,.sb2.on{border-color:var(--accent);color:var(--cyan);background:rgba(77,77,255,.1)}
</style>
{% endblock %}
{% block body %}
<div class="sh">
  <div><div class="sh-title">STUDENT <span>SCORES</span></div>
  <div style="font-size:12px;color:var(--dim);font-family:'Share Tech Mono',monospace;margin-top:3px">Avg score = total points ÷ sessions attended</div></div>
  <div class="sort-btns">
    <span style="color:var(--dim);font-family:'Share Tech Mono',monospace;font-size:10px">SORT:</span>
    <button class="sb2 on" onclick="sort('score',this)">SCORE</button>
    <button class="sb2" onclick="sort('name',this)">NAME</button>
    <button class="sb2" onclick="sort('sessions',this)">SESSIONS</button>
  </div>
</div>
{% if students %}
<div class="sum-bar">
  <div class="si"><div class="sv" style="color:var(--cyan)">{{students|length}}</div><div class="sl">TOTAL</div></div>
  <div class="div"></div>
  <div class="si"><div class="sv" style="color:var(--green)">{{students|selectattr('status','eq','excellent')|list|length}}</div><div class="sl">EXCELLENT ≥90</div></div>
  <div class="si"><div class="sv" style="color:var(--yellow)">{{students|selectattr('status','eq','good')|list|length}}</div><div class="sl">GOOD ≥75</div></div>
  <div class="si"><div class="sv" style="color:var(--orange)">{{students|selectattr('status','eq','warning')|list|length}}</div><div class="sl">AT RISK ≥50</div></div>
  <div class="si"><div class="sv" style="color:var(--red)">{{students|selectattr('status','eq','danger')|list|length}}</div><div class="sl">CRITICAL &lt;50</div></div>
  <div class="div"></div>
  <a href="/warn" class="btn btn-d"><i class="fas fa-exclamation-triangle"></i>SEND WARNINGS</a>
</div>
<div class="sc-grid" id="grid">
{% for s in students %}
<div class="sc-card {{s.status}}" data-score="{{s.avg_score}}" data-name="{{s.name}}" data-sessions="{{s.sessions}}">
  <div class="sc-h">
    <div>
      <div style="font-size:15px;font-weight:700">{{s.name}}</div>
      <div style="font-size:11px;color:var(--dim);font-family:'Share Tech Mono',monospace;margin-top:2px">{{s.email}}</div>
    </div>
    <div>
      <div class="sc-num">{{s.avg_score|int}}</div>
      <div style="font-size:9px;color:var(--dim);font-family:'Share Tech Mono',monospace;text-align:right;letter-spacing:1px">AVG PTS</div>
    </div>
  </div>
  <div class="bar-wrap" style="height:7px">
    <div class="bar {{'g' if s.status=='excellent' else 'y' if s.status=='good' else 'r'}}" style="width:0%" data-w="{{s.avg_score}}%"></div>
  </div>
  <div style="display:flex;justify-content:space-between;margin-top:10px;font-size:12px">
    <span style="color:var(--dim);font-family:'Share Tech Mono',monospace">{{s.sessions}} SESSIONS</span>
    <span class="badge {{'bg' if s.status=='excellent' else 'by' if s.status in ['good','warning'] else 'br'}}">{{s.status|upper}}</span>
  </div>
</div>
{% endfor %}
</div>
{% else %}
<div class="panel" style="margin-top:22px">
  <div class="pb" style="text-align:center;padding:56px;color:var(--dim);font-family:'Share Tech Mono',monospace">NO DATA — RUN A CAMERA SESSION FIRST</div>
</div>
{% endif %}
{% endblock %}
{% block js %}
<script>
setTimeout(()=>{document.querySelectorAll('.bar[data-w]').forEach(b=>b.style.width=b.dataset.w)},100);
function sort(by,el){
  const g=document.getElementById('grid');if(!g)return;
  const cards=Array.from(g.children);
  cards.sort((a,b)=>{
    if(by==='score')    return parseFloat(b.getAttribute('data-score'))-parseFloat(a.getAttribute('data-score'));
    if(by==='sessions') return parseInt(b.getAttribute('data-sessions'))-parseInt(a.getAttribute('data-sessions'));
    if(by==='name')     return a.getAttribute('data-name').localeCompare(b.getAttribute('data-name'));
  }).forEach(c=>g.appendChild(c));
  document.querySelectorAll('.sb2').forEach(b=>b.classList.remove('on'));
  el.classList.add('on');
}
</script>
{% endblock %}
"""

# ══════════════════════════════════════════════════════════════════════════════
#  WARNINGS
# ══════════════════════════════════════════════════════════════════════════════

WARN_HTML = """{% extends "base" %}
{% block css %}
<style>
.warn-layout{display:grid;grid-template-columns:1fr 340px;gap:22px}
.risk-card{background:var(--panel);border:1px solid var(--border);border-radius:11px;padding:16px 20px;display:flex;align-items:center;gap:14px;transition:.2s;cursor:pointer;position:relative}
.risk-card:hover{border-color:rgba(255,51,102,.4);background:rgba(255,51,102,.04)}
.risk-card.sel{border-color:var(--red);background:rgba(255,51,102,.08)}
.risk-score{font-family:'Orbitron',monospace;font-size:26px;font-weight:900;color:var(--red);min-width:64px;text-align:center}
.risk-score.mid{color:var(--orange)}
.send-box{background:var(--panel);border:1px solid var(--border);border-radius:11px;overflow:hidden;position:sticky;top:84px;height:fit-content}
.send-hdr{padding:18px 22px;background:rgba(255,51,102,.07);border-bottom:1px solid rgba(255,51,102,.2)}
.send-title{font-family:'Orbitron',monospace;font-size:12px;font-weight:700;color:var(--red);letter-spacing:2px}
.counter{font-family:'Orbitron',monospace;font-size:42px;font-weight:900;color:var(--red);text-align:center;margin-bottom:4px}
.c-lbl{font-family:'Share Tech Mono',monospace;font-size:10px;color:var(--dim);text-align:center;letter-spacing:2px;margin-bottom:18px}
.sel-all{width:100%;padding:9px;background:transparent;border:1px solid var(--border);border-radius:7px;color:var(--dim);font-family:'Share Tech Mono',monospace;font-size:11px;cursor:pointer;transition:.2s;margin-bottom:14px}
.sel-all:hover{border-color:var(--red);color:var(--red)}
.send-big{width:100%;padding:13px;background:linear-gradient(135deg,rgba(255,51,102,.25),rgba(255,51,102,.1));border:1px solid var(--red);border-radius:7px;color:var(--red);font-family:'Orbitron',monospace;font-size:12px;font-weight:700;letter-spacing:2px;cursor:pointer;transition:.2s;margin-top:14px}
.send-big:hover{background:linear-gradient(135deg,rgba(255,51,102,.4),rgba(255,51,102,.2));box-shadow:0 0 18px rgba(255,51,102,.3)}
.send-big:disabled{opacity:.35;cursor:not-allowed}
.note-box{background:rgba(255,204,0,.07);border:1px solid rgba(255,204,0,.2);border-radius:7px;padding:11px 13px;font-size:11px;color:var(--yellow);font-family:'Share Tech Mono',monospace;margin-top:14px;line-height:1.6}
</style>
{% endblock %}
{% block body %}
<div class="sh">
  <div><div class="sh-title">WARNING <span>CENTER</span></div>
  <div style="font-size:12px;color:var(--dim);font-family:'Share Tech Mono',monospace;margin-top:3px">Select students and send automated email alerts</div></div>
  <form method="GET" action="/warn" style="display:flex;align-items:center;gap:10px">
    <label class="flbl" style="margin:0;white-space:nowrap">THRESHOLD BELOW</label>
    <input class="fi" type="number" name="threshold" value="{{threshold}}" min="0" max="100" step="5" style="width:80px">
    <button type="submit" class="btn btn-d" style="padding:8px 14px">APPLY</button>
  </form>
</div>
<form method="POST" action="/warn" id="wf">
<div class="warn-layout">
  <div>
    {% if at_risk %}
    <div style="margin-bottom:10px;font-family:'Share Tech Mono',monospace;font-size:11px;color:var(--dim)">{{at_risk|length}} STUDENTS BELOW {{threshold}}pts AVG</div>
    <div style="display:flex;flex-direction:column;gap:10px">
    {% for s in at_risk %}
    <label class="risk-card" onclick="upd()">
      <input type="checkbox" name="students" value="{{s.name}}" style="display:none">
      <div class="risk-score {{'mid' if s.avg_score>=60}}">{{s.avg_score|int}}</div>
      <div style="flex:1">
        <div style="font-size:15px;font-weight:700">{{s.name}}</div>
        <div style="font-size:11px;color:var(--dim);font-family:'Share Tech Mono',monospace">{{s.email}}</div>
        <div style="font-size:11px;color:var(--dim);font-family:'Share Tech Mono',monospace">{{s.sessions}} sessions</div>
        <div class="bar-wrap" style="margin-top:7px"><div class="bar {{'y' if s.avg_score>=60 else 'r'}}" style="width:{{s.avg_score}}%"></div></div>
      </div>
    </label>
    {% endfor %}
    </div>
    {% else %}
    <div class="panel"><div class="pb" style="text-align:center;padding:52px;color:var(--green);font-family:'Share Tech Mono',monospace">
      <div style="font-size:36px;margin-bottom:12px">✓</div>ALL STUDENTS ABOVE {{threshold}}pts — NO WARNINGS NEEDED
    </div></div>
    {% endif %}
  </div>
  <div class="send-box">
    <div class="send-hdr"><div class="send-title">⚠ SEND WARNINGS</div>
    <div style="font-size:11px;color:var(--dim);font-family:'Share Tech Mono',monospace;margin-top:4px">Powered by SMTP (.env)</div></div>
    <div style="padding:22px">
      <div class="counter" id="cnt">0</div>
      <div class="c-lbl">STUDENTS SELECTED</div>
      <button type="button" class="sel-all" onclick="selAll()">SELECT ALL AT-RISK</button>
      <div class="fg"><label class="flbl">CUSTOM MESSAGE (OPTIONAL)</label>
        <textarea class="fi" name="custom_message" rows="4" placeholder="Extra note for students..." style="resize:vertical;min-height:80px"></textarea>
      </div>
      <input type="hidden" name="threshold" value="{{threshold}}">
      <button type="submit" class="send-big" id="sbtn" disabled><i class="fas fa-paper-plane"></i> &nbsp; SEND WARNINGS</button>
      <div class="note-box"><i class="fas fa-info-circle"></i> &nbsp; Configure SMTP settings in your <b>.env</b> file to enable automated alerts.</div>
    </div>
  </div>
</div>
</form>
{% endblock %}
{% block js %}
<script>
function upd(){
  setTimeout(()=>{
    const n=document.querySelectorAll('input[name="students"]:checked').length;
    document.getElementById('cnt').textContent=n;
    document.getElementById('sbtn').disabled=n===0;
    document.querySelectorAll('.risk-card').forEach(c=>{c.classList.toggle('sel',c.querySelector('input').checked);});
  },0);
}
function selAll(){document.querySelectorAll('input[name="students"]').forEach(c=>c.checked=true);upd();}
</script>
{% endblock %}
"""

# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    df      = load_attendance()
    scores  = compute_scores(df)
    sessions = session_summary(df)

    total_students = len(scores)
    total_sessions = df["SessionID"].nunique() if "SessionID" in df.columns else (df["Date"].nunique() if not df.empty else 0)

    on_time_pct  = round((df["Score"] == 100).mean() * 100, 1) if not df.empty else 0
    late_pct     = round((df["Score"] == 75).mean()  * 100, 1) if not df.empty else 0
    too_late_pct = round((df["Score"] == 50).mean()  * 100, 1) if not df.empty else 0
    miss_pct     = round((df["Score"] == 0).mean()   * 100, 1) if not df.empty else 0

    top = []
    if not scores.empty:
        for _, r in scores.sort_values("AvgScore", ascending=False).head(5).iterrows():
            top.append({"name": r["Name"], "sessions": int(r["Sessions"]), "avg_score": float(r["AvgScore"])})

    return render_template_string(DASHBOARD_HTML,
        page_title="Dashboard", topbar="DASHBOARD — OVERVIEW", active="dashboard",
        total_students=total_students, total_sessions=total_sessions,
        on_time_pct=on_time_pct, late_pct=late_pct, too_late_pct=too_late_pct, miss_pct=miss_pct,
        sessions=sessions, top=top)


@app.route("/records")
def records():
    import pandas as pd
    df = load_attendance()
    nf      = request.args.get("name", "").strip().upper()
    df_from = request.args.get("date_from", "")
    df_to   = request.args.get("date_to", "")
    sf      = request.args.get("score", "all")

    if nf:      df = df[df["Name"].str.upper().str.contains(nf)]
    if df_from: df = df[df["Date"] >= pd.to_datetime(df_from)]
    if df_to:   df = df[df["Date"] <= pd.to_datetime(df_to)]
    if sf in ("100","75","50","0"): df = df[df["Score"] == int(sf)]

    recs = [{"name":r["Name"],"email":r["Email"],
             "date":r["Date"].strftime("%Y-%m-%d") if hasattr(r["Date"],"strftime") else "N/A",
             "time":r["Time"],"score":int(r["Score"])}
            for _,r in df.iterrows()]

    return render_template_string(RECORDS_HTML,
        page_title="Records", topbar="ATTENDANCE — RECORDS", active="records",
        records=recs, f={"name": nf, "date_from": df_from, "date_to": df_to, "score": sf})


@app.route("/scores")
def scores():
    df    = load_attendance()
    sc_df = compute_scores(df)
    result = []
    for _, r in sc_df.iterrows():
        avg    = float(r["AvgScore"])
        status = "excellent" if avg >= 90 else "good" if avg >= 75 else "warning" if avg >= 50 else "danger"
        result.append({"name":r["Name"],"email":r["Email"],
                        "sessions":int(r["Sessions"]),"avg_score":round(avg,1),"status":status})
    result.sort(key=lambda x: x["avg_score"], reverse=True)
    return render_template_string(SCORES_HTML,
        page_title="Scores", topbar="SCORES — AVERAGES", active="scores", students=result)


@app.route("/warn", methods=["GET","POST"])
def warn():
    df        = load_attendance()
    scores_df = compute_scores(df)
    threshold = float(request.args.get("threshold", 75) if request.method=="GET"
                      else request.form.get("threshold", 75))

    if request.method == "POST":
        selected   = request.form.getlist("students")
        custom_msg = request.form.get("custom_message","")
        sent, failed = [], []
        for name in selected:
            row = scores_df[scores_df["Name"] == name]
            if row.empty: continue
            email = row.iloc[0]["Email"]
            avg   = float(row.iloc[0]["AvgScore"])
            ok = send_warning(name, email, avg, custom_msg) if email and email != "N/A" else False
            (sent if ok else failed).append(name if ok else f"{name} (no email)")
        if sent:   flash(f"✅ Sent to: {', '.join(sent)}", "success")
        if failed: flash(f"❌ Failed: {', '.join(failed)}", "error")
        return redirect(url_for("warn"))

    at_risk = []
    for _, r in scores_df.iterrows():
        if float(r["AvgScore"]) < threshold:
            at_risk.append({"name":r["Name"],"email":r["Email"],
                            "sessions":int(r["Sessions"]),"avg_score":round(float(r["AvgScore"]),1)})
    at_risk.sort(key=lambda x: x["avg_score"])

    return render_template_string(WARN_HTML,
        page_title="Warnings", topbar="WARNINGS — EMAIL ALERTS", active="warn",
        at_risk=at_risk, threshold=threshold)


# ── API ────────────────────────────────────────────────────────────────────────

@app.route("/api/dist")
def api_dist():
    df = load_attendance()
    if df.empty:
        return jsonify({"on_time":0,"late":0,"too_late":0,"miss":0})
    return jsonify({
        "on_time":  int((df["Score"]==100).sum()),
        "late":     int((df["Score"]==75).sum()),
        "too_late": int((df["Score"]==50).sum()),
        "miss":     int((df["Score"]==0).sum()),
    })


@app.route("/start-camera")
def start_camera():
    script = os.path.join(BASE_DIR, "attendance_engine.py")
    if os.path.exists(script):
        subprocess.Popen(["python", script])
        return jsonify({"status":"ok","message":"Camera session started!"})
    return jsonify({"status":"error","message":"attendance_engine.py not found"}), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)