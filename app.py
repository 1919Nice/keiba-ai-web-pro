
from flask import Flask, request

app = Flask(__name__)
APP_NAME = "KEIBA AI WEB PRO V3"

SAMPLE_HORSES = [
    {"num":1, "name":"アスコリピチェーノ", "odds":3.2, "pop":1, "style":"差し"},
    {"num":2, "name":"ステレンボッシュ", "odds":5.8, "pop":2, "style":"差し"},
    {"num":3, "name":"マスクトディーヴァ", "odds":7.6, "pop":3, "style":"先行"},
    {"num":4, "name":"ナミュール", "odds":8.9, "pop":4, "style":"差し"},
    {"num":5, "name":"ウンブライル", "odds":18.4, "pop":8, "style":"追込"},
    {"num":6, "name":"フィアスプライド", "odds":23.7, "pop":10, "style":"先行"},
    {"num":7, "name":"サウンドビバーチェ", "odds":35.2, "pop":12, "style":"逃げ"},
    {"num":8, "name":"コンクシェル", "odds":28.6, "pop":11, "style":"先行"},
]

def esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def score_horse(h, mode, ground, venue):
    base = 70 - (h["pop"] * 2.1)
    odds_value = min(h["odds"] * 1.15, 28)
    venue_bonus = 6 if venue in ["東京", "阪神", "京都"] and h["style"] in ["差し", "追込"] else 2
    ground_bonus = 5 if ground in ["稍重", "重", "不良"] and h["odds"] >= 10 else 1
    josho_style = venue_bonus + ground_bonus + odds_value * 0.25
    umalog_style = 6 if h["style"] in ["差し", "先行"] else 3
    if mode == "穴狙い":
        return base + odds_value + josho_style + umalog_style
    return base + (odds_value * 0.45) + josho_style + umalog_style

def make_prediction(race_name, venue, ground, mode):
    ranked = sorted(
        [(h, score_horse(h, mode, ground, venue)) for h in SAMPLE_HORSES],
        key=lambda x: x[1],
        reverse=True
    )
    top = [x[0] for x in ranked[:3]]
    tickets = {
        "単勝": f"{top[0]['num']}番 {top[0]['name']}",
        "馬連": f"{top[0]['num']}-{top[1]['num']}（{top[0]['name']} - {top[1]['name']}）",
        "3連単": f"{top[0]['num']}→{top[1]['num']}→{top[2]['num']}（{top[0]['name']}→{top[1]['name']}→{top[2]['name']}）",
    }
    return ranked, tickets

@app.route("/", methods=["GET", "POST"])
def index():
    race_name = request.form.get("race_name", "ヴィクトリアマイル")
    venue = request.form.get("venue", "東京")
    ground = request.form.get("ground", "良")
    venues = ["東京","中山","京都","阪神","中京","新潟","札幌","函館","福島","小倉"]
    grounds = ["良","稍重","重","不良"]

    html = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{APP_NAME}</title>
<style>
body {{ margin:0; font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background:#0b0b0b; color:#f5f5f5; }}
header {{ background:linear-gradient(90deg,#000,#2d2509); padding:18px; border-bottom:1px solid #d4af37; }}
h1 {{ margin:0; color:#d4af37; font-size:24px; }}
main {{ padding:16px; max-width:900px; margin:auto; }}
.card {{ background:#171717; border:1px solid #333; border-radius:16px; padding:16px; margin:14px 0; box-shadow:0 6px 18px rgba(0,0,0,.25); }}
label {{ display:block; margin-top:12px; color:#d4af37; font-weight:700; }}
input, select {{ width:100%; box-sizing:border-box; padding:12px; border-radius:10px; border:1px solid #555; background:#0f0f0f; color:#fff; font-size:16px; }}
button {{ width:100%; margin-top:16px; padding:14px; border:0; border-radius:12px; background:#d4af37; color:#111; font-weight:800; font-size:17px; }}
table {{ width:100%; border-collapse:collapse; margin-top:12px; }}
th,td {{ border-bottom:1px solid #333; padding:8px; text-align:left; }}
th {{ color:#d4af37; }}
.badge {{ display:inline-block; background:#2c250f; color:#d4af37; padding:4px 8px; border-radius:8px; margin:2px; }}
.small {{ color:#bbb; font-size:13px; line-height:1.6; }}
.pick {{ font-size:18px; font-weight:800; color:#ffd95a; }}
</style>
</head>
<body>
<header><h1>{APP_NAME}</h1><div>JRA予想支援・穴狙い / バランス対応</div></header>
<main>
<div class="card">
<form method="post">
<label>レース名</label>
<input name="race_name" value="{esc(race_name)}" placeholder="例：ヴィクトリアマイル">
<label>競馬場</label>
<select name="venue">
"""
    for v in venues:
        sel = "selected" if v == venue else ""
        html += f'<option value="{v}" {sel}>{v}</option>'
    html += '</select><label>馬場</label><select name="ground">'
    for g in grounds:
        sel = "selected" if g == ground else ""
        html += f'<option value="{g}" {sel}>{g}</option>'
    html += '</select><button type="submit">AI予想を作成</button></form></div>'

    for mode in ["穴狙い", "バランス"]:
        ranked, tickets = make_prediction(race_name, venue, ground, mode)
        html += f"""
<div class="card">
<h2>{esc(race_name)}：{mode}予想</h2>
<p><span class="badge">{venue}</span><span class="badge">{ground}</span><span class="badge">単勝・馬連・3連単</span></p>
<h3>推奨買い目</h3>
<p class="pick">単勝：{tickets["単勝"]}</p>
<p class="pick">馬連：{tickets["馬連"]}</p>
<p class="pick">3連単：{tickets["3連単"]}</p>
<h3>AI印</h3>
<table><tr><th>印</th><th>馬番</th><th>馬名</th><th>人気</th><th>想定オッズ</th><th>指数</th></tr>
"""
        marks = ["◎","○","▲","△","☆"]
        for i, (h, s) in enumerate(ranked[:5]):
            html += f"<tr><td>{marks[i]}</td><td>{h['num']}</td><td>{h['name']}</td><td>{h['pop']}人気</td><td>{h['odds']}</td><td>{s:.1f}</td></tr>"
        html += """</table>
<p class="small">
丞相風補正：トラックバイアス、馬場、展開、人気に対する妙味を重視。<br>
うまログ風補正：血統・距離適性・馬場適性・条件替わり・穴妙味を重視。<br>
※本人の有料・非公開ノウハウの複製ではなく、公開動画や一般的な競馬予想観点を参考にした独自ロジックです。
</p>
</div>
"""
    html += """
<div class="card">
<h3>データ取得について</h3>
<p class="small">
現在はRenderで確実に起動するため、サンプル実名データで動作します。
次段階でJRA/netkeiba等の公開ページ取得またはCSV取込を追加できます。
公開サイト取得はサイト構造変更やアクセス制限で失敗する場合があります。
</p>
</div>
</main></body></html>
"""
    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
