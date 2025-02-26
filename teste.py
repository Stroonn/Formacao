import cv2
import pytesseract as pt
import numpy as np 

pt.pytesseract.tesseract_cmd =  "C:/Program Files/Tesseract-OCR/tesseract.exe"

img = cv2.imread(r'cropped_8.jpg')
imH, imW, _ = img.shape

_, thresh = cv2.threshold(img, 200, 255, cv2.THRESH_BINARY_INV)
dados = pt.pytesseract.image_to_data(thresh, lang='por')


for x, linha in enumerate(dados.splitlines()):
    if x != 0:
        linha = linha.split()
        if len(linha) == 12:
            x, y, w, h = int(linha[6]), int(linha[7]), int(linha[8]), int(linha[9])
            palavra = linha[11]
            cv2.rectangle(thresh, (x, y), (w+x, h+y), (0, 0, 255), 1)

print(dados)

cv2.imwrite('teste_thresh.jpg',thresh)