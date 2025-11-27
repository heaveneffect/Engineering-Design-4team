#!/usr/bin/env python3

# 필요한 라이브러리들을 가져옵니다.
from ev3dev2.motor import LargeMotor, SpeedPercent
from ev3dev2.sensor.lego import UltrasonicSensor, GyroSensor, TouchSensor
from ev3dev2.button import Button 
from time import sleep, time

# --- 중요: 포트 설정 ---
# 모든 센서 포트를 실제 로봇에 맞게 수정해주세요.
FINGER_MOTOR_1_PORT = 'outA'
FINGER_MOTOR_2_PORT = 'outB'
THUMB_MOTOR_PORT = 'outC'
ULTRASONIC_SENSOR_PORT = 'in1'
PALM_TOUCH_SENSOR_PORT = 'in2' # 손바닥 터치 센서
SIDE_TOUCH_SENSOR_PORT = 'in3' # 손날 터치 센서
GYRO_SENSOR_PORT = 'in4'
# --------------------

# --- 동작 설정 ---
GRASP_DEGREES = -400
GRASP_SPEED = 15


RELEASE_SPEED = 15
THUMB_RELEASE_SP = 5

ULTRASONIC_DISTANCE_CM = 5
ULTRASONIC_DURATION_S = 2

# 자이로 센서 놓기 동작을 위한 설정
ROTATION_ANGLE_THRESHOLD = 90  # 회전 감지 각도
ROTATION_TIME_INTERVAL = 1.0   # 각도 측정 시간 간격 (초)
ROTATION_COUNT_TARGET = 2      # 목표 회전 횟수
# -----------------

# --- 하드웨어 준비 ---
finger_motor1 = LargeMotor(FINGER_MOTOR_1_PORT)
finger_motor2 = LargeMotor(FINGER_MOTOR_2_PORT)
thumb_motor = LargeMotor(THUMB_MOTOR_PORT)
ultrasonic_sensor = UltrasonicSensor(ULTRASONIC_SENSOR_PORT)
palm_touch_sensor = TouchSensor(PALM_TOUCH_SENSOR_PORT)
side_touch_sensor = TouchSensor(SIDE_TOUCH_SENSOR_PORT)
gyro_sensor = GyroSensor(GYRO_SENSOR_PORT)
buttons = Button() 
# --------------------

# --- 핵심 동작 함수들 ---
def grasp_hand():
    """손을 쥐고 성공 여부를 반환합니다."""
    
    try:
        finger_motor1.on_for_degrees(SpeedPercent(GRASP_SPEED), GRASP_DEGREES, block=False)
        finger_motor2.on_for_degrees(SpeedPercent(GRASP_SPEED), GRASP_DEGREES, block=False)
        thumb_motor.on_for_degrees(SpeedPercent(THUMB_RELEASE_SP), 200, block=True)
        return True
    except Exception:
        return False

def release_hand():
    """손을 놓고 성공 여부를 반환합니다."""
    try:
        finger_motor1.on_to_position(SpeedPercent(RELEASE_SPEED), 0, block=False)
        finger_motor2.on_to_position(SpeedPercent(RELEASE_SPEED), 0, block=False)
        thumb_motor.on_to_position(SpeedPercent(RELEASE_SPEED), 0, block=True)
        return True
    except Exception:
        return False

def reset_motor_positions():
    """현재 모터 위치를 새로운 0도로 설정합니다."""

    finger_motor1.reset()
    finger_motor2.reset()
    thumb_motor.reset()
# -------------------------

# --- 메인 프로그램 실행 ---

# 자이로 센서 초기화
gyro_sensor.reset()
sleep(2)

# --- 상태 및 타이머 변수 초기화 ---
hand_state = 'open'
ultrasonic_start_time = None

# 자이로 센서 관련 변수
last_check_time = time()
last_angle = gyro_sensor.angle
rotation_direction = 0  # 0: 중심, 1: +, -1: -
rotation_count = 0

side_touch_state = 'released'
side_touch_press_time = 0
# --------------------------------

