
from __future__ import annotations

import re
import random
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional

import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request

APP_NAME = "KEIBA AI WEB PRO V2"

app = Flask(__name__)


@dataclass
class Horse:
    number: int
    frame: int
    name: str
    jockey: str = "取得待ち"
    trainer: str = "取得待ち"
    age: str = "取得待ち"
    weight: str = "取得待ち"
    odds: float = 0.0
    popularity: int = 0
    father: str = "取得待ち"
    mother: str = "取得待ち"
    damsire: str = "取得待ち"
    last_runs_score: float = 50.0
    course_score: float = 50.0
    venue_score: float = 50.0
    ground_score: float = 50.0
    distance_score: float = 50.0
    jockey_score: float = 50.0
    trainer_score: float = 50.0
    workout_score: float = 50.0
    paddock_score: float = 50.0
    return_horse_score: float = 50.0
    pace_fit_score: float = 50.0
    bias_score: float = 50.0
    blood_score: float = 50.0


@dataclass
class RaceData:
    race_name: str
    venue: str
    course: str
    ground: str
    distance: str
    weather: str
    horses: List[Horse]
    source_note: str


JRA_VENUES = ["東京", "中山", "京都", "阪神", "中京", "新潟", "札幌", "函館", "福島", "小倉"]


def _safe_float(text: str) -> float:
    m = re.search(r"\d+(?:\.\d+)?", text or "")
    return float(m.group()) if m else 0.0


