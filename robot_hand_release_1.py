#!/usr/bin/env python3

# ev3dev2 라이브러리에서 필요한 클래스들을 가져옵니다.
from ev3dev2.motor import LargeMotor, SpeedPercent
from ev3dev2.sensor.lego import GyroSensor, TouchSensor
from time import sleep, time

# --- 중요: 포트 설정 ---
# 모터와 센서가 연결된 포트를 실제 로봇에 맞게 수정해주세요.
FINGER_MOTOR_1_PORT = 'outA'
FINGER_MOTOR_2_PORT = 'outB'
THUMB_MOTOR_PORT = 'outC'
GYRO_SENSOR_PORT = 'in1'  # 자이로 센서 포트
TOUCH_SENSOR_PORT = 'in2' # 터치 센서 포트
# ---------------------

# --- 동작 설정 ---
SWING_THRESHOLD = 85  # 팔을 흔들었다고 감지할 최소 각도 (도). 필요시 조정하세요.
SWING_COUNT_TARGET = 3 # 목표 왕복 횟수
# -----------------

# 모터와 센서 객체를 생성합니다.
finger_motor1 = LargeMotor(FINGER_MOTOR_1_PORT)
finger_motor2 = LargeMotor(FINGER_MOTOR_2_PORT)
thumb_motor = LargeMotor(THUMB_MOTOR_PORT)
gyro_sensor = GyroSensor(GYRO_SENSOR_PORT)
touch_sensor = TouchSensor(TOUCH_SENSOR_PORT)

# '손 놓기' 동작을 수행하는 함수
def release_hand():
    "모터들을 초기 위치(0도)로 되돌립니다."
    print("손을 놓습니다...")
    finger_motor1.on_to_position(SpeedPercent(50), 0, block=False)
    finger_motor2.on_to_position(SpeedPercent(50), 0, block=False)
    thumb_motor.on_to_position(SpeedPercent(50), 0, block=False)
    finger_motor1.wait_until_not_moving()
    finger_motor2.wait_until_not_moving()
    thumb_motor.wait_until_not_moving()
    print("초기 위치로 복귀 완료.")

# --- 신규 추가된 함수 ---
def reset_motor_positions():
    "현재 모터 위치를 새로운 0도(초기 위치)로 설정합니다."
    print("모터 위치를 리셋합니다...")
    finger_motor1.reset()
    finger_motor2.reset()
    thumb_motor.reset()
    print("모터 위치 리셋 완료.")
# ----------------------

# 메인 프로그램 루프
print("로봇 핸드 제어 프로그램을 시작합니다. (Ctrl+C로 종료)")

# 자이로 센서 초기화
print("자이로 센서를 보정합니다. 팔을 움직이지 마세요...")
gyro_sensor.reset()
sleep(2)
print("보정 완료. 프로그램을 시작합니다.")

# 스윙 동작 상태 변수
swing_count = 0
swing_state = 'center' # 'center', 'positive', 'negative'

# 터치 센서 상태 변수
touch_state = 'released' # 'released', 'pressing', 'action_taken'
touch_press_time = 0

try:
    while True:
        # --- 1. 자이로 센서 감지 로직 ---
        angle = gyro_sensor.angle
        if swing_state == 'center':
            if angle > SWING_THRESHOLD: swing_state = 'positive'
            elif angle < -SWING_THRESHOLD: swing_state = 'negative'
        elif swing_state == 'positive':
            if angle < -SWING_THRESHOLD:
                swing_count += 1; swing_state = 'negative'
                print(f"왕복 감지! (횟수: {swing_count})")
        elif swing_state == 'negative':
            if angle > SWING_THRESHOLD:
                swing_count += 1; swing_state = 'positive'
                print(f"왕복 감지! (횟수: {swing_count})")

        if swing_count >= SWING_COUNT_TARGET:
            print(f"{SWING_COUNT_TARGET}번 왕복 감지 완료. 1.5초 후 손을 놓습니다.")
            sleep(1.5)
            release_hand()
            print("카운트를 초기화합니다...")
            swing_count = 0; swing_state = 'center'
            gyro_sensor.reset()
            sleep(5)

        # --- 2. 터치 센서 감지 로직 ---
        is_pressed = touch_sensor.is_pressed
        
        # 센서가 눌렸을 때
        if is_pressed:
            if touch_state == 'released':
                touch_state = 'pressing'
                touch_press_time = time()
            elif touch_state == 'pressing':
                if time() - touch_press_time >= 3:
                    print("터치 센서 3초 입력 감지. 1.5초 후 손을 놓습니다.")
                    sleep(1.5)
                    release_hand()
                    touch_state = 'action_taken' # 동작 수행 완료 상태
        # 센서에서 손을 뗐을 때
        else:
            if touch_state == 'pressing': # 짧은 클릭 후 손을 뗀 경우
                press_duration = time() - touch_press_time
                if 0.1 < press_duration < 2.0:
                    reset_motor_positions()
            # 상태 초기화
            touch_state = 'released'

        sleep(0.05) # 메인 루프 대기

except KeyboardInterrupt:
    print("프로그램을 종료합니다.")
    finger_motor1.off()
    finger_motor2.off()
    thumb_motor.off()