try:
    while not buttons.backspace:
        # --- 1. 잡기 동작 로직 (손이 열려 있을 때) ---
        if hand_state == 'open':
            # 1-1. 초음파 센서로 잡기
            distance = ultrasonic_sensor.distance_centimeters
            if distance < ULTRASONIC_DISTANCE_CM:
                if ultrasonic_start_time is None:
                    ultrasonic_start_time = time()
                if time() - ultrasonic_start_time > ULTRASONIC_DURATION_S:
                    if grasp_hand():
                        hand_state = 'closed'
                        # 잡기 성공 후 자이로 관련 변수 초기화
                        last_check_time = time()
                        last_angle = gyro_sensor.angle
                        rotation_direction = 0
                        rotation_count = 0
                    ultrasonic_start_time = None
                    sleep(1)
            else:
                ultrasonic_start_time = None

            # 1-2. 손바닥 터치 센서로 잡기 (이미 잡는 중이 아닐 때)
            if hand_state == 'open' and palm_touch_sensor.is_pressed:
                if grasp_hand():
                    hand_state = 'closed'
                    # 잡기 성공 후 자이로 관련 변수 초기화
                    last_check_time = time()
                    last_angle = gyro_sensor.angle
                    rotation_direction = 0
                    rotation_count = 0
                sleep(1)

        # --- 2. 놓기 동작 로직 (손이 닫혀 있을 때) ---
        else: # hand_state == 'closed'
            current_time = time()
            # 2-1. 자이로 센서로 놓기 (1초 간격으로 체크)
            if current_time - last_check_time >= ROTATION_TIME_INTERVAL:
                current_angle = gyro_sensor.angle
                angle_change = current_angle - last_angle

                # 1단계: 첫 번째 회전 감지
                if rotation_direction == 0:
                    if angle_change > ROTATION_ANGLE_THRESHOLD:
                        rotation_direction = 1  # 양의 방향으로 회전 감지
                    elif angle_change < -ROTATION_ANGLE_THRESHOLD:
                        rotation_direction = -1 # 음의 방향으로 회전 감지
                
                # 2단계: 반대 방향 회전 감지
                elif rotation_direction == 1:
                    if angle_change < -ROTATION_ANGLE_THRESHOLD:
                        rotation_count += 1
                        rotation_direction = 0 # 카운트 후 초기화
                elif rotation_direction == -1:
                    if angle_change > ROTATION_ANGLE_THRESHOLD:
                        rotation_count += 1
                        rotation_direction = 0 # 카운트 후 초기화
                
                # 다음 측정을 위해 현재 상태 저장
                last_check_time = current_time
                last_angle = current_angle

            # 목표 회전 횟수 도달 시 손 놓기
            if rotation_count >= ROTATION_COUNT_TARGET:
                if release_hand():
                    hand_state = 'open'
                # 변수 초기화
                rotation_count = 0
                rotation_direction = 0
                gyro_sensor.reset()
                sleep(2) # 안정화 시간

        # --- 3. 손날 터치 센서 로직 (놓기/리셋) ---
        side_is_pressed = side_touch_sensor.is_pressed
        if side_is_pressed:
            if side_touch_state == 'released':
                side_touch_state = 'pressing'
                side_touch_press_time = time()
            elif side_touch_state == 'pressing':
                # 3초 이상 길게 누르면 리셋
                if time() - side_touch_press_time >= 3:
                    reset_motor_positions()
                    side_touch_state = 'action_taken' # 동작 수행 완료
        else: # 손을 뗐을 때
            if side_touch_state == 'pressing':
                press_duration = time() - side_touch_press_time
                # 짧은 클릭(0.1~2초) 시 놓기
                if 0.1 < press_duration < 2.0 and hand_state == 'closed':
                    if release_hand():
                        hand_state = 'open'
                    # 놓기 성공 후 자이로 관련 변수 초기화
                    rotation_count = 0
                    rotation_direction = 0
            side_touch_state = 'released'

        sleep(0.05)

except KeyboardInterrupt:
    pass

finally:
    finger_motor1.off()
    finger_motor2.off()
    thumb_motor.off()