def fetch_from_netkeiba_like_url(url: str, race_name: str) -> Optional[RaceData]:
    """公開HTMLから取れる範囲だけ抽出する簡易取得器。
    サイト側の構造変更やアクセス制限で失敗する場合があります。
    """
    if not url:
        return None
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 KEIBA-AI-WEB-PRO-V2 personal research tool"
        }
        res = requests.get(url, headers=headers, timeout=12)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text("\n", strip=True)

        title = race_name or (soup.title.get_text(strip=True) if soup.title else "取得レース")
        venue = next((v for v in JRA_VENUES if v in text), "取得待ち")
        ground = "重" if "重" in text else "稍重" if "稍重" in text else "不良" if "不良" in text else "良"
        weather = "取得待ち"
        distance = "取得待ち"
        course = "取得待ち"

        dist_match = re.search(r"(芝|ダート|ダ)\s*(\d{3,4})m", text)
        if dist_match:
            course = "芝" if dist_match.group(1) == "芝" else "ダート"
            distance = f"{dist_match.group(2)}m"

        horses: List[Horse] = []

        # netkeibaの出馬表に近いテーブル構造を広めに拾う
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            if len(rows) < 5:
                continue
            for row in rows:
                cells = [c.get_text(" ", strip=True) for c in row.find_all(["td", "th"])]
                joined = " ".join(cells)
                # 馬番＋馬名らしき日本語/英数を検出
                if len(cells) >= 4:
                    nums = [int(x) for x in re.findall(r"(?<!\d)([1-9]|1[0-8])(?!\d)", joined)]
                    horse_links = [a.get_text(strip=True) for a in row.find_all("a") if len(a.get_text(strip=True)) >= 2]
                    candidates = [h for h in horse_links if not re.search(r"騎手|調教師|厩舎|馬主", h)]
                    if nums and candidates:
                        num = nums[0]
                        name = candidates[0]
                        if not any(h.number == num or h.name == name for h in horses):
                            odds = 0.0
                            pop = 0
                            for c in cells:
                                if re.fullmatch(r"\d+\.\d+", c):
                                    odds = float(c)
                                if re.fullmatch(r"\d+人気", c):
                                    pop = int(c.replace("人気", ""))
                            horses.append(Horse(
                                number=num,
                                frame=max(1, min(8, (num + 1)//2)),
                                name=name,
                                odds=odds,
                                popularity=pop
                            ))
                if len(horses) >= 18:
                    break
            if len(horses) >= 5:
                break

        if len(horses) >= 3:
            return RaceData(
                race_name=title[:60],
                venue=venue,
                course=course,
                ground=ground,
                distance=distance,
                weather=weather,
                horses=sorted(horses, key=lambda h: h.number),
                source_note="公開ページから取得しました。取得精度はページ構造に依存します。"
            )
    except Exception as e:
        return None
    return None


def demo_race(race_name: str, venue: str) -> RaceData:
    # 実データ取得失敗時にも動作確認できるサンプル。アプリの予想ロジック検証用。
    names = [
        "サンプルスター", "ゴールドライン", "ミラクルマイル", "ブラックバイアス",
        "ラストスパート", "フォースブラッド", "ディープコース", "ワイドキング",
        "トラックセンス", "オッズハンター", "パドッククイーン", "テンハヤテ"
    ]
    horses = []
    for i, name in enumerate(names, start=1):
        odds = round([2.8, 4.5, 6.2, 9.8, 13.4, 18.6, 23.1, 31.5, 42.0, 55.0, 68.0, 88.0][i-1], 1)
        horses.append(Horse(
            number=i,
            frame=max(1, min(8, (i+1)//2)),
            name=name,
            jockey=random.choice(["川田", "ルメール", "横山武", "戸崎", "武豊", "坂井", "松山"]),
            trainer=random.choice(["国枝", "友道", "矢作", "手塚", "中内田", "木村"]),
            age=random.choice(["牡4", "牝4", "牡5", "牝5"]),
            weight=random.choice(["55.0", "56.0", "57.0", "58.0"]),
            odds=odds,
            popularity=i,
            father=random.choice(["ディープ系", "キングマンボ系", "ロベルト系", "サンデー系"]),
            mother="母系取得待ち",
            damsire=random.choice(["Storm Cat系", "Roberto系", "Danzig系"]),
            last_runs_score=random.uniform(45, 85),
            course_score=random.uniform(45, 90),
            venue_score=random.uniform(45, 90),
            ground_score=random.uniform(45, 90),
            distance_score=random.uniform(45, 90),
            jockey_score=random.uniform(45, 90),
            trainer_score=random.uniform(45, 90),
            workout_score=random.uniform(45, 90),
            paddock_score=random.uniform(45, 90),
            return_horse_score=random.uniform(45, 90),
            pace_fit_score=random.uniform(45, 90),
            bias_score=random.uniform(45, 90),
            blood_score=random.uniform(45, 90),
        ))
    return RaceData(
        race_name=race_name or "サンプル重賞",
        venue=venue or "東京",
        course="芝",
        ground="良",
        distance="1600m",
        weather="晴",
        horses=horses,
        source_note="実データ取得に失敗したため、動作確認用サンプルで表示しています。実運用ではレースURLまたは正規データ連携を設定してください。"
    )


def enrich_scores(h: Horse, race: RaceData) -> Dict[str, float]:
    # 今まで決めた収集データを指数化
    base = (
        h.last_runs_score * 0.14 +
        h.course_score * 0.10 +
        h.venue_score * 0.10 +
        h.ground_score * 0.08 +
        h.distance_score * 0.08 +
        h.jockey_score * 0.08 +
        h.trainer_score * 0.08 +
        h.workout_score * 0.08 +
        h.paddock_score * 0.08 +
        h.return_horse_score * 0.06 +
        h.pace_fit_score * 0.06 +
        h.blood_score * 0.06
    )

    # 丞相風：トラックバイアス・展開・馬場・買い目の期待値を強調
    josho_style = (
        h.bias_score * 0.32 +
        h.pace_fit_score * 0.24 +
        h.course_score * 0.18 +
        h.ground_score * 0.14 +
        value_score(h) * 0.12
    )

    # うまログ風：血統・条件替わり・距離/馬場適性・穴妙味を強調
    umalog_style = (
        h.blood_score * 0.34 +
        h.distance_score * 0.20 +
        h.ground_score * 0.16 +
        h.venue_score * 0.12 +
        longshot_boost(h) * 0.18
    )

    balanced = base * 0.70 + josho_style * 0.15 + umalog_style * 0.15
    ana = base * 0.42 + josho_style * 0.25 + umalog_style * 0.23 + longshot_boost(h) * 0.10

    return {
        "base": round(base, 1),
        "josho": round(josho_style, 1),
        "umalog": round(umalog_style, 1),
        "balanced": round(balanced, 1),
        "ana": round(ana, 1),
        "value": round(value_score(h), 1),
    }


def value_score(h: Horse) -> float:
    if h.odds <= 0:
        return 55
    # 期待値。過剰人気は少し下げ、妙味ある中穴を上げる。
    if 6 <= h.odds <= 25:
        return 82
    if 25 < h.odds <= 60:
        return 72
    if h.odds < 3:
        return 52
    return 60


def longshot_boost(h: Horse) -> float:
    if h.popularity >= 7 or h.odds >= 15:
        return 88
    if h.popularity >= 4 or h.odds >= 7:
        return 72
    return 50


def marks(ranked: List[Tuple[Horse, Dict[str, float]]], mode: str) -> Dict[int, str]:
    symbols = ["◎", "○", "▲", "△", "☆"]
    result = {}
    for i, (h, _) in enumerate(ranked[:5]):
        result[h.number] = symbols[i]
    # 危険人気馬/消し
    for h, s in ranked:
        if h.popularity in (1, 2) and s[mode] < 62:
            result[h.number] = "×"
        elif s[mode] < 50:
            result[h.number] = "消"
    return result


def make_tickets(ranked: List[Tuple[Horse, Dict[str, float]]], mode: str) -> Dict[str, List[str]]:
    top = [h for h, _ in ranked[:5]]
    if len(top) < 3:
        return {"単勝": [], "馬連": [], "3連単": []}
    if mode == "ana":
        win = [f"{top[2].number} {top[2].name}", f"{top[4].number} {top[4].name}"]
        umaren = [
            f"{top[2].number}-{top[0].number}",
            f"{top[4].number}-{top[0].number}",
            f"{top[2].number}-{top[1].number}",
        ]
        trifecta = [
            f"{top[2].number} → {top[0].number},{top[1].number} → {top[0].number},{top[1].number},{top[3].number},{top[4].number}",
            f"{top[4].number} → {top[0].number},{top[2].number} → {top[0].number},{top[1].number},{top[2].number},{top[3].number}",
        ]
    else:
        win = [f"{top[0].number} {top[0].name}"]
        umaren = [
            f"{top[0].number}-{top[1].number}",
            f"{top[0].number}-{top[2].number}",
            f"{top[1].number}-{top[2].number}",
        ]
        trifecta = [
            f"{top[0].number} → {top[1].number},{top[2].number} → {top[1].number},{top[2].number},{top[3].number}",
            f"{top[1].number} → {top[0].number} → {top[2].number},{top[3].number}",
        ]
    return {"単勝": win, "馬連": umaren, "3連単": trifecta}


def analyze(race: RaceData):
    rows = []
    for h in race.horses:
        rows.append((h, enrich_scores(h, race)))
    balanced_rank = sorted(rows, key=lambda x: x[1]["balanced"], reverse=True)
    ana_rank = sorted(rows, key=lambda x: x[1]["ana"], reverse=True)
    return {
        "rows": rows,
        "balanced_rank": balanced_rank,
        "ana_rank": ana_rank,
        "balanced_marks": marks(balanced_rank, "balanced"),
        "ana_marks": marks(ana_rank, "ana"),
        "balanced_tickets": make_tickets(balanced_rank, "balanced"),
        "ana_tickets": make_tickets(ana_rank, "ana"),
    }


@app.route("/", methods=["GET", "POST"])
def index():
    race = None
    analysis = None
    if request.method == "POST":
        race_name = request.form.get("race_name", "").strip()
        venue = request.form.get("venue", "東京")
        url = request.form.get("source_url", "").strip()
        race = fetch_from_netkeiba_like_url(url, race_name) or demo_race(race_name, venue)
        analysis = analyze(race)
    return render_template("index.html", app_name=APP_NAME, venues=JRA_VENUES, race=race, analysis=analysis)


if __name__ == "__main__":
    app.run(debug=True)
