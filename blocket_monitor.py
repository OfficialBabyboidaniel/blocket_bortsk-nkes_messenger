#!/usr/bin/env python3
"""Blocket Bortskänkes Monitor — posts new free listings to Telegram topics."""
import json, os, httpx, logging
from pathlib import Path
from datetime import datetime

LOG_FILE = Path(os.environ.get("DATA_DIR", "/data")) / "blocket_classify.log"
SEEN_FILE = Path(os.environ.get("DATA_DIR", "/data")) / "blocket_seen.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
log = logging.getLogger(__name__)

TOKEN    = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID  = os.environ.get("TELEGRAM_CHAT_ID", "")
API_BASE = "https://blocket-api.se/v1"
MAX_PAGES = 5

ALLOWED_AREAS = {
    "Danderyd","Djursholm","Enebyberg",
    "Järfälla","Kallhäll","Jakobsberg","Kungsängen",
    "Sollentuna","Häggvik","Tureberg","Edsberg",
    "Solna","Hagalund","Råsunda","Huvudsta",
    "Täby","Arninge","Viggbyholm","Roslags-Näsby",
    "Upplands Väsby","Väsby","Rotebro",
}

TOPICS = {
    "möbler":109,"bygg":110,"kök":111,"teknik":112,
    "fordon":113,"kläder":114,"barn":115,
    "trädgård":116,"hobby":117,"blandat":118,
}
TOPIC_NAMES = {v: k for k, v in TOPICS.items()}

