# Guia Avançado de Pré-processamento de Documentos Escaneados com OpenCV para OCR

**Principais recomendações:**
Para maximizar a acurácia de OCR em documentosaneados (impressos ou manuscritos), aplique uma sequência de operações de pré-processamento com OpenCV:

1. **Normalização e remoção de ruido**
2. **Deskew (correção de inclinação)**
3. **Binzarização adaptativa e global**
4. **Operações morfológicas** (dilatação, erosão)
5. **Detecção e recorte de ROI**

---

## 1. Normalização e Remoção de Ruído

Converta para escala de cinza e suavize para reduzir artefatos:

```python
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
gray = cv2.GaussianBlur(gray, (5,5), 0)
```

- *GaussianBlur* atenua ruído sal e pimenta[^1].
- Em cenários com muito grão, use `cv2.fastNlMeansDenoising()` para preservação de bordas[^2].

---

## 2. Deskew (Correção de Inclinação)

Corrige rotações resultantes de digitalizações tortas:

```python
# Binariza invertido para destacar texto
thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV|cv2.THRESH_OTSU)[^1]
coords = np.column_stack(np.where(thresh>0))
angle = cv2.minAreaRect(coords)[-1]
if angle < -45: angle = -(90+angle)
else: angle = -angle
(h, w) = gray.shape
M = cv2.getRotationMatrix2D((w//2,h//2), angle, 1.0)
rotated = cv2.warpAffine(img, M, (w,h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
```

- *minAreaRect* sobre pixels de texto estima ângulo de skew[^3].
- `BORDER_REPLICATE` evita bordas pretas após a rotação[^3].

---

## 3. Binarização

### 3.1 Global (Otsu)

```python
_, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
```

- Método rápido, mas sensível a iluminação não uniforme[^4].


### 3.2 Adaptativa

```python
binary = cv2.adaptiveThreshold(
    gray, 255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY,
    blockSize=35,
    C=5
)
```

- Calcula limiar local por vizinhança, ideal para variações de luz[^5].
- Tente tanto `MEAN_C` quanto `GAUSSIAN_C` e ajuste `blockSize` e `C`[^6].

---

## 4. Operações Morfológicas

Refina a binarização removendo buracos e conectando caracteres:

```python
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
clean = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)   # remove ruído
clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, kernel) # fecha fissuras
```

- **Abertura** (open) elimina pequenos pontos isolados[^7].
- **Fechamento** (close) une lacunas em traços de texto[^7].

---

## 5. Detecção e Recorte de ROI (Regiões de Interesse)

Para documentos com múltiplos blocos (tabelas, formulários), segmente contornos:

```python
contours, _ = cv2.findContours(clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
for cnt in contours:
    x,y,w,h = cv2.boundingRect(cnt)
    if w*h > min_area:
        roi = img[y:y+h, x:x+w]
        # aplicar OCR em cada ROI
```

- Filtre por área mínima (`min_area`) para descartar ruído[^8].
- Opcionalmente, use `dilate` com kernel alongado para combinar caracteres em linhas antes de detectar contornos[^9].


## 6. Fluxo Completo de Pré-processamento

```python
import cv2, numpy as np

def preprocess_for_ocr(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5,5), 0)
    # Deskew
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV|cv2.THRESH_OTSU)[^1]
    coords = np.column_stack(np.where(thresh>0))
    angle = cv2.minAreaRect(coords)[-1]
    angle = -(90+angle) if angle < -45 else -angle
    (h, w) = img.shape[:2]
    M = cv2.getRotationMatrix2D((w//2,h//2), angle, 1.0)
    img = cv2.warpAffine(img, M, (w,h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    # Binarização adaptativa
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY,35,5)
    # Morfologia
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(2,2))
    clean = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, kernel)
    return clean
```

Aplicando essa pipeline em cada página ou ROI, o Tesseract (ou outro motor OCR) alcançará resultados substancialmente melhores em termos de precisão de reconhecimento de texto e detecção de dados estruturados.

<div style="text-align: center">⁂</div>

[^1]: https://www.dynamsoft.com/codepool/deskew-scanned-document.html

[^2]: https://gist.github.com/russss/922be97d2a65eb534744c5a4054ff88d

[^3]: https://stackoverflow.com/questions/78337034/deskew-image-using-opencv-in-python

[^4]: https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html

[^5]: https://www.geeksforgeeks.org/python/python-thresholding-techniques-using-opencv-set-2-adaptive-thresholding/

[^6]: https://www.youtube.com/watch?v=nps3zzo7CCY

[^7]: https://stackoverflow.com/questions/28935983/preprocessing-image-for-tesseract-ocr-with-opencv

[^8]: https://isjem.com/download/text-detection-and-extraction-using-opencv-and-ocr/

[^9]: http://services.igi-global.com/resolvedoi/resolve.aspx?doi=10.4018/IJAMC.2017010104

[^10]: https://arxiv.org/abs/2410.13622

[^11]: https://humgenomics.biomedcentral.com/articles/10.1186/s40246-024-00684-8

[^12]: https://www.spwla.org/SPWLA/Publications/Publication_Detail.aspx?iProductCode=PJV65N5-2024a8

[^13]: https://ijsrem.com/download/character-recognition-and-extraction-using-opencv-and-pytesseract/

[^14]: https://www.ijitee.org/portfolio-item/G5745059720/

[^15]: https://www.spwla.org/SPWLA/Publications/Publication_Detail.aspx?iProductCode=SPWLA-2023-0084

[^16]: https://ieeexplore.ieee.org/document/10269964/

[^17]: http://biorxiv.org/lookup/doi/10.1101/240044

[^18]: https://pyimagesearch.com/2021/11/22/improving-ocr-results-with-basic-image-processing/

[^19]: https://www.geeksforgeeks.org/python/text-detection-and-extraction-using-opencv-and-ocr/

[^20]: https://www.youtube.com/watch?v=ADV-AjAXHdc

[^21]: https://arxiv.org/pdf/1509.03456.pdf

[^22]: https://arxiv.org/html/2404.05669v1

[^23]: https://arxiv.org/pdf/2105.07983.pdf

[^24]: https://arxiv.org/pdf/1412.4183.pdf

[^25]: http://arxiv.org/pdf/2109.10282v3.pdf

[^26]: https://arxiv.org/pdf/2204.00052.pdf

[^27]: https://arxiv.org/pdf/2410.13622.pdf

[^28]: https://arxiv.org/pdf/2109.03144.pdf

[^29]: http://arxiv.org/pdf/2409.01704v1.pdf

[^30]: https://arxiv.org/pdf/2212.09297.pdf

[^31]: https://becominghuman.ai/how-to-automatically-deskew-straighten-a-text-image-using-opencv-a0c30aed83df

[^32]: https://studyopedia.com/opencv/image-thresholding-opencv/

[^33]: https://nextgeninvent.com/blogs/7-steps-of-image-pre-processing-to-improve-ocr-using-python-2/

[^34]: https://github.com/sbrunner/deskew

[^35]: https://stackoverflow.com/questions/22122309/opencv-adaptive-threshold-ocr

[^36]: https://forum.opencv.org/t/opencv-python-preprocessing-strategies-for-ocr-pytesseract-character-recognition/19674

[^37]: https://pyimagesearch.com/2017/02/20/text-skew-correction-opencv-python/

[^38]: https://pyimagesearch.com/2021/05/12/adaptive-thresholding-with-opencv-cv2-adaptivethreshold/

[^39]: https://opencv.org/blog/text-detection-and-removal-using-opencv/

[^40]: https://answers.opencv.org/question/231234/deskewingaligning-content-of-paper/

