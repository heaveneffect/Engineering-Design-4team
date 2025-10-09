#!/usr/bin/env python3

from ev3dev2.motor import LargeMotor, SpeedPercent
from ev3dev2.sensor.lego import UltrasonicSensor, TouchSensor
from time import sleep, time

FINGER_MOTOR_1_PORT = 'outA'
FINGER_MOTOR_2_PORT = 'outB'                     
THUMB_MOTOR_PORT = 'outC'
ULTRASONIC_SENSOR_PORT = 'in1'
TOUCH_SENSOR_PORT = 'in2'

# 동작 설정 (변수는 여기서 유동적으로 조절하면 됩니다.)  
GRASP_DEGREES = 60          # 손을 쥘 때의 각도
GRASP_SPEED = 25            # 손을 쥘 때의 속도
ULTRASONIC_DISTANCE_CM = 5  # 초음파 센서 감지 거리 (cm)
ULTRASONIC_DURATION_S = 3  # 초음파 센서 감지 시간 (초)
TOUCH_DURATION_S = 3        # 터치 센서 감지 시간 (초)
# --------------------

# --- 2. 하드웨어 준비 ---
# 3개의 모터와 2개의 센서 객체를 생성
finger_motor1 = LargeMotor(FINGER_MOTOR_1_PORT)
finger_motor2 = LargeMotor(FINGER_MOTOR_2_PORT)
thumb_motor = LargeMotor(THUMB_MOTOR_PORT)
ultrasonic_sensor = UltrasonicSensor(ULTRASONIC_SENSOR_PORT)
touch_sensor = TouchSensor(TOUCH_SENSOR_PORT)
# --------------------

# --- 3. 핵심 동작 함수 ---
def grasp_hand():
    """세 손가락을 동시에 쥐는 동작을 수행하는 함수"""
    print(f"{GRASP_DEGREES}도 만큼 손을 쥡니다...")
    # block=False를 이용해 세 모터가 동시에 움직이도록 명령합니다.
    finger_motor1.on_for_degrees(SpeedPercent(GRASP_SPEED), GRASP_DEGREES, block=False)
    finger_motor2.on_for_degrees(SpeedPercent(GRASP_SPEED), GRASP_DEGREES, block=False)
    # 마지막 모터는 block=True로 설정하여 모든 움직임이 끝날 때까지 기다립니다.
    thumb_motor.on_for_degrees(SpeedPercent(GRASP_SPEED), GRASP_DEGREES, block=True)
    print("동작 완료.")
# --------------------

# --- 4. 메인 프로그램 실행 ---
print("로봇 핸드 프로그램을 시작합니다. (두 조건 중 하나를 만족하면 종료)")

# 타이머 변수 초기화
ultrasonic_start_time = None
touch_start_time = None

try:
    # 무한 루프를 돌며 두 센서를 계속 확인합니다.
    while True:
        # --- 4-1. 초음파 센서 로직 ---
        distance = ultrasonic_sensor.distance_centimeters
        if distance < ULTRASONIC_DISTANCE_CM:
            if ultrasonic_start_time is None:
                ultrasonic_start_time = time()
                print(f"물체 감지 (거리: {distance:.1f} cm)")
            
            if time() - ultrasonic_start_time > ULTRASONIC_DURATION_S:
                print(f"초음파 센서 조건 만족 ({ULTRASONIC_DURATION_S}초 이상 감지).")
                grasp_hand() # 손 쥐기 함수 호출
                break        # 루프 탈출
        else:
            ultrasonic_start_time = None # 물체가 없으면 타이머 리셋

        # --- 4-2. 터치 센서 로직 ---
        if touch_sensor.is_pressed:
            if touch_start_time is None:
                touch_start_time = time()
                print("터치 센서 감지")

            if time() - touch_start_time > TOUCH_DURATION_S:
                print(f"터치 센서 조건 만족 ({TOUCH_DURATION_S}초 이상 감지).")
                grasp_hand() # 손 쥐기 함수 호출
                break        # 루프 탈출
        else:
            touch_start_time = None # 손을 떼면 타이머 리셋

        sleep(0.05) # 루프 대기

except KeyboardInterrupt:
    print("프로그램을 강제 종료합니다.")

finally:
    # 프로그램이 어떻게 끝나든 모터를 안전하게 정지시킵니다.      # 여기 파트는 코드 합칠 때 필요 없습니다.
    print("프로그램을 종료합니다.")
    finger_motor1.off()
    finger_motor2.off()
    thumb_motor.off()
# --------------
