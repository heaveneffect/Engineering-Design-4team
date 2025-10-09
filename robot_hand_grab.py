#!/usr//bin/env python3

# 필요한 라이브러리를 가져옵니다.
import time
from ev3dev2.sensor import INPUT_1
from ev3dev2.sensor.lego import UltrasonicSensor
from ev3dev2.motor import LargeMotor, OUTPUT_B, SpeedPercent

# --- 하드웨어 설정 ---
# 1번 포트에 초음파 센서 연결
us = UltrasonicSensor(INPUT_1)

# 2번 포트(B)에 모터 연결 (모터 포트는 A, B, C, D 중 하나입니다)
# 사용하시는 모터가 '중간 모터'라면 LargeMotor를 MediumMotor로 바꿔주세요.
lm = LargeMotor(OUTPUT_B)

# --- 변수 설정 ---
# 물체가 감지되기 시작한 시간을 기록할 변수 (처음에는 비워둠)
detection_start_time = None
# 모터 동작이 한번 실행되었는지 확인하는 변수
action_triggered = False

print("프로그램 시작: 5cm 안에 물체를 2초 이상 두면 모터가 움직입니다.")

# 무한 루프를 돌면서 계속 센서 값을 확인합니다.
while Tru
    # 초음파 센서에서 거리를 cm 단위로 읽어옵니다.
    distance = us.distance_centimeters

    # 1. 물체가 5cm보다 가까이 있는 경우
    if distance < 5:
        # 1-1. 물체가 '처음' 감지된 순간이라면
        if detection_start_time is None:
            # 현재 시간을 기록합니다.
            detection_start_time = time.time()
            print(f"물체 감지 시작! (거리: {distance:.1f} cm)")

        # 1-2. 감지된 후 2초가 지났고, 아직 모터가 움직인 적이 없다면
        if time.time() - detection_start_time > 2 and not action_triggered:
            print("2초 이상 감지됨! 모터를 45도 회전합니다.")
            
            # 모터를 25% 속도로 45도 만큼 회전시킵니다.
            lm.on_for_degrees(speed=SpeedPercent(25), degrees=45)
            
            # 모터 동작을 완료했으므로, 다시 움직이지 않도록 True로 변경합니다.
            action_triggered = True
            print("모터 작동 완료.")

    # 2. 물체가 5cm보다 멀리 있는 경우 (또는 사라진 경우)
    else:
        # 감지 시간을 초기화해서 타이머를 리셋합니다.
        if detection_start_time is not None:
             print("물체가 사라져서 타이머를 리셋합니다.")
        detection_start_time = None
        action_triggered = False

    # CPU가 너무 빠르게 작동하지 않도록 0.1초 쉽니다.
    time.sleep(0.1)
