import cv2
import cv2.aruco as aruco

# Open the video stream
def detect_markers(stream_url,on_marker_detected,status_holder=None):
    cap = cv2.VideoCapture(stream_url)

    # ArUco setup
    aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
    parameters = aruco.DetectorParameters()
    detector = aruco.ArucoDetector(aruco_dict, parameters)

    marker_log=[]

    window_name = "ArUco Detection from Phosphobot"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)

    ret,frame=cap.read()
    if ret:
        cv2.imshow(window_name,frame)
        cv2.waitKey(1)

    print("Press 'q' to quit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame from stream.")
            break

        # Detect markers
        corners, ids, _ = detector.detectMarkers(frame)
        if ids is not None:
            for marker in ids:
                marker_id=int(marker[0])
                if marker_id not in marker_log:
                    aruco.drawDetectedMarkers(frame, corners, ids)
                    print(f"Detected marker ID: {marker_id}")
                    on_marker_detected(marker_id)
                    marker_log.append(marker_id)

        if status_holder is not None:
            cv2.putText(frame,f"Status: {status_holder['status']}",(10,30),
                    cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,255,0),2)

        cv2.imshow(window_name, frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()