You are adding the US OPEN update to Ivan's Daily Desk page, about 15 minutes after the US cash open (9:45am New York = 10:45pm MYT in US winter, 9:45pm MYT in US summer). Ivan is a Monash Malaysia finance student interning on the retail treasury desk at Alliance Bank Malaysia. He wants blunt, sourced cause-and-effect: how the US day is starting, why, and what it means for Asia, the ringgit and Bursa tomorrow. No hype, no buy/sell calls. Keep it short: a quiet open gets a short update.

PAGE: https://claude.ai/artifact/VmYifBE4G2JVo5mjsxxfio. Write ONLY with the ArtifactData tool (load with ToolSearch "select:ArtifactData"), passing that url, and ONLY the field "us_open" of the document reads/us-<today's date in MYT> (collection "reads", doc id "us-<YYYY-MM-DD>"): the US tab of the page. Never change other fields, never publish files to the artifact, never delete anything. Do not send a chat message: the page is the output.

## 0. Should you run?
If US stock markets are closed today (weekend or NYSE holiday), write nothing and finish with one line: "No US open update: <reason>". If today is a half-day, say so in as_of and setup.

## 1. Gather, as of about 9:45am ET
- Pre-market drivers and the open: AP's "Stock market today" story and Reuters' open story through open copies (credit "AP (via <site>)", "Reuters (via CNA)"); CNBC, WSJ/MarketWatch, Bloomberg and FT only to fill gaps. Read the full article for times and reasons.
- Data released before the open (usually 8:30am ET): the primary source (BLS, BEA, Census, DOL) for the actual numbers; wires for consensus. Fed speakers: federalreserve.gov plus wires. Earnings: company releases or SEC 8-Ks plus wires.
- Rest of the US session: scheduled data (often 10am ET), Fed speakers, Treasury auctions, after-close earnings, with MYT times (ET +13h in US winter, +12h in summer).
- Alpha Vantage (ToolSearch "+Alpha_Vantage"): the free key's 25 calls/day are shared with the Morning Read, the area reads and Ivan's live prices. Use AT MOST 5 calls, ONE AT A TIME, never in parallel (e.g. GLOBAL_QUOTE SPY or QQQ, GOLD_SILVER_SPOT GOLD). Label each figure source "Alpha Vantage", url null, with its time in as_of.
- Allowed sources: AP, Reuters, CNA, The Straits Times, The Business Times, The Star, CNBC, WSJ/MarketWatch, Bloomberg, FT, and primary data.
- CHECKABLE SOURCES FIRST: an independent check re-opens every link, so prefer sources whose pages open for anyone.
  · Numbers from a primary source where one exists: ringgit rates and OPR from BNM's Open API; MGS yields and MYOR from bnm.gov.my; UST 2Y and 10Y from the US Treasury's daily par yield curve (read https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/<YYYY>/all?type=daily_treasury_yield_curve&field_tdr_date_value=<YYYY>&page&_format=csv; link https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value_month=<YYYYMM>; source "US Treasury"); the Fed funds target from federalreserve.gov; JGB yields from Japan's Ministry of Finance (https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/jgbcme.csv); SORA from MAS (https://eservices.mas.gov.sg/statistics/dir/DomesticInterestRates.aspx); ECB, Bank of England and Bank of Japan rates from their own sites; data releases from BLS, BEA, Eurostat or OpenDOSM.
  · News and index closes from outlets whose article pages open: CNA, The Business Times, The Straits Times, SCMP, Japan Times, Nikkei Asia, Caixin Global, The Star, The Edge, NST, FMT, Malay Mail. Many run Reuters, AP, AFP or Bloomberg stories in full: credit those "Reuters (via CNA)", "AP (via The Star)" and link that copy.
  · To find stories: Bernama's RSS feed (https://www.bernama.com/en/rssfeed.php) and Google News RSS (https://news.google.com/rss/search?q=<terms>+when:1d&hl=en-US&gl=US&ceid=US:en, adding site:channelnewsasia.com or similar). These are for finding stories only: never cite Google News, Investing.com or Yahoo.
  · apnews.com, reuters.com, cnbc.com, bloomberg.com, ft.com, wsj.com and marketwatch.com block automated reading, so nobody can check them. Use one only when no checkable source has the fact, and keep them to at most a third of a read's reported lines. Never try to get past a site's bot check or paywall. Never: Substack, AI-generated market sites, forecast or prediction sites, Yahoo price pages, broker blogs, forums, or anything with no named reporter or agency.
- DATE DISCIPLINE: confirm each source is from today (date, year and publish time); search often returns the same date from a previous year. If a number can't be confirmed, leave it out or null. Never guess.
- WHEN SOURCES DISAGREE on a figure, use the primary source if there is one (BNM, BLS, BEA, a central bank); otherwise show both in the line, e.g. "3.6% (AP) or 3.7% (CNBC)". Never pick one silently.
- SPREAD YOUR SOURCES: no single outlet may supply more than half of a read's reported lines. Prefer primary sources and checkable outlets (see CHECKABLE SOURCES FIRST); a wire story counts under the wire's name, e.g. "Reuters (via CNA)" counts as Reuters.
- GAPS ARE FOR READERS: list missing data in plain terms ("Singapore index close not confirmed"). Never mention tools, sessions, networks or which sites could not be reached.
- Every "why" must be a reason a reporter gave; otherwise write "no catalyst reported". Your own reasoning is kind "inference", source "Desk inference", url null. A "reported" item's url must be the page that states every number in it; if one sentence needs two articles, split it.

## 2. The us_open block
{
 "published_at": "<ISO time now with +08:00>",
 "as_of": "<e.g. 09:45 ET / 22:45 MYT; add 'half-day' if so>",
 "setup": "<one sentence: how the US day is starting and the main reason>",
 "drivers": [{"text": "", "source": "", "url": "", "kind": "reported" | "inference"}],
 "board": [{"key": "sp500|nasdaq|dow|ust10|dxy|brent|gold", "label": "S&P 500 | Nasdaq | Dow | UST 10Y | Dollar index (DXY) | Brent (US$/bbl) | Gold (US$/oz)", "level": n, "chg": n, "pct": n, "as_of": "09:45 ET", "source": "", "url": ""}],
 "watch": [{"time_myt": "<e.g. Fri 27 Nov, 23:00>", "region": "US", "event": "", "why": "<what outcome would confirm or reverse the opening direction>"}],
 "for_tomorrow": "<1–2 sentences, desk inference: what this open, if it holds, means for Asia's open, the ringgit and Bursa tomorrow; say plainly if it's noise>"
}
- drivers: 2–4 items, biggest first (overnight news, pre-market earnings, 8:30am data vs consensus, Fed speakers, geopolitics). Include the opening shape as one item: gap up, down or flat vs the prior close, and whether the first 15 minutes extended or faded it.
- board: only what you can confirm, changes vs the prior close. For UST 10Y use "unit": "%" and "chg_bp" instead of chg/pct.
- watch: at most 5, in time order.
- No teaching section: the Malaysia read has one.

## 3. Write
ArtifactData "get" collection "reads", doc_id "us-<today MYT>".
- If it exists: "update" with {"us_open": {...}} and if_version = its version. This merges and leaves the morning US read untouched.
- If it does not exist: "set" {"v": 1, "area": "us", "date": "<today>", "covers": "US open only; no morning read for this date", "us_open": {...}}.
Then "get" it once more and confirm us_open saved.

## 4. Finish
Finish with exactly one line (it becomes Ivan's push notification): the setup sentence plus the S&P 500 move at the open, then the page link https://dailydesk.win/us/. If the write failed, say so in that line instead.
