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
GRASP_DEGREES = 60
GRASP_SPEED = 25
ULTRASONIC_DISTANCE_CM = 5
ULTRASONIC_DURATION_S = 2

SWING_THRESHOLD = 85
SWING_COUNT_TARGET = 3
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
    print(f"{GRASP_DEGREES}도 만큼 손을 쥡니다...")
    try:
        finger_motor1.on_for_degrees(SpeedPercent(GRASP_SPEED), GRASP_DEGREES, block=False)
        finger_motor2.on_for_degrees(SpeedPercent(GRASP_SPEED), GRASP_DEGREES, block=False)
        thumb_motor.on_for_degrees(SpeedPercent(GRASP_SPEED), GRASP_DEGREES, block=True)
        print("잡기 동작 완료.")
        return True
    except Exception as e:
        print(f"잡기 동작 중 오류 발생: {e}")
        return False

def release_hand():
    """손을 놓고 성공 여부를 반환합니다."""
    print("손을 놓습니다...")
    try:
        finger_motor1.on_to_position(SpeedPercent(50), 0, block=False)
        finger_motor2.on_to_position(SpeedPercent(50), 0, block=False)
        thumb_motor.on_to_position(SpeedPercent(50), 0, block=True)
        print("놓기 동작 완료.")
        return True
    except Exception as e:
        print(f"놓기 동작 중 오류 발생: {e}")
        return False

def reset_motor_positions():
    """현재 모터 위치를 새로운 0도로 설정합니다."""
    print("모터 위치를 리셋합니다...")
    finger_motor1.reset()
    finger_motor2.reset()
    thumb_motor.reset()
    print("모터 위치 리셋 완료.")
# -------------------------

# --- 메인 프로그램 실행 ---
print("모든 센서를 사용하는 최종 로봇 핸드 프로그램을 시작합니다.")
print("종료하려면 EV3의 '뒤로 가기' 버튼을 누르세요.") # <<< 안내 메시지 추가

# 자이로 센서 초기화
print("자이로 센서를 보정합니다. 팔을 움직이지 마세요...")
gyro_sensor.reset()
sleep(2)
print("보정 완료.")

# --- 상태 및 타이머 변수 초기화 ---
hand_state = 'open'
print(f"초기 상태: {hand_state}")

ultrasonic_start_time = None
swing_count = 0
swing_state = 'center'
side_touch_state = 'released'
side_touch_press_time = 0
# --------------------------------

try:
    # <<< 변경점: 루프 조건을 '뒤로 가기' 버튼이 눌리지 않는 동안으로 변경
    while not buttons.backspace:
        # --- 1. 잡기 동작 로직 (손이 열려 있을 때) ---
        if hand_state == 'open':
            # 1-1. 초음파 센서로 잡기
            distance = ultrasonic_sensor.distance_centimeters
            if distance < ULTRASONIC_DISTANCE_CM:
                if ultrasonic_start_time is None:
                    ultrasonic_start_time = time()
                if time() - ultrasonic_start_time > ULTRASONIC_DURATION_S:
                    print("초음파 센서 감지. 잡기 시도...")
                    if grasp_hand():
                        hand_state = 'closed'
                        print(f"상태 변경: {hand_state}")
                    ultrasonic_start_time = None
                    sleep(1)
            else:
                ultrasonic_start_time = None

            # 1-2. 손바닥 터치 센서로 잡기 (이미 잡는 중이 아닐 때)
            if hand_state == 'open' and palm_touch_sensor.is_pressed:
                print("손바닥 터치 감지. 잡기 시도...")
                if grasp_hand():
                    hand_state = 'closed'
                    print(f"상태 변경: {hand_state}")
                sleep(1)

        # --- 2. 놓기 동작 로직 (손이 닫혀 있을 때) ---
        else: # hand_state == 'closed'
            # 2-1. 자이로 센서로 놓기
            angle = gyro_sensor.angle
            if swing_state == 'center':
                if angle > SWING_THRESHOLD: swing_state = 'positive'
                elif angle < -SWING_THRESHOLD: swing_state = 'negative'
            elif swing_state == 'positive' and angle < -SWING_THRESHOLD:
                swing_count += 1; swing_state = 'negative'; print(f"왕복 감지! ({swing_count})")
            elif swing_state == 'negative' and angle > SWING_THRESHOLD:
                swing_count += 1; swing_state = 'positive'; print(f"왕복 감지! ({swing_count})")

            if swing_count >= SWING_COUNT_TARGET:
                print(f"{SWING_COUNT_TARGET}번 왕복 감지. 놓기 시도...")
                sleep(1.5)
                if release_hand():
                    hand_state = 'open'
                    print(f"상태 변경: {hand_state}")
                swing_count = 0; swing_state = 'center'; gyro_sensor.reset(); sleep(3)

        # --- 3. 손날 터치 센서 로직 (놓기/리셋) ---
        side_is_pressed = side_touch_sensor.is_pressed
        if side_is_pressed:
            if side_touch_state == 'released':
                side_touch_state = 'pressing'
                side_touch_press_time = time()
            elif side_touch_state == 'pressing':
                # 3초 이상 길게 누르면 리셋
                if time() - side_touch_press_time >= 3:
                    print("손날 터치 3초 입력 감지. 모터 위치 리셋 시도...")
                    reset_motor_positions()
                    side_touch_state = 'action_taken' # 동작 수행 완료
        else: # 손을 뗐을 때
            if side_touch_state == 'pressing':
                press_duration = time() - side_touch_press_time
                # 짧은 클릭(0.1~2초) 시 놓기
                if 0.1 < press_duration < 2.0 and hand_state == 'closed':
                    print("손날 터치 짧은 입력 감지. 놓기 시도...")
                    if release_hand():
                        hand_state = 'open'
                        print(f"상태 변경: {hand_state}")
            side_touch_state = 'released'

        sleep(0.05)

except KeyboardInterrupt:
    # Ctrl+C로 종료 시 메시지
    print("\n프로그램을 강제 종료합니다. (키보드 입력)")

finally:
    # '뒤로 가기' 버튼으로 루프가 정상 종료되었을 때 메시지
    if buttons.backspace:
        print("\n'뒤로 가기' 버튼 입력으로 프로그램을 종료합니다.")
    
    print("프로그램을 종료하며 모터를 정지합니다.")
    finger_motor1.off()
    finger_motor2.off()
    thumb_motor.off()
