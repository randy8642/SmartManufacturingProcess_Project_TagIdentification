from cam_jpg import Camera
import cv2

def main():
    cap = Camera()

    cap.start()
    out = cv2.VideoWriter('output.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 24, (2560, 480))
    while True:
        ret, frame = cap.read()

        if not ret:
            continue
        
        # 輸出
        out.write(frame)
        frame = cv2.resize(frame, (1500, 400), interpolation=cv2.INTER_AREA)
        cv2.imshow('', frame)

        k = cv2.waitKey(10) & 0xFF
        if (k == 113):  # q is pressed
            cap.close()
            break
    out.release()

if __name__ == '__main__':
    main()
