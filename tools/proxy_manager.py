import os, sys, json, asyncio, cloudscraper, random

# -------------------- 文件路径 --------------------
def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

PROXY_JSON_FILE = os.path.join(get_base_path(), "stable_proxies.json")

if not os.path.exists(PROXY_JSON_FILE):
    os.makedirs(os.path.dirname(PROXY_JSON_FILE), exist_ok=True)
    with open(PROXY_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

# -------------------- 文件操作 --------------------
def load_proxy_file():
    if os.path.exists(PROXY_JSON_FILE):
        with open(PROXY_JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_proxy_file(proxy_dict):
    with open(PROXY_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(proxy_dict, f, ensure_ascii=False, indent=2)

# -------------------- Cloudscraper 代理检测 --------------------
def test_proxy_cloudscraper(proxy: str, test_url: str, timeout=20, log_func=print, verbose=True):
    result = {"http": False, "https": False}
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "desktop": True}
    )
    if verbose: log_func(f"\n🔍 测试代理: {proxy}")

    for scheme in ("https", "http"):
        proxy_url = f"{scheme}://{proxy}"
        proxies = {"http": proxy_url, "https": proxy_url}
        try:
            if verbose: log_func(f"   ▶ 访问 {test_url} via {proxy_url}")
            resp = scraper.get(test_url, proxies=proxies, timeout=timeout)
            if resp.status_code == 200:
                result[scheme] = True
                if verbose: log_func(f"   ✅ 可用代理 ({scheme})")
        except Exception as e:
            if verbose: log_func(f"   ❌ 失败 ({scheme}) {type(e).__name__}")
    return result

# -------------------- 批量测试 --------------------
async def test_proxies_batch(proxy_dict, test_url, batch_size=3, log_func=print, verbose=True, max_keep=50):
    keys = list(proxy_dict.keys())
    log_func(f"🧪 开始批量测试 {len(keys)} 个代理...")

    for i in range(0, len(keys), batch_size):
        batch = keys[i:i+batch_size]
        log_func(f"🔹 正在测试批次 {i//batch_size+1} ...")

        total_proxies = len(proxy_dict)
        fail_threshold = 4 if total_proxies > 30 else 3 if total_proxies > 15 else 2 if total_proxies > 5 else 1

        tasks = [asyncio.to_thread(test_proxy_cloudscraper, p, test_url, 20, log_func, verbose) for p in batch]
        results = await asyncio.gather(*tasks)

        for proxy, res in zip(batch, results):
            for scheme in ("http", "https"):
                if res[scheme]:
                    proxy_dict[proxy][f"{scheme}_score"] = proxy_dict[proxy].get(f"{scheme}_score", 0) + 1
                    proxy_dict[proxy][f"{scheme}_fail"] = 0
                else:
                    proxy_dict[proxy][f"{scheme}_score"] = max(-5, proxy_dict[proxy].get(f"{scheme}_score", 0) - 1)
                    proxy_dict[proxy][f"{scheme}_fail"] = proxy_dict[proxy].get(f"{scheme}_fail", 0) + 1

        for p in list(proxy_dict.keys()):
            if proxy_dict[p]["http_fail"] >= fail_threshold and proxy_dict[p]["https_fail"] >= fail_threshold:
                proxy_dict[p]["http_score"] //= 2
                proxy_dict[p]["https_score"] //= 2
                proxy_dict[p]["http_fail"] = 0
                proxy_dict[p]["https_fail"] = 0
                if verbose: log_func(f"⚠️ 代理 {p} 连续失败，健康值减半")
            if proxy_dict[p]["http_score"] <= 0 and proxy_dict[p]["https_score"] <= 0:
                del proxy_dict[p]
                if verbose: log_func(f"❌ 移除低健康代理: {p}")

        if len(proxy_dict) > max_keep:
            sorted_proxies = sorted(proxy_dict.items(), key=lambda x: max(x[1]["http_score"], x[1]["https_score"]), reverse=True)
            proxy_dict = dict(sorted_proxies[:max_keep])
            log_func(f"⚠️ 代理池裁剪至 {max_keep} 个高健康代理...")

        save_proxy_file(proxy_dict)
        await asyncio.sleep(0.5)

    log_func(f"✅ 批量测试完成，可用代理 {len(proxy_dict)} 个")
    return proxy_dict

# -------------------- 免费代理抓取 --------------------
async def fetch_free_proxies(log_func=print, rounds=3, test_url=None, verbose=False, max_keep=50):
    proxy_dict = load_proxy_file()
    log_func(f"📂 加载本地代理池: {len(proxy_dict)} 个")

    proxy_dict = await test_proxies_batch(proxy_dict, test_url, log_func=log_func, verbose=verbose, max_keep=max_keep)
    log_func(f"✅ 本地代理检测完成，可用代理: {len(proxy_dict)}")

    PROXY_APIS = [
        "https://proxy.scdn.io/api/get_proxy.php?protocol=https&count=20",
        "https://www.proxy-list.download/api/v1/get?type=https",
        "https://api.getproxylist.com/proxy?protocol=https"
    ]
    scraper = cloudscraper.create_scraper()

    for i in range(rounds):
        log_func(f"🌐 第 {i+1} 次抓取代理...")
        for api_url in PROXY_APIS:
            try:
                resp = await asyncio.to_thread(scraper.get, api_url, timeout=15)
                proxies = []

                try:
                    response = json.loads(resp.text)
                    if "data" in response and "proxies" in response["data"]:
                        proxies = response["data"]["proxies"]
                    elif isinstance(response, list):
                        proxies = response
                except Exception:
                    proxies = resp.text.splitlines()

                proxies = [p.strip() for p in proxies if p.strip()]
                log_func(f"获取到 {len(proxies)} 个代理")

                for p in proxies:
                    if p not in proxy_dict:
                        proxy_dict[p] = {"http_score":0, "https_score":0, "http_fail":0, "https_fail":0}
                    else:
                        proxy_dict[p]["http_score"] = max(proxy_dict[p]["http_score"], 1)
                        proxy_dict[p]["https_score"] = max(proxy_dict[p]["https_score"], 1)
                        proxy_dict[p]["http_fail"] = 0
                        proxy_dict[p]["https_fail"] = 0

                proxy_dict = await test_proxies_batch(proxy_dict, test_url, log_func=log_func, verbose=verbose, max_keep=max_keep)

            except Exception as e:
                log_func(f"❌ 抓取异常: {api_url} {e}")

        await asyncio.sleep(2)

    save_proxy_file(proxy_dict)
    log_func(f"✅ 代理池更新完成，共 {len(proxy_dict)} 个")
    return proxy_dict

# -------------------- 获取工作代理 --------------------
cached_working_proxies = {}

async def get_working_proxy(url, log_func=print, top_n=20):
    scheme = "https" if url.startswith("https") else "http"
    global cached_working_proxies

    if not cached_working_proxies:
        proxy_dict = load_proxy_file()
        if not proxy_dict:
            log_func("⚠️ 代理池为空")
            return None
        cached_working_proxies = proxy_dict

    available_proxies = [p for p, info in cached_working_proxies.items() if info[f"{scheme}_score"] > 0]
    if not available_proxies:
        fallback_scheme = "http" if scheme == "https" else "https"
        available_proxies = [p for p, info in cached_working_proxies.items() if info[f"{fallback_scheme}_score"] > 0]
        if available_proxies:
            log_func(f"⚠️ {scheme.upper()} 代理不足，使用 {fallback_scheme.upper()} fallback")
            scheme = fallback_scheme
        else:
            log_func("⚠️ 没有可用代理")
            return None

    sorted_proxies = sorted(
        available_proxies,
        key=lambda p: cached_working_proxies[p][f"{scheme}_score"],
        reverse=True
    )
    top_proxies = sorted_proxies[:min(top_n, len(sorted_proxies))]
    weights = [cached_working_proxies[p][f"{scheme}_score"]**2 for p in top_proxies]
    chosen = random.choices(top_proxies, weights=weights, k=1)[0]

    log_func(f"🌐 使用代理: {chosen} ({scheme}) [健康值: {cached_working_proxies[chosen][f'{scheme}_score']}]")
    return chosen

def remove_bad_proxy(proxy, log_func=print):
    global cached_working_proxies
    if proxy in cached_working_proxies:
        del cached_working_proxies[proxy]
        log_func(f"❌ 立即移除坏代理: {proxy}")
        save_proxy_file(cached_working_proxies)

async def run_proxy_check(url_to_test, log_func=print, rounds=5, verbose=True):
    log_func("🚀 开始完整代理检测流程...")
    proxy_dict = await fetch_free_proxies(log_func=log_func, rounds=rounds, test_url=url_to_test, verbose=verbose)
    global cached_working_proxies
    cached_working_proxies = proxy_dict
    log_func(f"✅ 更新后可用代理数量: {len(proxy_dict)}")
    return proxy_dict

def check_proxies(url_to_test="https://httpbin.org/get", log_func=None, rounds=5, verbose=False):
    return asyncio.run(run_proxy_check(url_to_test=url_to_test, log_func=log_func, rounds=rounds, verbose=verbose))

def print_proxy_health(log_func=print):
    global cached_working_proxies
    if not cached_working_proxies:
        log_func("⚠️ 当前没有缓存代理")
        return

    sorted_proxies = sorted(cached_working_proxies.items(), key=lambda x: max(x[1]["http_score"], x[1]["https_score"]), reverse=True)
    log_func("\n📊 当前代理健康值:")
    log_func("代理地址\t\thttp_score\thttps_score\thttp_fail\thttps_fail")
    log_func("-"*50)
    for proxy, info in sorted_proxies:
        log_func(f"{proxy}\t{info['http_score']}\t{info['https_score']}\t{info['http_fail']}\t{info['https_fail']}")
    log_func(f"✅ 总代理数: {len(sorted_proxies)}\n")

if __name__ == "__main__":
    def log_print(msg): print(msg)

    test_url = "https://httpbin.org/get"

    log_print("🔹 测试代理检测功能开始 🔹")
    log_print("⚠️ 注意：测试过程可能需要较长时间，请耐心等待...")
    stable_proxies = check_proxies(url_to_test=test_url, log_func=log_print, rounds=3, verbose=True)

    print_proxy_health(log_print)

    log_print("\n✅ 可用代理列表:")
    for p in stable_proxies:
        print(p)

    log_print("🔹 测试完成 🔹")
