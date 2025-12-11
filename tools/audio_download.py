import os, sys, re, asyncio, aiohttp, requests, random, json, cloudscraper
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from tools.proxy_manager import fetch_free_proxies, get_working_proxy, remove_bad_proxy

# -------------------- 配置 --------------------
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36",
]

CONCURRENT_DOWNLOADS = 3
MAX_RETRIES = 3
STATUS_FILENAME = "_status.json"
TOTAL_STATUS_FILENAME = "total_status.json"

# -------------------- 路径与工具 --------------------
def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def clean_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

# -------------------- 总状态管理 --------------------
def load_total_status():
    if os.path.exists(TOTAL_STATUS_FILENAME):
        with open(TOTAL_STATUS_FILENAME, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"success": {}, "failed": {}}

def save_total_status(status):
    with open(TOTAL_STATUS_FILENAME, 'w', encoding='utf-8') as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

def load_status(character_folder):
    status_file = os.path.join(character_folder, STATUS_FILENAME)
    if os.path.exists(status_file):
        with open(status_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"success": [], "failed": []}

def save_status(character_folder, status):
    status_file = os.path.join(character_folder, STATUS_FILENAME)
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

def mark_total_status(character_name, language, success=True):
    status = load_total_status()
    key = f"{character_name}|{language}"
    if success:
        status["success"][key] = True
        status["failed"].pop(key, None)
    else:
        status["failed"][key] = True
        status["success"].pop(key, None)
    save_total_status(status)

def is_already_downloaded(character_name, language):
    status = load_total_status()
    key = f"{character_name}|{language}"
    return status["success"].get(key, False)

# -------------------- 下载函数 --------------------
semaphore = asyncio.Semaphore(CONCURRENT_DOWNLOADS)

