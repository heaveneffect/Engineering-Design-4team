#!/usr/bin/env python3

# 필요한 라이브러리들을 가져옵니다.
from ev3dev2.motor import LargeMotor, SpeedPercent
from ev3dev2.sensor.lego import UltrasonicSensor, GyroSensor, TouchSensor
from ev3dev2.button import Button 
from time import sleep, time

# --- 포트 설정 ---
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
GRASP_DEGREES = -300
GRASP_SPEED = 15
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
    
    try:
        finger_motor1.on_for_degrees(SpeedPercent(GRASP_SPEED), GRASP_DEGREES, block=False)
        finger_motor2.on_for_degrees(SpeedPercent(GRASP_SPEED), GRASP_DEGREES, block=False)
        thumb_motor.on_for_degrees(SpeedPercent(GRASP_SPEED), GRASP_DEGREES, block=True)
        
        return True
    except Exception as e:
        
        return False

def release_hand():
    """손을 놓고 성공 여부를 반환합니다."""
    
    try:
        finger_motor1.on_to_position(SpeedPercent(15), 0, block=False)
        finger_motor2.on_to_position(SpeedPercent(15), 0, block=False)
        thumb_motor.on_to_position(SpeedPercent(15), 0, block=True)
        
        return True
    except Exception as e:
        
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
swing_count = 0
swing_state = 'center'
side_touch_state = 'released'
side_touch_press_time = 0
# --------------------------------

try:
    #
    while not buttons.backspace:
        # --- 1 잡기 동작 로직 (손이 열려 있을 때) ---
        if hand_state == 'open':
            # 1-1 초음파 센서로 잡기
            distance = ultrasonic_sensor.distance_centimeters
            if distance < ULTRASONIC_DISTANCE_CM:
                if ultrasonic_start_time is None:
                    ultrasonic_start_time = time()
                if time() - ultrasonic_start_time > ULTRASONIC_DURATION_S:
                    
                    if grasp_hand():
                        hand_state = 'closed'
                        
                    ultrasonic_start_time = None
                    sleep(1)
            else:
                ultrasonic_start_time = None

            # 1-2 손바닥 터치 센서로 잡기 (이미 잡는 중이 아닐 때)
            if hand_state == 'open' and palm_touch_sensor.is_pressed:
                
                if grasp_hand():
                    hand_state = 'closed'
                    
                sleep(1)

        # --- 2 놓기 동작 로직 (손이 닫혀 있을 때) ---
        else: 
            # 2-1 자이로 센서로 놓기
            angle = gyro_sensor.angle
            if swing_state == 'center':
                if angle > SWING_THRESHOLD: swing_state = 'positive'
                elif angle < -SWING_THRESHOLD: swing_state = 'negative'
            elif swing_state == 'positive' and angle < -SWING_THRESHOLD:
                swing_count += 1; swing_state = 'negative'; 
            elif swing_state == 'negative' and angle > SWING_THRESHOLD:
                swing_count += 1; swing_state = 'positive'; 

            if swing_count >= SWING_COUNT_TARGET:
                
                sleep(1.5)
                if release_hand():
                    hand_state = 'open'
                    
                swing_count = 0; swing_state = 'center'; gyro_sensor.reset(); sleep(3)

        # --- 3 손날 터치 센서 로직 (놓기/리셋) ---
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
                        
            side_touch_state = 'released'

        sleep(0.05)

except KeyboardInterrupt:
    
    finger_motor1.off()
    finger_motor2.off()
    thumb_motor.off()