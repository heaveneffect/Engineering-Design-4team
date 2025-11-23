//수정사항: 특수 공백 문자 삭제해서 오류 방지, 숫자 변수 (변수 미세 조정시 편의성 위해)  ,변수명 및 구조 통일되게 수정

// 자이로 센서 관련 로직만 수정 해주시면 됩니다!!



#!/usr/bin/env python3

# 필요한 라이브러리들을 가져옵니다.
from ev3dev2.motor import LargeMotor, SpeedPercent
from ev3dev2.sensor.lego import UltrasonicSensor, GyroSensor, TouchSensor
from ev3dev2.button import Button
from time import sleep, time

# ==========================================
# [설정] 포트 및 하드웨어 구성
# ==========================================
PORT_FINGER_1 = 'outA'
PORT_FINGER_2 = 'outB'
PORT_THUMB    = 'outC'

PORT_US    = 'in1'  # 초음파 센서
PORT_TOUCH_PALM = 'in2'  # 손바닥 터치 센서
PORT_TOUCH_SIDE = 'in3'  # 손날 터치 센서
PORT_GYRO  = 'in4'  # 자이로 센서

# ==========================================
# [설정] 동작 파라미터 (속도, 각도, 시간)
# ==========================================
# 모터 설정
GRASP_SPEED   = 15     # 잡을 때 속도 (%)
RELEASE_SPEED = 15     # 놓을 때 속도 (%)
GRASP_DEGREES = -300   # 잡을 때 회전 각도 (음수)

# 센서 임계값 및 타이머
US_DIST_THRESHOLD_CM = 5   # 초음파 감지 거리 (cm)
US_DETECT_DURATION   = 2   # 초음파 감지 지속 시간 (초)

SIDE_BTN_RESET_TIME  = 3.0 # 리셋을 위한 버튼 누름 시간 (초)

# 자이로 설정 
SWING_THRESHOLD    = 85
SWING_COUNT_TARGET = 3

# ==========================================
# [초기화] 하드웨어 객체 생성
# ==========================================
finger_motor1 = LargeMotor(PORT_FINGER_1)
finger_motor2 = LargeMotor(PORT_FINGER_2)
thumb_motor   = LargeMotor(PORT_THUMB)

ultrasonic_sensor = UltrasonicSensor(PORT_US)
palm_touch_sensor = TouchSensor(PORT_TOUCH_PALM)
side_touch_sensor = TouchSensor(PORT_TOUCH_SIDE)
gyro_sensor       = GyroSensor(PORT_GYRO)

buttons = Button()

# ==========================================
# [함수] 동작 정의
# ==========================================
def grasp_hand():
    """손을 쥐고 성공 여부를 반환합니다."""
    try:
        finger_motor1.on_for_degrees(SpeedPercent(GRASP_SPEED), GRASP_DEGREES, block=False)
        finger_motor2.on_for_degrees(SpeedPercent(GRASP_SPEED), GRASP_DEGREES, block=False)
        thumb_motor.on_for_degrees(SpeedPercent(GRASP_SPEED), GRASP_DEGREES, block=True)
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

# ==========================================
# [메인] 프로그램 실행
# ==========================================

# 자이로 센서 초기화
gyro_sensor.reset()
sleep(2)

# 상태 변수 초기화
hand_state = 'open'

ultrasonic_start_time = None

# 자이로 관련 변수
swing_count = 0
swing_state = 'center'

# 측면 버튼 관련 변수
side_touch_state = 'released'
side_touch_press_time = 0

try:
    while not buttons.backspace:
        
        # --- 1. 잡기 동작 (손이 열려 있을 때) ---
        if hand_state == 'open':
            # 1-1. 초음파 센서 감지
            distance = ultrasonic_sensor.distance_centimeters
            
            if distance < US_DIST_THRESHOLD_CM:
                if ultrasonic_start_time is None:
                    ultrasonic_start_time = time()
                
                # 감지 지속 시간 체크
                if time() - ultrasonic_start_time > US_DETECT_DURATION:
                    if grasp_hand():
                        hand_state = 'closed'
                    ultrasonic_start_time = None
                    sleep(1)
            else:
                ultrasonic_start_time = None

            # 1-2. 손바닥 터치 센서 감지
            if hand_state == 'open' and palm_touch_sensor.is_pressed:
                if grasp_hand():
                    hand_state = 'closed'
                sleep(1)

        # --- 2. 놓기 동작 (손이 닫혀 있을 때: 자이로) ---
        else: 
            # 자이로 로직 (요청하신 대로 원본 로직 유지)
            angle = gyro_sensor.angle
            
            if swing_state == 'center':
                if angle > SWING_THRESHOLD: 
                    swing_state = 'positive'
                elif angle < -SWING_THRESHOLD: 
                    swing_state = 'negative'
            elif swing_state == 'positive' and angle < -SWING_THRESHOLD:
                swing_count += 1
                swing_state = 'negative'
            elif swing_state == 'negative' and angle > SWING_THRESHOLD:
                swing_count += 1
                swing_state = 'positive'

            if swing_count >= SWING_COUNT_TARGET:
                sleep(1.5)
                if release_hand():
                    hand_state = 'open'
                
                # 자이로 상태 리셋
                swing_count = 0
                swing_state = 'center'
                gyro_sensor.reset()
                sleep(3)

        # --- 3. 측면 버튼 (수동 놓기 / 리셋) ---
        side_is_pressed = side_touch_sensor.is_pressed
        
        if side_is_pressed:
            if side_touch_state == 'released':
                side_touch_state = 'pressing'
                side_touch_press_time = time()
            
            elif side_touch_state == 'pressing':
                # 3초 이상 길게 누르면 리셋
                if time() - side_touch_press_time >= SIDE_BTN_RESET_TIME:
                    reset_motor_positions()
                    side_touch_state = 'action_taken' # 중복 동작 방지
        
        else: # 버튼을 뗐을 때
            if side_touch_state == 'pressing':
                press_duration = time() - side_touch_press_time
                
                # 짧은 클릭(0.1~2초) 시 손 놓기 동작
                if 0.1 < press_duration < 2.0 and hand_state == 'closed':
                    if release_hand():
                        hand_state = 'open'
            
            side_touch_state = 'released'

        sleep(0.05)

except KeyboardInterrupt:
    # 종료 시 모터 정지
    finger_motor1.off()
    finger_motor2.off()
    thumb_motor.off()
