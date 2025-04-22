#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import uvloop
import logging
from miio import Device
from miio.exceptions import DeviceException
import signal, sys

def handle_sigterm(signum, frame):
    logging.info("[Launchd] SIGTERM 수신 - Roborock Monitoring 종료...")
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_sigterm)

# 로깅 설정
# 로깅 설정 (파일 + 콘솔 동시에 출력)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 포맷 지정
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

# 콘솔 핸들러
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# 파일 핸들러
file_handler = logging.FileHandler("monitoring.log", mode="a", encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# 로봇 청소기의 IP 주소와 토큰을 입력하세요.

VACUUM_IP = "your_ip"
VACUUM_TOKEN = "your_token"

# 상태 확인 주기 (초 단위)
CHECK_INTERVAL = 60  # 1분

async def check_vacuum_status():
    """
    로봇 청소기의 상태를 주기적으로 확인하고,
    오류나 배터리 부족 시 도크로 복귀시키는 코루틴.
    """
    try:
        vacuum = Device(VACUUM_IP, VACUUM_TOKEN)
    except DeviceException as e:
        logging.error(f"로봇 청소기 초기화 중 오류 발생: {e}")
        return

    while True:
        try:
            # 상태 정보 가져오기
            status = vacuum.send("get_status")[0]
            state = status.get("state")
            battery = status.get("battery")
            error_code = status.get("error_code")

            logging.info(f"현재 상태: {state}, 배터리: {battery}%, 오류 코드: {error_code}")

            # 오류 발생 시 도크로 복귀
            if error_code != 0:
                logging.warning("오류가 감지되었습니다. 도크로 복귀를 시도합니다.")
                vacuum.send("app_charge")

            # 배터리가 20% 미만이고 충전 중이 아니라면 도크로 복귀
            if battery < 20 and state not in ["charging", "returning"]:
                logging.info("배터리가 20% 미만입니다. 도크로 복귀합니다.")
                vacuum.send("app_charge")

        except DeviceException as e:
            logging.error(f"로봇 청소기와 통신 중 오류 발생: {e}")
        except Exception as e:
            logging.error(f"예상치 못한 오류 발생: {e}")

        await asyncio.sleep(CHECK_INTERVAL)

async def main():
    """
    uvloop 이벤트 루프를 사용하는 메인 함수.
    """
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    await check_vacuum_status()

if __name__ == "__main__":
    logging.info("Startup Roborock Monitoring")
    logging.info(f"- Device IP : {VACUUM_IP}")
    asyncio.run(main())

