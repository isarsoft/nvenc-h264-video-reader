from GPUVideoReader import GPUVideoReader
import cv2

cv2.namedWindow('FRAME', cv2.WINDOW_NORMAL)

reader = GPUVideoReader("h264videofileorrtspstream")

ret = True
while ret:
    ret, frame = reader.read()
    if not ret:
        break
    print("frame read")
    cv2.imshow("FRAME", frame)
    cv2.waitKey(1)

cv2.destroyAllWindows()