KEYWORD_TOPIC = {
    # Specific compounds first to prevent false substring matches
    "studsmatta":116,"trampolin":116,   # before "matta" → kläder
    "ryamatta":114,"ryamattor":114,     # before generic "matta"
    "lampskärm":109,                    # before "skärm" → teknik
    # 109 möbler
    "soffa":109,"bäddsoffa":109,"soffgrupp":109,"soffbord":109,
    "stol":109,"stolar":109,"fåtölj":109,"fotölj":109,"fåtöljer":109,"barstol":109,"pall":109,"puff":109,
    "bord":109,"matbord":109,"skrivbord":109,"sidobord":109,"sängbord":109,
    "säng":109,"sängar":109,"sängram":109,"sänggavel":109,"våningssäng":109,"madrass":109,"bäddmadrass":109,
    "hylla":109,"hyllor":109,"bokhylla":109,"skohylla":109,"skoskåp":109,"skoförvaring":109,
    "garderob":109,"skåp":109,"klädskåp":109,"byrå":109,"chiffonier":109,"sekretär":109,"kommod":109,"vitrinskåp":109,
    "möbel":109,"möbler":109,"inredning":109,"hallbänk":109,"hallmöbel":109,"tv-bänk":109,"tvbänk":109,"tv bänk":109,
    "lampa":109,"lampor":109,"belysning":109,"taklampa":109,"golvlampa":109,"bordslampa":109,
    "spegel":109,"speglar":109,"tavla":109,"tavlor":109,"anslagstavla":109,
    "kudde":109,"kuddar":109,"dyna":109,"dynor":109,
    "klädhängare":109,"klädstång":109,"klädkrok":109,
    "bestå":109,"kallax":109,"billy":109,"brimnes":109,"nevada":109,"resårbotten":109,"poäng":109,"hemnes":109,"malm":109,"brusali":109,
    "markis":109,
    # 110 bygg
    "dörr":110,"dörrar":110,"fönster":110,"fönsterbåge":110,"dörrkar":110,"karm":110,
    "parkett":110,"golv":110,"golvbräda":110,"laminat":110,"klinker":110,
    "kakel":110,"köksstomme":110,"kökslucka":110,"köksluckor":110,
    "isolering":110,"gipsskiva":110,"gips":110,
    "betong":110,"virke":110,"träplank":110,"byggmaterial":110,
    "skruv":110,"spik":110,"verktyg":110,"borr":110,"såg":110,"hammare":110,
    "badkar":110,"badrum":110,"badrumsmöbel":110,"badrumsinredning":110,"toalett":110,
    "tvättmaskin":110,"torktumlare":110,"element":110,"radiator":110,"elpanna":110,"varmvattenberedare":110,"värmepump":110,
    "panel":110,"list":110,"täcklist":110,
    "fyllnadsmassor":110,"bärlager":110,"ballingslöv":110,"stommar":110,
    # 111 kök
    "kyl":111,"kylskåp":111,"frys":111,"frysskåp":111,"kylfrys":111,
    "spis":111,"ugn":111,"mikro":111,"mikrovåg":111,"diskmaskin":111,
    "köksfläkt":111,"köksfläktar":111,
    "köksmaskin":111,"mixer":111,"blender":111,
    "kastrull":111,"kastruller":111,"stekpanna":111,"köksredskap":111,
    "glas":111,"glasvaror":111,"porslin":111,"tallrik":111,"tallrikar":111,"mugg":111,"kanna":111,
    "bestick":111,"kniv":111,"knivar":111,"skärbräda":111,
    "kaffebryggare":111,"kaffemaskin":111,"vattenkokare":111,
    "diskbänk":111,"bänkskiva":111,"inbyggd":111,"vitvaror":111,
    # 112 teknik
    "tv":112,"dator":112,"laptop":112,"bärbar":112,"surfplatta":112,"ipad":112,
    "television":112,"bildskärm":112,"monitor":112,
    "telefon":112,"mobil":112,"smartphone":112,"iphone":112,"samsung":112,
    "kamera":112,"kameror":112,"objektiv":112,"gopro":112,
    "hörlurar":112,"högtalare":112,"soundbar":112,"receiver":112,"förstärkare":112,
    "router":112,"hdd":112,"ssd":112,
    "konsol":112,"playstation":112,"xbox":112,"nintendo":112,
    "skrivare":112,"projektor":112,"lysrör":112,"toner":112,"bläckpatron":112,
    "bravia":112,
    # 113 fordon
    "cykel":113,"cyklar":113,"elcykel":113,"mountainbike":113,"mtb":113,"racercykel":113,
    "barnvagn":113,"barnvagnar":113,"sittvagn":113,"liggvagn":113,"bugaboo":113,
    "moped":113,"motorcykel":113,"scooter":113,
    "elsparkcykel":113,"sparkcykel":113,"kickbike":113,
    "husvagn":113,"släpvagn":113,"trailer":113,
    "skidor":113,"snowboard":113,"skridskor":113,
    "traktorvagn":113,
    # 114 kläder
    "jacka":114,"jackor":114,"kappa":114,"kappor":114,
    "kläder":114,"klänning":114,"byxor":114,"jeans":114,"tröja":114,"skjorta":114,"kjol":114,
    "skor":114,"stövlar":114,"sneakers":114,"sandaler":114,
    "väska":114,"väskor":114,"ryggsäck":114,"handväska":114,
    "textil":114,"tyg":114,"gardin":114,"gardiner":114,"matta":114,"mattor":114,
    "påslakan":114,"lakan":114,"handduk":114,"handdukar":114,
    "halsduk":114,"mössa":114,"handskar":114,
    # 115 barn
    "leksak":115,"leksaker":115,"pussel":115,"byggklossar":115,"duplo":115,"lego":115,
    "barnkläder":115,"babykläder":115,"barnsko":115,"barnskor":115,
    "barnsäng":115,"spjälsäng":115,"vagga":115,
    "bilbarnstol":115,"barnstol":115,"nappflaska":115,"babygym":115,
    "barnbok":115,"barnböcker":115,
    "lektunnel":115,"lekstuga":115,"gunghäst":115,"gunga":115,"sandlåda":115,"lekhage":115,
    "dockhus":115,"dockvagn":115,"barnmöbel":115,
    "crib":115,"bedside":115,
    # 116 trädgård
    "trädgård":116,"trädgårdsverktyg":116,
    "kruka":116,"krukor":116,"blomkruka":116,"plastkruka":116,"plastkrukor":116,
    "utemöbel":116,"utemöbler":116,"trädgårdsmöbel":116,
    "gräsklippare":116,"häcktrimmer":116,"spade":116,
    "blomma":116,"blommor":116,"växt":116,"växter":116,
    "pergola":116,"växthus":116,"uteplats":116,"solstol":116,"loungemöbel":116,
    "sten":116,"stenar":116,"marksten":116,"sjösten":116,"betongplatta":116,
    "grus":116,"jord":116,"planteringsjord":116,"bark":116,
    "gran":116,"elefantgräs":116,"lecakulor":116,"förodlingslåda":116,"förodling":116,
    "grill":116,"gasolgrill":116,"weber":116,"grillkol":116,
    "ved":116,"hö":116,"halm":116,
    "trädgårdsslang":116,"spabad":116,"pool":116,
    # 117 hobby
    "bok":117,"böcker":117,"roman":117,"tidning":117,
    "sport":117,"träning":117,"yogamatta":117,"hantlar":117,"ishockeymål":117,
    "musik":117,"gitarr":117,"piano":117,"orgel":117,"keyboard":117,"trummor":117,"instrument":117,
    "brädspel":117,"sällskapsspel":117,"kortspel":117,
    "fiske":117,"fiskespö":117,"camping":117,"tält":117,
    "symaskin":117,"broderi":117,"stickning":117,"konst":117,"målning":117,
    "akvarium":117,"terrarium":117,"kattlåda":117,"hundfoder":117,"kattfoder":117,"hundmat":117,
    "hundbur":117,"kattbur":117,"hamster":117,"kanin":117,"marsvin":117,"husdjur":117,"torrfoder":117,
    "samlarföremål":117,"figurin":117,"antik":117,"antikvitet":117,"retro":117,"vintage":117,
    "bildram":117,"tavelram":117,
    "strykbräda":117,"korg":117,"korgar":117,
}