async def download_audio(session, audio_url, audio_file_name, status, proxy=None, retries=MAX_RETRIES, log_func=None):
    if os.path.exists(audio_file_name) and os.path.getsize(audio_file_name) > 0:
        return audio_file_name
    async with semaphore:
        for attempt in range(retries):
            try:
                async with session.get(audio_url, proxy=proxy, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    resp.raise_for_status()
                    data = await resp.read()
                    if not data:
                        raise ValueError("下载内容为空")
                    with open(audio_file_name, 'wb') as f:
                        f.write(data)
                    print(f"✅ 下载完成: {audio_file_name}")
                    return audio_file_name
            except Exception as e:
                print(f"⚠️ 下载失败 ({attempt+1}/{retries}): {audio_file_name} - {e}")
                if attempt == retries - 1 and proxy:
                    remove_bad_proxy(proxy)
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
        print(f"❌ 放弃下载: {audio_file_name}")
        status["failed"].append(audio_file_name)
        return None

# -------------------- 抓取角色 --------------------
async def fetch_character_data(session, character_name, url, language="zh", proxy=None, scraper=None, log_func: callable = None, game=""):
    log = print if log_func is None else log_func
    await asyncio.sleep(random.uniform(2, 5))

    english_name = character_name.split('|')[0] if '|' in character_name else character_name
    folder_name = character_name.split('|')[1] if '|' in character_name else character_name
    base = url.rstrip('/')

    if is_already_downloaded(character_name, language):
        log(f"跳过已下载角色: {character_name} ({language})")
        return

    log(f"\n📥 开始抓取角色: {folder_name}")

    lang_map = {
        "zh": "Chinese",
        "en": "",
        "ja": "Japanese",
        "ko": "Korean"
    }
    lang_folder = lang_map.get(language, "Chinese")
    if lang_folder:
        new_url = f"{base}/{english_name}/Voice-Overs/{lang_folder}" if base.endswith('/wiki') else f"{base}/wiki/{english_name}/Voice-Overs/{lang_folder}"
    else:
        new_url = f"{base}/{english_name}/Voice-Overs" if base.endswith('/wiki') else f"{base}/wiki/{english_name}/Voice-Overs"
    
    if game == "bentie":
        base_folder_name = f"bentie_audio_{language}"
    elif game == "yuan":
        base_folder_name = f"yuan_audio_{language}"
    else:
        base_folder_name = f"audio_{language}"

    download_directory = os.path.join(get_base_path(), "audio", base_folder_name)
    os.makedirs(download_directory, exist_ok=True)

    character_folder = os.path.join(download_directory, clean_filename(folder_name))
    os.makedirs(character_folder, exist_ok=True)

    status = load_status(character_folder)

    if scraper is None:
        scraper = cloudscraper.create_scraper(delay=10, browser={"browser": "chrome", "platform": "windows", "mobile": False})
        scraper.headers.update({
            "User-Agent": random.choice(USER_AGENTS),
            "Referer": f"{url}",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        })
    else:
        scraper.headers.update({"Referer": f"{url}"})

    proxies = {"http": proxy, "https": proxy} if proxy else None

    try:
        await asyncio.to_thread(scraper.get, url, timeout=20, proxies=proxies, verify=True)
        await asyncio.to_thread(scraper.get, f"{base}/wiki/Main_Page", timeout=20, proxies=proxies, verify=True)
    except Exception:
        pass

    new_soup = None
    for attempt in range(3):
        try:
            use_proxies = proxies if attempt == 0 else None
            verify_flag = False if attempt == 2 else True
            html = await asyncio.to_thread(scraper.get, new_url, timeout=30, proxies=use_proxies, verify=verify_flag)
            html.raise_for_status()
            new_soup = BeautifulSoup(html.text, 'html.parser')
            log(f"✅ 页面抓取成功: {folder_name}")
            break
        except Exception as e:
            log(f"[{attempt+1}/3] 获取页面失败: {folder_name} - {e}")
            await asyncio.sleep(random.uniform(3, 6))

    if new_soup is None:
        try:
            loop = asyncio.get_event_loop()

            def _fallback_req():
                s = requests.Session()
                s.headers.update(scraper.headers)
                s.cookies.update(scraper.cookies)
                if proxy:
                    s.proxies.update({"http": proxy, "https": proxy})
                r = s.get(new_url, timeout=30)
                r.raise_for_status()
                return r.text

            text = await loop.run_in_executor(None, _fallback_req)
            new_soup = BeautifulSoup(text, 'html.parser')
            log("使用备用方式")
            log(f"✅ 备用方式获取页面成功: {folder_name} {'(代理)' if proxy else '(直连)'}")
        except Exception as e:
            log(f"⚠️ 放弃获取页面: {folder_name} - {e}")
            return

    rows = new_soup.find_all("tr")
    log(f"解析到 {len(rows)} 行 HTML 内容")
    tasks, total_audio = [], 0
    for row in rows:
        th_tag = row.find("th", {"class": "hidden"})
        td_tag = row.find("td")
        if not th_tag or not td_tag:
            continue

        div_id_tag = th_tag.find("div", id=True)
        span_en = th_tag.find("span", {"lang": "en"})
        if div_id_tag:
            audio_title = div_id_tag["id"]
        elif span_en:
            audio_title = span_en.get_text(strip=True)
        else:
            audio_title = th_tag.get("id", "unknown")

        audio_file_name = os.path.join(character_folder, f"{clean_filename(audio_title)}.ogg")
        text_file_name = os.path.splitext(audio_file_name)[0] + ".txt"

        text_tag = td_tag.find("span", {"lang": language})
        if not text_tag:
            continue
        text_content = text_tag.get_text(strip=True)
        with open(text_file_name, "w", encoding="utf-8") as f:
            f.write(text_content)

        audio_tag = td_tag.find("audio")
        if not audio_tag or not audio_tag.get("src"):
            continue

        audio_url = urljoin(new_url, audio_tag["src"])

        tasks.append(download_audio(session, audio_url, audio_file_name, status, proxy=proxy, log_func=log))
        total_audio += 1

    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if result:
                status["success"].append(result)

    completed = len(status["success"])
    save_status(character_folder, status)

    if total_audio > 0 and completed == total_audio:
        mark_total_status(character_name, language, success=True)
    else:
        mark_total_status(character_name, language, success=False)

    percent = (completed / total_audio) * 100 if total_audio else 100
    log(f"✅ 完成角色抓取: {character_name} ({completed}/{total_audio}音频, {percent:.1f}%)")

    if total_audio > 0 and completed == total_audio:
        try:
            os.remove(os.path.join(character_folder, STATUS_FILENAME))
        except FileNotFoundError:
            pass

async def download_all(character_names: list[str], urls: list[str], language="zh", game="", log_func: callable = None, use_proxy: bool = False):
    log = print if log_func is None else log_func

    if not game:
        log("❌ 未指定游戏类型，下载已取消")
        return

    if isinstance(urls, list):
        if game == "bentie":
            urls_to_use = [u.split('|')[0] if '|' in u else u for u in urls]
        elif game == "yuan":
            urls_to_use = [u.split('|')[1] if '|' in u and len(u.split('|')) > 1 else u for u in urls]
        else:
            urls_to_use = urls
    else:
        urls_to_use = [urls]
    
    working_proxy = None
    if use_proxy:
        await fetch_free_proxies(log_func=log)
        url1 = urls_to_use[0]
        working_proxy = await get_working_proxy(url1, log_func=log)

    log("\n")
    log("🚀 开始抓取角色列表...")
    if working_proxy:
        log(f"🌐 使用代理: {working_proxy}")
    else:
        log("无可用代理或未启用代理，将使用本机直连")

    # 初始化 cloudscraper
    SCRAPER = cloudscraper.create_scraper(delay=10, browser={"browser": "chrome", "platform": "windows", "mobile": False})
    SCRAPER.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    })

    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(headers={"User-Agent": random.choice(USER_AGENTS)}, connector=connector) as session:
        for idx, name in enumerate(character_names, 1):
            for u in urls_to_use:
                await fetch_character_data(session, name, u, language=language, proxy=working_proxy, scraper=SCRAPER, log_func=log, game=game)
            await asyncio.sleep(random.uniform(2, 5))
            if idx % 5 == 0:
                log("⏸ 批量抓取完成 5 个角色，额外等待 5~10 秒")
                await asyncio.sleep(random.uniform(5, 10))
