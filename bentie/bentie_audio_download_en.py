import os,sys,re,asyncio,aiohttp
from bs4 import BeautifulSoup

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

download_directory = os.path.join(get_base_path(), "bentie_audio_en")
os.makedirs(download_directory, exist_ok=True)

def clean_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

async def download_audio(session, audio_url, audio_file_name, retries=3,log_func=None):
    for attempt in range(retries):
        try:
            async with session.get(audio_url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                response.raise_for_status()
                with open(audio_file_name, 'wb') as file:
                    file.write(await response.read())
                if log_func:
                    log_func(f"下载完成: {audio_file_name}")
                print(f"下载完成: {audio_file_name}")
                return
        except aiohttp.ClientError as e:
            if log_func:
                log_func(f"下载失败: {audio_file_name} - {e}")
            print(f"下载失败: {audio_file_name} - {e}")
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                if log_func:
                    log_func(f"放弃下载: {audio_file_name}")
                print(f"放弃下载: {audio_file_name}")

async def fetch_character_data(session, character_name,log_func=None):
    new_url = f"https://honkai-star-rail.fandom.com/wiki/{character_name}/Voice-Overs"
    character_folder = os.path.join(download_directory, character_name)
    os.makedirs(character_folder, exist_ok=True)

    for attempt in range(3):
        try:
            async with session.get(new_url, timeout=aiohttp.ClientTimeout(total=100)) as response:
                response.raise_for_status()
                new_soup = BeautifulSoup(await response.text(), 'html.parser')
                break
        except aiohttp.ClientError:
            if attempt < 2:
                await asyncio.sleep(5 ** attempt)
            else:
                if log_func:
                    log_func(f"放弃获取页面: {character_name}")
                print(f"放弃获取页面: {character_name}")
                return
    if new_soup:
        rows = new_soup.find_all("tr")
        
    tasks = []
    for row in rows:
        td = row.find("td")
        if td:
            audio_btn = td.find("span", class_="audio-button custom-theme hidden")
            en_text = td.find("span", lang="en")
            div = row.find("th")

            if audio_btn and en_text and div:
                link = audio_btn.find("a", class_="internal")
                if link:
                    audio_url = link["href"]
                    audio_title = clean_filename(div.get("id", "unknown"))
                    audio_file_name = os.path.join(character_folder, f"{audio_title}.ogg")
                    text_file_name = os.path.splitext(audio_file_name)[0] + ".txt"
                    text_content = en_text.get_text(strip=True)

                    if os.path.exists(audio_file_name):
                        with open(text_file_name, 'w', encoding='utf-8') as f:
                            f.write(text_content)
                    else:
                        if text_content:
                            tasks.append(download_audio(session, audio_url, audio_file_name))
                            with open(text_file_name, 'w', encoding='utf-8') as f:
                                f.write(text_content)

    await asyncio.gather(*tasks)

async def download_all(character_names: list[str], log_func:callable):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_character_data(session, name, log_func=log_func) for name in character_names]
        await asyncio.gather(*tasks)
