import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
import sys

class HeadMouseController:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.8,
            min_tracking_confidence=0.8
        )

        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.001

        self.screen_w, self.screen_h = pyautogui.size()
        self.screen_center = np.array([self.screen_w // 2, self.screen_h // 2], dtype=np.float64)

        self.pos_filter = self.screen_center.copy()
        self.prev_pos = self.screen_center.copy()
        self.deadzone_radius = 0.01 * min(self.screen_w, self.screen_h)

        self.NOSE_TIP = 1

        self.LEFT_EYE_POINTS = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE_POINTS = [362, 385, 387, 263, 373, 380]
        self.MOUTH_POINTS = [13, 14, 78, 308]

        self.calibrated = False
        self.calibration_stage = 0
        self.calibration_data = {
            'center': [],
            'left': [],
            'right': [],
            'up': [],
            'down': []
        }
        self.current_calibration_stage_frames = 0
        self.CALIBRATION_STAGE_DURATION = 90
        self.CALIBRATION_GUIDE_TEXTS = {
            0: "Preparazione calibrazione...",
            1: "GUARDA DRITTO AL CENTRO",
            2: "GUARDA IL PIÙ A SINISTRA POSSIBILE",
            3: "GUARDA IL PIÙ A DESTRA POSSIBILE",
            4: "GUARDA IL PIÙ IN ALTO POSSIBILE",
            5: "GUARDA IL PIÙ IN BASSO POSSIBILE",
            6: "Elaborazione dati...",
            7: "CALIBRATO! Mouse Attivo."
        }
        self.last_calibration_text_update = time.time()
        self.calibration_text_cooldown = 1.0

        self.movement_range = {'min_x': 0, 'max_x': 0, 'min_y': 0, 'max_y': 0}
        self.MARGIN_FACTOR = 0.15

        self.nose_pos_history = []
        self.ACCELERATION_HISTORY_LENGTH = 3
        self.ACCELERATION_THRESHOLD_X = 200
        self.ACCELERATION_THRESHOLD_Y = 200
        self.ACCELERATION_THRESHOLD_MAGNITUDE = 300

        self.BLINK_THRESHOLD = 0.22
        self.MOUTH_THRESHOLD = 0.35
        self.eye_history = []
        self.mouth_history = []
        self.HISTORY_LENGTH = 5

        self.STILL_TIME_THRESHOLD = 1.0
        self.last_movement_time = time.time()
        self.is_still = False
        self.STILL_MOVEMENT_THRESHOLD = 5

        self.last_left_click_time = 0.0
        self.last_right_click_time = 0.0
        self.last_double_click_time = 0.0
        self.CLICK_COOLDOWN = 0.7

        self.FILTER_STRENGTH = 0.2

    def _get_ear(self, landmarks, eye_points):
        try:
            p1 = landmarks[eye_points[0]]
            p2 = landmarks[eye_points[1]]
            p3 = landmarks[eye_points[2]]
            p4 = landmarks[eye_points[3]]
            p5 = landmarks[eye_points[4]]
            p6 = landmarks[eye_points[5]]

            vertical1_dist = np.linalg.norm(p2 - p6)
            vertical2_dist = np.linalg.norm(p3 - p5)
            horizontal_dist = np.linalg.norm(p1 - p4)

            ear = (vertical1_dist + vertical2_dist) / (2.0 * horizontal_dist) if horizontal_dist != 0 else 0
            return ear
        except IndexError:
            return 0

    def _get_mar(self, landmarks):
        try:
            p_top = landmarks[self.MOUTH_POINTS[0]]
            p_bottom = landmarks[self.MOUTH_POINTS[1]]
            p_right = landmarks[self.MOUTH_POINTS[2]]
            p_left = landmarks[self.MOUTH_POINTS[3]]

            vertical_dist = np.linalg.norm(p_top - p_bottom)
            horizontal_dist = np.linalg.norm(p_right - p_left)

            mar = vertical_dist / horizontal_dist if horizontal_dist != 0 else 0
            return mar
        except IndexError:
            return 0

    def calibrate_movement_range(self, nose_pos):
        if self.calibration_stage == 0:
            if time.time() - self.last_calibration_text_update > self.calibration_text_cooldown * 2:
                self.calibration_stage = 1
                self.current_calibration_stage_frames = 0
                self.last_calibration_text_update = time.time()
            return

        stage_key = {
            1: 'center',
            2: 'left',
            3: 'right',
            4: 'up',
            5: 'down'
        }.get(self.calibration_stage)

        if stage_key:
            self.calibration_data[stage_key].append(nose_pos)
            self.current_calibration_stage_frames += 1

            if self.current_calibration_stage_frames >= self.CALIBRATION_STAGE_DURATION:
                self.calibration_stage += 1
                self.current_calibration_stage_frames = 0
                self.last_calibration_text_update = time.time()
                self.nose_pos_history = []
                self.pos_filter = self.screen_center.copy()
                self.prev_pos = self.screen_center.copy()

        if self.calibration_stage == 6:
            all_x = []
            all_y = []

            center_data = np.array(self.calibration_data['center'])
            if center_data.size > 0:
                center_x_avg = np.mean(center_data[:, 0])
                center_y_avg = np.mean(center_data[:, 1])
            else:
                center_x_avg = nose_pos[0]
                center_y_avg = nose_pos[1]
                print("[WARNING] Dati di calibrazione 'center' insufficienti. Usando posizione attuale.")

            for key in ['left', 'right', 'up', 'down']:
                if self.calibration_data[key]:
                    data = np.array(self.calibration_data[key])
                    all_x.extend(data[:, 0])
                    all_y.extend(data[:, 1])

            if not all_x or not all_y:
                print("[ERROR] Calibrazione fallita: Dati insufficienti per definire il range di movimento.")
                self.calibrated = False
                self.calibration_stage = 0 # Reset calibration
                return

            self.movement_range['min_x'] = min(all_x)
            self.movement_range['max_x'] = max(all_x)
            self.movement_range['min_y'] = min(all_y)
            self.movement_range['max_y'] = max(all_y)

            x_range = self.movement_range['max_x'] - self.movement_range['min_x']
            y_range = self.movement_range['max_y'] - self.movement_range['min_y']

            self.movement_range['min_x'] -= x_range * self.MARGIN_FACTOR
            self.movement_range['max_x'] += x_range * self.MARGIN_FACTOR
            self.movement_range['min_y'] -= y_range * self.MARGIN_FACTOR
            self.movement_range['max_y'] += y_range * self.MARGIN_FACTOR

            # Adjust range to be centered around the initially detected center position
            current_mid_x = (self.movement_range['min_x'] + self.movement_range['max_x']) / 2
            current_mid_y = (self.movement_range['min_y'] + self.movement_range['max_y']) / 2

            offset_x = center_x_avg - current_mid_x
            offset_y = center_y_avg - current_mid_y

            self.movement_range['min_x'] += offset_x
            self.movement_range['max_x'] += offset_x
            self.movement_range['min_y'] += offset_y
            self.movement_range['max_y'] += offset_y

            self.calibrated = True
            self.calibration_stage = 7
            print(f"Calibrato! Area movimento X: {self.movement_range['min_x']:.0f}-{self.movement_range['max_x']:.0f} "
                  f"Y: {self.movement_range['min_y']:.0f}-{self.movement_range['max_y']:.0f}")
            self.calibration_data = {k: [] for k in self.calibration_data} # Clear data

    def smooth_movement(self, target_pos):
        self.pos_filter = self.pos_filter * (1 - self.FILTER_STRENGTH) + target_pos * self.FILTER_STRENGTH

        movement_vector = self.pos_filter - self.prev_pos
        distance_sq = np.dot(movement_vector, movement_vector)

        if distance_sq < self.deadzone_radius**2:
            return self.prev_pos.copy()

        distance = np.sqrt(distance_sq)
        acceleration_full_strength_distance = self.deadzone_radius * 3
        raw_acceleration = (distance - self.deadzone_radius) / (acceleration_full_strength_distance - self.deadzone_radius)
        acceleration = max(0.0, min(1.0, raw_acceleration))

        new_pos = self.prev_pos + movement_vector * acceleration

        new_pos[0] = np.clip(new_pos[0], 0, self.screen_w - 1)
        new_pos[1] = np.clip(new_pos[1], 0, self.screen_h - 1)

        return new_pos

    def _calculate_nose_acceleration(self):
        if len(self.nose_pos_history) < self.ACCELERATION_HISTORY_LENGTH:
            return np.array([0.0, 0.0])

        p_t = self.nose_pos_history[-1]
        p_t_minus_1 = self.nose_pos_history[-2]
        p_t_minus_2 = self.nose_pos_history[-3]

        v_t = p_t - p_t_minus_1
        v_t_minus_1 = p_t_minus_1 - p_t_minus_2

        acceleration = v_t - v_t_minus_1
        return acceleration

    def _is_blinking(self, ear_history, eye_index):
        if not ear_history:
            return False
        return all(ear[eye_index] < self.BLINK_THRESHOLD for ear in ear_history)

    def _is_mouth_open(self, mouth_history):
        if not mouth_history:
            return False
        return all(mr > self.MOUTH_THRESHOLD for mr in mouth_history)

    def detect_gestures(self, nose_pos, left_ear, right_ear, mouth_ratio):
        self.nose_pos_history.append(nose_pos)
        while len(self.nose_pos_history) > self.ACCELERATION_HISTORY_LENGTH:
            self.nose_pos_history.pop(0)

        current_time = time.time()

        if len(self.nose_pos_history) > 1:
            movement = np.linalg.norm(self.nose_pos_history[-1] - self.nose_pos_history[-2])
            if movement > self.STILL_MOVEMENT_THRESHOLD:
                self.last_movement_time = current_time
                self.is_still = False
            else:
                if (current_time - self.last_movement_time) >= self.STILL_TIME_THRESHOLD:
                    self.is_still = True
                else:
                    self.is_still = False

        self.eye_history.append((left_ear, right_ear))
        self.mouth_history.append(mouth_ratio)
        while len(self.eye_history) > self.HISTORY_LENGTH:
            self.eye_history.pop(0)
            self.mouth_history.pop(0)

        is_left_blinking = self._is_blinking(self.eye_history, 0)
        is_right_blinking = self._is_blinking(self.eye_history, 1)
        is_mouth_open = self._is_mouth_open(self.mouth_history)

        if self.is_still and (current_time - self.last_left_click_time > self.CLICK_COOLDOWN):
            pyautogui.click()
            self.last_left_click_time = current_time
            self.is_still = False
            print(f"[ACTION] Left click (Still for {self.STILL_TIME_THRESHOLD}s)")

        elif is_left_blinking and not is_right_blinking and \
             (current_time - self.last_right_click_time > self.CLICK_COOLDOWN):
            pyautogui.click(button='right')
            self.last_right_click_time = current_time
            print("[ACTION] Right click (Left wink)")

        elif is_right_blinking and not is_left_blinking and \
             (current_time - self.last_right_click_time > self.CLICK_COOLDOWN):
            pyautogui.click(button='right')
            self.last_right_click_time = current_time
            print("[ACTION] Right click (Right wink)")

        elif is_mouth_open and (current_time - self.last_double_click_time > self.CLICK_COOLDOWN):
            pyautogui.doubleClick()
            self.last_double_click_time = current_time
            print("[ACTION] Double click (Mouth open)")

    def draw_interface(self, frame, nose_pos, left_ear, right_ear, mouth_ratio, nose_acceleration):
        h, w = frame.shape[:2]

        if self.calibrated:
            cv2.rectangle(frame,
                        (int(self.movement_range['min_x']), int(self.movement_range['min_y'])),
                        (int(self.movement_range['max_x']), int(self.movement_range['max_y'])),
                        (0, 255, 0), 2)
            cv2.circle(frame, tuple(nose_pos.astype(int)), 8, (0, 255, 0), -1)
            status_text = self.CALIBRATION_GUIDE_TEXTS[7] # "CALIBRATO! Mouse Attivo."
            color = (0, 255, 0)
        else:
            status_text = self.CALIBRATION_GUIDE_TEXTS[self.calibration_stage]
            color = (0, 255, 255)
            if self.calibration_stage > 0 and self.calibration_stage < 6:
                progress_text = f" ({self.current_calibration_stage_frames}/{self.CALIBRATION_STAGE_DURATION})"
                status_text += progress_text
            cv2.circle(frame, tuple(nose_pos.astype(int)), 8, (0, 165, 255), -1)

        cv2.putText(frame, status_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        if self.calibrated:
            cv2.putText(frame, f"Pos: {int(nose_pos[0])},{int(nose_pos[1])}", (20, 80),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, f"Occhi: L={left_ear:.2f} R={right_ear:.2f} (Soglia: {self.BLINK_THRESHOLD:.2f})", (20, 110),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, f"Bocca: {mouth_ratio:.2f} (Soglia: {self.MOUTH_THRESHOLD:.2f})", (20, 140),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            still_status = "FERMO" if self.is_still else "MUOVENDOSI"
            still_color = (0, 255, 0) if self.is_still else (0, 165, 255)
            cv2.putText(frame, f"Stato: {still_status} ({time.time() - self.last_movement_time:.1f}s)", (20, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.6, still_color, 1)

            cv2.putText(frame, "Mantieni FERMO (>=1.0s): Click SX", (20, h-100),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, "Ammicca un occhio: Click DX", (20, h-70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, "Bocca APERTA: Doppio click", (20, h-40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

def main():
    print("="*60)
    print("HEAD MOUSE CONTROLLER ULTIMATE")
    print("="*60)
    print("Controllo del mouse tramite movimenti del capo e gesti facciali.")
    print("Include calibrazione guidata per una precisione ottimale.")
    print("="*60)

    controller = HeadMouseController()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Errore: Impossibile aprire la webcam. Controlla che sia connessa e non in uso.")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 60)

    try:
        current_nose_acceleration = np.array([0.0, 0.0])

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Avviso: Impossibile leggere il frame dalla webcam. Terminazione.")
                break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            results = controller.face_mesh.process(rgb_frame)

            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                h, w = frame.shape[:2]
                landmarks_np = np.array([[lm.x * w, lm.y * h] for lm in face_landmarks.landmark], dtype=np.float64)

                nose_pos = landmarks_np[controller.NOSE_TIP]

                if not controller.calibrated:
                    controller.calibrate_movement_range(nose_pos)

                if controller.calibrated:
                    norm_x = np.interp(nose_pos[0],
                                       [controller.movement_range['min_x'], controller.movement_range['max_x']],
                                       [0, controller.screen_w])
                    norm_y = np.interp(nose_pos[1],
                                       [controller.movement_range['min_y'], controller.movement_range['max_y']],
                                       [0, controller.screen_h])

                    target_pos = np.array([norm_x, norm_y], dtype=np.float64)
                    smooth_pos = controller.smooth_movement(target_pos)
                    pyautogui.moveTo(smooth_pos[0], smooth_pos[1])
                    controller.prev_pos = smooth_pos

                left_ear = controller._get_ear(landmarks_np, controller.LEFT_EYE_POINTS)
                right_ear = controller._get_ear(landmarks_np, controller.RIGHT_EYE_POINTS)
                mouth_ratio = controller._get_mar(landmarks_np)
                if controller.calibrated: # Only detect gestures after calibration is complete
                    controller.detect_gestures(nose_pos, left_ear, right_ear, mouth_ratio)

                current_nose_acceleration = controller._calculate_nose_acceleration()

                controller.draw_interface(frame, nose_pos, left_ear, right_ear, mouth_ratio, current_nose_acceleration)
            else:
                controller.nose_pos_history = []
                controller.is_still = False
                if controller.calibrated:
                    # If face disappears after calibration, reset filter to screen center
                    controller.pos_filter = controller.screen_center.copy()
                    controller.prev_pos = controller.screen_center.copy()


            cv2.imshow('Head Mouse Ultimate', frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

    except Exception as e:
        print(f"Errore inatteso: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Disattivazione completata.")

if __name__ == "__main__":
    main()