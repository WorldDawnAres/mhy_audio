import os,sys,re,asyncio,aiohttp,requests
from bs4 import BeautifulSoup

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

download_directory = os.path.join(get_base_path(), "audio/bentie_audio_ko")
os.makedirs(download_directory, exist_ok=True)

def clean_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

async def download_audio(session, audio_url, audio_file_name, retries=3):
    for attempt in range(retries):
        try:
            async with session.get(audio_url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                response.raise_for_status()
                with open(audio_file_name, 'wb') as file:
                    file.write(await response.read())
                print(f"下载完成: {audio_file_name}")
                return
        except aiohttp.ClientError as e:
            print(f"下载失败: {audio_file_name} - {e}")
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                print(f"放弃下载: {audio_file_name}")

async def fetch_character_data(session, character_name):
    if '|' in character_name:
        english_name, folder_name = character_name.split('|', 1)
    else:
        english_name = folder_name = character_name
    new_url = f"https://honkai-star-rail.fandom.com/wiki/{english_name}/Voice-Overs/Korean"
    character_folder = os.path.join(download_directory, folder_name)
    os.makedirs(character_folder, exist_ok=True)

    new_soup = None

    for attempt in range(3):
        try:
            async with session.get(new_url, timeout=aiohttp.ClientTimeout(total=100)) as response:
                response.raise_for_status()
                new_soup = BeautifulSoup(await response.text(), 'html.parser')
                break
        except aiohttp.ClientError as e:
            print(f"[{attempt+1}/3] 获取页面失败: {folder_name}")
            if attempt < 2:
                await asyncio.sleep(5 ** attempt)

    if new_soup is None:
        print(f"⚠️ 获取失败，尝试使用其他方式获取: {folder_name}")
        try:
            response = requests.get(new_url, timeout=100)
            response.raise_for_status()
            new_soup = BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException as e:
            print(f"放弃获取页面: {folder_name}")
            return
        
    rows = new_soup.find_all("tr")
    tasks = []
    for row in rows:
        td = row.find("td")
        if td:
            audio_btn = td.find("span", class_="audio-button custom-theme hidden")
            zh_text = td.find("span", lang="ko")
            div = row.find("div")

            if audio_btn and zh_text and div:
                link = audio_btn.find("a", class_="internal")
                if link:
                    audio_url = link["href"]
                    audio_title = clean_filename(div.get("id", "unknown"))
                    audio_file_name = os.path.join(character_folder, f"{audio_title}.ogg")
                    text_file_name = os.path.splitext(audio_file_name)[0] + ".txt"
                    text_content = zh_text.get_text(strip=True)

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