SEARCHES = [
    {"query": "bortskänkes",           "max_price": 0,   "filter_area": True},
    {"query": "bortskänkes barstolar", "max_price": 0,   "filter_area": False},
    {"query": "gratis",                "max_price": 100, "filter_area": True},
    {"query": "fåtölj",                "max_price": 0,   "filter_area": True},
]

def in_area(location):
    return any(area.lower() in location.lower() for area in ALLOWED_AREAS)

def keyword_thread(title):
    import re as _re
    _WORD_BOUNDARY = {"tv", "mc", "pc", "pool", "gran", "sony"}
    t = title.lower()
    for kw, tid in KEYWORD_TOPIC.items():
        if kw in _WORD_BOUNDARY:
            if _re.search(r"\b" + _re.escape(kw) + r"\b", t):
                return tid, kw
        else:
            if kw in t:
                return tid, kw
    return None, None

def load_seen():
    return set(json.loads(SEEN_FILE.read_text())) if SEEN_FILE.exists() else set()

def save_seen(seen):
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    SEEN_FILE.write_text(json.dumps(list(seen)))

def send(text, thread_id):
    if not TOKEN or not CHAT_ID:
        log.warning("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set — skipping send")
        return
    try:
        httpx.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "message_thread_id": thread_id, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
    except Exception as e:
        log.error(f"Telegram send error: {e}")

def fetch_pages(query, max_price, filter_area):
    results = []
    for page in range(1, MAX_PAGES + 1):
        try:
            r = httpx.get(
                f"{API_BASE}/search",
                params={"query": query, "sort_order": "PUBLISHED_DESC", "page": page},
                timeout=15,
            )
            data = r.json()
            for d in data.get("docs", []):
                price = d.get("price", {}).get("amount", 999)
                if price > max_price:
                    continue
                if filter_area and not in_area(d.get("location", "")):
                    continue
                results.append(d)
            paging = data.get("metadata", {}).get("paging", {})
            if page >= paging.get("last", 1):
                break
        except Exception as e:
            log.error(f"Fetch page {page}: {e}")
            break
    return results

def main():
    seen = load_seen()
    new_items = []

    for s in SEARCHES:
        items = fetch_pages(s["query"], s.get("max_price", 0), s.get("filter_area", True))
        for item in items:
            aid = str(item["id"])
            if aid in seen:
                continue
            seen.add(aid)
            new_items.append(item)

    if not new_items:
        log.info("No new items.")
        save_seen(seen)
        return

    log.info(f"--- {datetime.now().strftime('%Y-%m-%d %H:%M')} | {len(new_items)} new items ---")
    for item in new_items:
        title    = item.get("heading", "?")
        location = item.get("location", "?")
        url      = item.get("canonical_url", "")
        price    = item.get("price", {}).get("amount", 0)
        price_str = "Gratis" if price == 0 else f"{price} kr"

        tid, kw = keyword_thread(title)
        thread = tid if tid is not None else 118  # fallback: blandat
        category = TOPIC_NAMES.get(thread, "blandat")

        log.info(f"[{category}] kw={kw} | {title} | {location}")
        send(f"🆕 <b>{title}</b>\n💰 {price_str}\n📍 {location}\n🔗 {url}", thread)

    save_seen(seen)
    log.info(f"✅ Done. {len(new_items)} sent.")

if __name__ == "__main__":
    main()
