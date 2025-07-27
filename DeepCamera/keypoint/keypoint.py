from ultralytics import YOLO
import cv2
import numpy as np
import time
import json

# YOLO keypoint names
YOLO_KEYPOINT_NAMES = {
    0: "nose",
    1: "left_eye",
    2: "right_eye",
    3: "left_ear",
    4: "right_ear",
    5: "left_shoulder",
    6: "right_shoulder",
    7: "left_elbow",
    8: "right_elbow",
    9: "left_wrist",
    10: "right_wrist",
    11: "left_hip",
    12: "right_hip",
    13: "left_knee",
    14: "right_knee",
    15: "left_ankle",
    16: "right_ankle",
    17: "left_foot",
    18: "right_foot"
}

# YOLO keypoint indices mapping to MediaPipe indices
# Reference: https://docs.ultralytics.com/tasks/pose/
YOLO_TO_MEDIAPIPE = {
    5: 11,   # left shoulder
    6: 12,   # right shoulder
    7: 13,   # left elbow
    8: 14,   # right elbow
    9: 15,   # left wrist
    10: 16,  # right wrist
    11: 23,  # left hip
    12: 24,  # right hip
    13: 25,  # left knee
    14: 26,  # right knee
    15: 27,  # left ankle
    16: 28,  # right ankle
    17: 31,  # left foot
    18: 32,  # right foot
}

# Define the mapping from MediaPipe indices to Unity bone names
KEYPOINT_TO_UNITY_MAP = {
    23: ["bn_spine01", "bn_thigh01.L"],  # Hips and LeftUpperLeg
    24: ["bn_spine02", "bn_spine03", "bn_spine04", "bn_thigh01.R"],  # Spine series and RightUpperLeg
    11: ["bn_shoulder.L", "bn_upperarm01.L"],  # LeftShoulder and LeftUpperArm
    13: ["bn_forearm01.L"],  # LeftLowerArm
    15: ["bn_hand.L"],  # LeftHand
    12: ["bn_shoulder.R", "bn_upperarm01.R"],  # RightShoulder and RightUpperArm
    14: ["bn_forearm01.R"],  # RightLowerArm
    16: ["bn_hand.R"],  # RightHand
    25: ["bn_shin01.L"],  # LeftLowerLeg
    27: ["bn_foot.L"],  # LeftFoot
    31: ["bn_toe.L"],  # LeftToes
    26: ["bn_shin01.R"],  # RightLowerLeg
    28: ["bn_foot.R"],  # RightFoot
    32: ["bn_toe.R"],  # RightToes
}

def draw_keypoint_label(frame, x, y, label, confidence):
    """Helper function to draw keypoint label with background"""
    # Font settings
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    font_thickness = 1
    
    # Get text size
    (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, font_thickness)
    
    # Calculate background rectangle position
    padding = 2
    rect_x = x + 5
    rect_y = y - text_height - padding
    
    # Draw background rectangle
    cv2.rectangle(frame, 
                 (rect_x, rect_y), 
                 (rect_x + text_width + 2*padding, rect_y + text_height + 2*padding), 
                 (0, 0, 0), 
                 -1)
    
    # Draw text
    cv2.putText(frame, 
                label, 
                (rect_x + padding, rect_y + text_height + padding), 
                font, 
                font_scale, 
                (255, 255, 255), 
                font_thickness)

def create_skeleton_data(keypoints):
    """Convert keypoints to Unity skeleton format"""
    skeleton_data = {
        "timestamp": time.time(),
        "bones": []
    }
    
    # First convert YOLO indices to MediaPipe indices
    mediapipe_keypoints = {}
    for yolo_idx, mediapipe_idx in YOLO_TO_MEDIAPIPE.items():
        if yolo_idx < len(keypoints):
            mediapipe_keypoints[mediapipe_idx] = keypoints[yolo_idx]
    
    # Process each keypoint
    for mediapipe_idx, unity_bones in KEYPOINT_TO_UNITY_MAP.items():
        if mediapipe_idx in mediapipe_keypoints:
            kpt = mediapipe_keypoints[mediapipe_idx]
            x, y = float(kpt[0]), float(kpt[1])
            confidence = float(kpt[2]) if len(kpt) > 2 else 1.0
            
            # Only use points with confidence > 0.5
            if confidence > 0.5:
                # Convert to Unity coordinate system
                unity_x = x
                unity_y = -y  # Invert Y for Unity's coordinate system
                unity_z = 0  # Z coordinate would need depth information
                
                # Add entry for each Unity bone that maps to this keypoint
                for bone_name in unity_bones:
                    bone_data = {
                        "name": bone_name,
                        "position": {
                            "x": unity_x,
                            "y": unity_y,
                            "z": unity_z
                        },
                        "confidence": confidence
                    }
                    skeleton_data["bones"].append(bone_data)
    
    return skeleton_data

# Load a model
model = YOLO("yolo11l-pose.pt")  # load an official model

# Open the camera (ID: 1)
cap = cv2.VideoCapture(1)

# Check if camera opened successfully
if not cap.isOpened():
    print("Error: Could not open camera")
    exit()

# Initialize FPS calculation variables
prev_time = 0
curr_time = 0

try:
    while True:
        # Read a frame from camera
        ret, frame = cap.read()
        if not ret:
            print("Error: Can't receive frame")
            break

        # Calculate FPS
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time) if prev_time > 0 else 0
        prev_time = curr_time

        # Predict with the model
        results = model(frame)  # predict on the frame

        # Access the results and draw keypoints
        for result in results:
            # Get keypoints
            kpts = result.keypoints.data[0]  # Get keypoints for first person
            
            # Debug: Print raw keypoints
            print("\nRaw Keypoints:")
            for i, kpt in enumerate(kpts):
                print(f"{YOLO_KEYPOINT_NAMES.get(i, f'Point {i}')}: x={kpt[0]:.1f}, y={kpt[1]:.1f}, conf={kpt[2]:.2f}")
            
            # Create and output skeleton data
            skeleton_data = create_skeleton_data(kpts)
            print("\nSkeleton Data:")
            print(json.dumps(skeleton_data, indent=2))
            
            # Draw each keypoint (for visualization)
            for i, kpt in enumerate(kpts):
                x, y = int(kpt[0]), int(kpt[1])
                confidence = kpt[2] if len(kpt) > 2 else 1.0
                
                # Draw keypoint with different colors based on confidence
                color = (0, int(255 * confidence), int(255 * (1 - confidence)))
                cv2.circle(frame, (x, y), 5, color, -1)
                
                # Draw keypoint label
                label = YOLO_KEYPOINT_NAMES.get(i, f"Point {i}")
                draw_keypoint_label(frame, x, y, f"{label} ({confidence:.2f})", confidence)

        # Display FPS on frame
        cv2.putText(frame, f"FPS: {int(fps)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Display the frame
        cv2.imshow("Keypoints", frame)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Release resources
    cap.release()
    cv2.destroyAllWindows()