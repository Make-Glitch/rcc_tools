import requests
import subprocess
import pyfiglet
import os
import asyncio
import aiohttp
import time
import shutil
from datetime import datetime

RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
WHITE = '\033[97m'
RESET = '\033[0m'

def clear_screen():
    subprocess.run('clear')

def print_title():
    ascii_title = pyfiglet.figlet_format("RBX Cookie Checker")
    print(f"{WHITE}{ascii_title}{RESET}")

async def check_cookie(session, original_cookie, filter_valid):
    cookie = original_cookie
    if cookie.startswith('.ROBLOSECURITY='):
        cookie = cookie.replace('.ROBLOSECURITY=', '')

    headers = {'Cookie': f'.ROBLOSECURITY={cookie}'}
    try:
        async with session.get("https://users.roblox.com/v1/users/authenticated", headers=headers, timeout=10) as resp1:
            if resp1.status != 200:
                if not filter_valid:
                    print(f"{RED}[-] 불량 쿠키입니다{RESET}")
                return 'invalid', original_cookie, None, None

            user_info = await resp1.json()

        async with session.get("https://economy.roblox.com/v1/user/currency", headers=headers, timeout=10) as resp2:
            robux = (await resp2.json()).get('robux', '알 수 없음') if resp2.status == 200 else '알 수 없음'

        print(f"{GREEN}[+] 유효 쿠키입니다{RESET}")
        return 'valid', original_cookie, user_info.get('name'), robux

    except Exception:
        if not filter_valid:
            print(f"{RED}[-] 오류 쿠키입니다{RESET}")
        return 'invalid', original_cookie, None, None

async def process_cookies(cookies, filter_valid):
    connector = aiohttp.TCPConnector(limit=100)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for cookie in cookies:
            tasks.append(check_cookie(session, cookie, filter_valid))
        return await asyncio.gather(*tasks)

def input_cookies():
    print(f"{YELLOW}쿠키를 한 줄씩 입력하세요. 종료하려면 Ctrl+D 입력:{RESET}")
    cookies = set()
    try:
        while True:
            line = input()
            if line.strip() and (line.startswith('.ROBLOSECURITY=') or line.startswith('_|')):
                cookies.add(line.strip())
    except EOFError:
        pass
    return list(cookies)

def search_txt_files():
    print(f"{YELLOW}TXT 검색 방식을 선택하세요:{RESET}")
    print(f"{GREEN}[1]{RESET} 전체 txt 검색")
    print(f"{GREEN}[2]{RESET} 키워드 포함 txt 검색")
    mode = input(f"{CYAN}선택 (1/2): {RESET}").strip()

    keyword = ''
    if mode == '2':
        keyword = input(f"{CYAN}검색할 키워드를 입력하세요: {RESET}").strip()

    print(f"{YELLOW}검색 중... 잠시만 기다려주세요.{RESET}")
    try:
        result = subprocess.run(
            ['find', '/storage/emulated/0', '-type', 'f', '-name', '*.txt'],
            capture_output=True, text=True, timeout=60
        )
        files = result.stdout.strip().split('\n')
        if mode == '2':
            files = [f for f in files if keyword in os.path.basename(f)]

        files = [f for f in files if f]
        if not files:
            print(f"{RED}TXT 파일을 찾을 수 없습니다.{RESET}")
            return {}

        file_map = {str(i+1): f for i, f in enumerate(files)}
        for num, path in file_map.items():
            print(f"{CYAN}[{num}] {os.path.basename(path)}{RESET}")
        return file_map
    except Exception as e:
        print(f"{RED}검색 오류: {e}{RESET}")
        return {}

def select_and_read_file(file_map):
    while True:
        choice = input(f"{YELLOW}파일 번호를 선택하세요 (취소는 'exit'): {RESET}").strip()
        if choice.lower() == 'exit':
            return []
        if choice in file_map:
            try:
                with open(file_map[choice], 'r') as f:
                    cookies = {
                        line.strip() for line in f
                        if line.strip().startswith('.ROBLOSECURITY=') or line.strip().startswith('_|')
                    }
                    print(f"{GREEN}{len(cookies)}개의 쿠키를 불러왔습니다.{RESET}")
                    return list(cookies)
            except Exception as e:
                print(f"{RED}파일 읽기 실패: {e}{RESET}")
        else:
            print(f"{RED}잘못된 선택입니다.{RESET}")

def save_valid_cookies(valid_list):
    if not valid_list:
        print(f"{YELLOW}저장할 유효 쿠키가 없습니다.{RESET}")
        return

    want_save = input(f"{CYAN}유효 쿠키를 파일로 저장하시겠습니까? (y/n): {RESET}").strip().lower()
    if want_save != 'y':
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"유효쿠키_{timestamp}.txt"
    temp_path = filename
    save_path = f"/sdcard/{filename}"

    try:
        with open(temp_path, 'w') as f:
            for name, robux, cookie in valid_list:
                f.write(f"유저네임 : {name} | Robux : {robux}\n{cookie}\n\n")

        shutil.move(temp_path, save_path)
        print(f"{GREEN}유효 쿠키가 저장되었습니다: {save_path}{RESET}")
    except Exception as e:
        print(f"{RED}파일 저장 실패: {e}{RESET}")

def main():
    while True:
        clear_screen()
        print_title()
        print(f"{YELLOW}입력 방법을 선택하세요:{RESET}")
        print(f"{GREEN}[1]{RESET} 수동 입력")
        print(f"{GREEN}[2]{RESET} TXT 파일")
        print(f"{GREEN}[0]{RESET} 종료")

        choice = input(f"{CYAN}선택 (0/1/2): {RESET}").strip()

        if choice == '0':
            print(f"{RED}종료합니다.{RESET}")
            break
        elif choice == '1':
            cookies = input_cookies()
        elif choice == '2':
            file_map = search_txt_files()
            if not file_map:
                input(f"{YELLOW}엔터를 눌러 메뉴로 돌아갑니다...{RESET}")
                continue
            cookies = select_and_read_file(file_map)
            if not cookies:
                input(f"{YELLOW}엔터를 눌러 메뉴로 돌아갑니다...{RESET}")
                continue
        else:
            print(f"{RED}잘못된 입력입니다.{RESET}")
            input(f"{YELLOW}엔터를 눌러 메뉴로 돌아갑니다...{RESET}")
            continue

        filter_valid = input(f"{CYAN}유효한 쿠키만 출력할까요? (y/n): {RESET}").strip().lower() == 'y'

        print(f"\n{GREEN}[+] 총 {len(cookies)}개의 쿠키를 확인 합니다...{RESET}\n")
        start_time = time.time()
        try:
            results = asyncio.run(process_cookies(cookies, filter_valid))
        except KeyboardInterrupt:
            print(f"{YELLOW}\n\n검사가 사용자에 의해 중단되었습니다.{RESET}")
            results = []

        end_time = time.time()
        duration = end_time - start_time
        rps = len(results) / duration if duration > 0 else 0

        valid = []
        for result, cookie, name, robux in results:
            if result == 'valid':
                print(f"{GREEN}유저네임 : {name} | Robux : {robux}\n{cookie}{RESET}\n")
                valid.append((name, robux, cookie))

        print(f"{YELLOW}검사 완료 - 총 {len(results)}개 | 유효: {len(valid)}, 불량: {len(results)-len(valid)}{RESET}")
        print(f"{CYAN}소요 시간: {duration:.2f}초 | RPS: {rps:.2f}{RESET}")

        save_valid_cookies(valid)
        input(f"{YELLOW}계속하려면 엔터를 누르세요...{RESET}")

if __name__ == "__main__":
    main()
