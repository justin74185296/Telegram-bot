"""
This bot is provided strictly for private programming study, data-structure research,
and offline fuzzy-matching experiments. Do NOT deploy publicly or use it to facilitate
any real-world transactions or services.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from fuzzywuzzy import fuzz

from .database import LocationRecord


router = Router()

# Fuzzy match threshold (explicit requirement)
FUZZY_THRESHOLD = 70

# Keep a tiny in-memory session of the most recent search results per user.
# This is intentionally ephemeral (no persistence).
_user_last_results: Dict[int, List[LocationRecord]] = {}


@dataclass(frozen=True)
class ScoredRecord:
    record: LocationRecord
    score: int
    best_field: str


def _score_record(query: str, rec: LocationRecord) -> ScoredRecord:
    """
    Score a record against user query using fuzzywuzzy ratios.

    Priority rule:
    - sub_area > area > city > country

    Implementation:
    - Compute ratio per field and apply weights.
    - Use the maximum weighted score as the record's final score.
    """

    q = query.strip().lower()
    if not q:
        return ScoredRecord(rec, 0, "none")

    # Per-field fuzzy ratios (0..100)
    r_sub = fuzz.token_set_ratio(q, (rec.sub_area or "").lower())
    r_area = fuzz.token_set_ratio(q, (rec.area or "").lower())
    r_city = fuzz.token_set_ratio(q, (rec.city or "").lower())
    r_country = fuzz.token_set_ratio(q, (rec.country or "").lower())

    # Weights encode the requested priority
    candidates: List[Tuple[str, int]] = [
        ("sub_area", int(round(r_sub * 1.30))),
        ("area", int(round(r_area * 1.20))),
        ("city", int(round(r_city * 1.10))),
        ("country", int(round(r_country * 1.00))),
    ]

    best_field, best_score = max(candidates, key=lambda x: x[1])
    best_score = min(best_score, 100)

    # Tie-break hint: if query matches any of the combined blob well,
    # give a small bonus (still capped at 100).
    blob_ratio = fuzz.token_set_ratio(q, rec.to_search_blob())
    if blob_ratio >= 85:
        best_score = min(100, best_score + 3)

    return ScoredRecord(rec, best_score, best_field)


def _rank_and_filter(query: str, records: List[LocationRecord]) -> List[ScoredRecord]:
    """
    Rank records by:
    1) fuzzy score desc (>=70)
    2) presence of tg_contacts desc (if scores are close)
    3) specificity (sub_area/area present) desc
    """

    scored = [_score_record(query, r) for r in records]
    scored = [s for s in scored if s.score >= FUZZY_THRESHOLD]

    def _specificity(rec: LocationRecord) -> int:
        return int(bool(rec.sub_area)) + int(bool(rec.area)) + int(bool(rec.nickname))

    # “If similarity is close, prefer records with tg_contacts”
    # We implement it by adding a small tie-breaker weight for tg_contacts.
    scored.sort(
        key=lambda s: (
            s.score,
            1 if s.record.tg_contacts else 0,
            _specificity(s.record),
        ),
        reverse=True,
    )
    return scored


def _format_compact_line(idx: int, s: ScoredRecord) -> str:
    """Compact line for search result list (Markdown)."""

    r = s.record
    place = " / ".join(p for p in [r.country, r.city, r.area, r.sub_area] if p)
    nick = f" — *{r.nickname}*" if r.nickname else ""
    tg_hint = " — **TG**" if r.tg_contacts else ""
    return f"{idx}. **{place}**{nick}{tg_hint} (score {s.score})"


def _format_detail(r: LocationRecord) -> str:
    """Detailed Markdown output (forces TG field display)."""

    lines = []
    if r.nickname:
        lines.append(f"**暱稱/代號**：{r.nickname}")
    lines.append(f"**國家**：{r.country or '-'}")
    lines.append(f"**城市**：{r.city or '-'}")
    lines.append(f"**區域**：{r.area or '-'}")
    lines.append(f"**子區域**：{r.sub_area or '-'}")
    lines.append(f"**位置描述**：{r.address_detail or '-'}")
    lines.append(f"**類型/標籤**：{', '.join(r.services) if r.services else '-'}")
    lines.append(f"**價格區間（估計）**：{r.price_range or '-'}")
    # Force TG field presence in response
    if r.tg_contacts:
        lines.append("**Telegram（公開連結/帳號，研究用）**：\n- " + "\n- ".join(r.tg_contacts))
    else:
        lines.append("**Telegram（公開連結/帳號，研究用）**：-")
    if r.notes:
        lines.append(f"**備註**：{r.notes}")
    if r.last_update:
        lines.append(f"**資料更新**：{r.last_update}")
    return "\n".join(lines)


def _make_results_keyboard(count: int) -> InlineKeyboardMarkup:
    """Inline keyboard for selecting one of the current results."""

    rows: List[List[InlineKeyboardButton]] = []

    # Detail buttons (1..count)
    row: List[InlineKeyboardButton] = []
    for i in range(1, count + 1):
        row.append(InlineKeyboardButton(text=f"查看詳細 #{i}", callback_data=f"pick:{i}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    # Region filters (simple, based on country->continent heuristics in JSON notes/tags)
    rows.append(
        [
            InlineKeyboardButton(text="更多亞洲", callback_data="more:asia"),
            InlineKeyboardButton(text="更多歐洲", callback_data="more:europe"),
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(text="更多美洲", callback_data="more:americas"),
            InlineKeyboardButton(text="更多其他", callback_data="more:other"),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _continent_of(record: LocationRecord) -> str:
    """Best-effort continent mapping by country (static heuristic; no network)."""

    c = (record.country or "").lower()
    asia = {
        "taiwan",
        "japan",
        "thailand",
        "vietnam",
        "singapore",
        "philippines",
        "malaysia",
        "indonesia",
        "south korea",
        "hong kong",
        "china",
        "india",
        "united arab emirates",
        "turkey",
    }
    europe = {
        "netherlands",
        "germany",
        "belgium",
        "czech republic",
        "france",
        "spain",
        "united kingdom",
        "switzerland",
        "portugal",
        "sweden",
        "austria",
        "italy",
        "poland",
        "greece",
        "denmark",
        "ireland",
        "hungary",
    }
    americas = {
        "united states",
        "canada",
        "mexico",
        "brazil",
        "colombia",
        "argentina",
        "chile",
        "peru",
    }
    africa = {"south africa", "kenya", "morocco", "egypt", "nigeria", "tanzania"}
    oceania = {"australia", "new zealand"}

    if c in asia:
        return "asia"
    if c in europe:
        return "europe"
    if c in americas:
        return "americas"
    if c in africa or c in oceania:
        return "other"
    return "other"


@router.message(Command("start"))
async def on_start(message: Message) -> None:
    """Welcome message with examples."""

    text = (
        "歡迎！這是一個**離線靜態資料**的地點模糊匹配 Bot（研究/學習用）。\n\n"
        "你可以輸入地點關鍵字（多語言可混用），例如：\n"
        "- `Amsterdam Canal Belt`\n"
        "- `Tokyo Shibuya Center Gai`\n"
        "- `Bangkok Sukhumvit Soi 11`\n"
        "- `Singapore Clarke Quay`\n\n"
        "我會在本機 JSON 資料庫中以 **70%** 門檻做模糊匹配，顯示前 3–6 個結果並提供按鈕查看詳細。"
    )
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("help"))
async def on_help(message: Message) -> None:
    """Help text and data disclaimer."""

    text = (
        "**指令**\n"
        "- `/start`：開始使用\n"
        "- `/help`：顯示說明\n\n"
        "**資料說明**\n"
        "- 資料完全來自 `data/global_locations.json`（靜態範例），不做任何網路請求。\n"
        "- 內容用於資料結構研究與比對實驗；`tg_contacts` 欄位若存在，僅示範如何顯示公開 Telegram 連結/帳號。\n\n"
        "**輸入建議**\n"
        "- 盡量輸入「城市 + 區域/子區域」以提高命中率，例如：`Tokyo Shibuya`。"
    )
    await message.answer(text, parse_mode="Markdown")


@router.message(F.text)
async def on_text_query(message: Message, locations: List[LocationRecord]) -> None:
    """Handle free-text search queries."""

    q = (message.text or "").strip()
    if not q or q.startswith("/"):
        await message.answer("請輸入地點關鍵字，如 `Tokyo Shibuya`。", parse_mode="Markdown")
        return

    ranked = _rank_and_filter(q, locations)
    if not ranked:
        examples = [
            "Amsterdam Canal Belt",
            "Bangkok Sukhumvit",
            "Tokyo Shibuya",
            "Singapore Clarke Quay",
            "New York Times Square",
        ]
        await message.answer(
            "無匹配記錄，或資料可能已過期。建議嘗試更精確關鍵字（如城市+區域）。\n\n"
            "你可以試試：\n- " + "\n- ".join(f"`{e}`" for e in examples),
            parse_mode="Markdown",
        )
        return

    # Keep top 6 (as requested 3–6)
    top = ranked[:6]
    _user_last_results[message.from_user.id] = [x.record for x in top if message.from_user]

    lines = ["**匹配結果（點選查看詳細）**\n"]
    for i, s in enumerate(top, start=1):
        lines.append(_format_compact_line(i, s))
    kb = _make_results_keyboard(len(top))
    await message.answer("\n".join(lines), parse_mode="Markdown", reply_markup=kb)


@router.callback_query(F.data.startswith("pick:"))
async def on_pick_detail(callback: CallbackQuery) -> None:
    """Show detail for a selected result index."""

    user_id = callback.from_user.id
    last = _user_last_results.get(user_id) or []
    try:
        idx = int((callback.data or "").split(":", 1)[1])
    except Exception:
        await callback.answer("按鈕資料錯誤，請重新搜尋。", show_alert=True)
        return

    if idx < 1 or idx > len(last):
        await callback.answer("結果已過期或不存在，請重新搜尋。", show_alert=True)
        return

    rec = last[idx - 1]
    await callback.message.answer(_format_detail(rec), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("more:"))
async def on_more_region(callback: CallbackQuery, locations: List[LocationRecord]) -> None:
    """Offer more locations by continent as a lightweight browsing feature."""

    region = (callback.data or "").split(":", 1)[1]
    filtered = [r for r in locations if _continent_of(r) == region]
    if not filtered:
        await callback.answer("沒有更多資料。", show_alert=True)
        return

    # Show up to 10 suggestions (not tied to last search).
    filtered = filtered[:10]
    lines = [f"**{region.upper()} 範例（隨機展示/固定前段）**\n"]
    for r in filtered:
        place = " / ".join(p for p in [r.country, r.city, r.area, r.sub_area] if p)
        lines.append(f"- **{place}** — *{r.nickname}*" if r.nickname else f"- **{place}**")
    await callback.message.answer("\n".join(lines), parse_mode="Markdown")
    await callback.answer()

