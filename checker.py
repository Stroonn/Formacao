import cv2
import pytesseract as pt
import numpy as np

'''
for x, linha in enumerate(dados.splitlines()):
    if x != 0:
        linha = linha.split()
        if len(linha) == 12:
            x, y, w, h = int(linha[6]), int(linha[7]), int(linha[8]), int(linha[9])
            palavra = linha[11]
            cv2.rectangle(img, (x, y), (w+x, h+y), (0, 0, 255), 1)

print(dados)

print(pt.pytesseract.image_to_string(img, lang='por'))
'''

def process_image(image_path):
    pt.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"
    
    img = cv2.imread(image_path)
    imH, imW, _ = img.shape

    dados = pt.pytesseract.image_to_data(img, lang='por')

    image = cv2.GaussianBlur(img, (3, 3), -1, -1)
    cv2.imwrite('gaussian.jpg', image)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cv2.imwrite('gray.jpg', gray)

    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
    cv2.imwrite('thresh.jpg', thresh)

    rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilation = cv2.dilate(thresh, rect_kernel, iterations=3)
    cv2.imwrite('dilation_image.jpg', dilation)

    contours, _ = cv2.findContours(dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    im2 = thresh
    i = 0
    for cnt in contours:
        i += 1

        x, y, w, h = cv2.boundingRect(cnt)

        # Draw the bounding box on the text area
        rect = cv2.rectangle(gray, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.imwrite('rectanglebox.jpg', rect)

        # Crop the bounding box area
        cropped = gray[y:y + h, x:x + w]

        cv2.imwrite(f'cropped_{i}.jpg', cropped)

        # open the text file
        file = open("text_output2.txt", "a", encoding="utf-8")

        # Using tesseract on the cropped image area to get text
        text = pt.pytesseract.image_to_string(cropped, lang='por')

        # Adding the text to the file
        file.write(text)
        file.write("\n")

        # Closing the file
        file.close()

    cv2.imwrite('resultado.jpg', rect)
    caminho = 'resultado.jpg'
    cv2.waitKey(0)
    return caminho

# Example usage:
result_image = process_image(r'imagem_t1.jpg')