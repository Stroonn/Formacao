import cv2
import numpy as np

def process_image(image_bytesio):
    
    image_bytes = image_bytesio.getvalue()

    # Converte para um array NumPy
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)

    img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    image = cv2.GaussianBlur(img, (3, 3), -1, -1)
    cv2.imwrite('modelo\\gaussian.jpg', image)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cv2.imwrite('modelo\\gray.jpg', gray)

    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
    cv2.imwrite('modelo\\thresh.jpg', thresh)

    rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilation = cv2.dilate(thresh, rect_kernel, iterations=3)
    cv2.imwrite('modelo\\dilation_image.jpg', dilation)

    contours, _ = cv2.findContours(dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    i = 0
    for cnt in contours:
        i += 1
        x, y, w, h = cv2.boundingRect(cnt)
        rect = cv2.rectangle(gray, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.imwrite('modelo\\rectanglebox.jpg', rect)

        cropped = gray[y:y + h, x:x + w]
        cv2.imwrite(f'modelo\\cropped_{i}.jpg', cropped)

    cv2.imwrite('resultado.jpg', rect)
    caminho = 'resultado.jpg'
    cv2.waitKey(0)
    return caminho