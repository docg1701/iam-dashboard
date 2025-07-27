# Guia Completo de Pillow para Pré-processamento de Imagens em Pipelines OCR

**Visão Geral**
Este guia apresenta técnicas avançadas de uso da biblioteca Pillow para preparar imagens destinadas extração de texto via OCR (OpenCV, PyMuPDF e Tesseract). São abordados todos os passos — desde operações básicas de conversão de formato até ajustes finos de qualidade — com código de fácil integração em pipelines automatizadas.

## 1. Instalação

```bash
pip install Pillow pytesseract
```

*Obs.:* certifique-se de que o executável Tesseract esteja no PATH do sistema ou configure

```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

conforme a sua instalação[^1].

## 2. Leitura e Salvamento de Imagens

```python
from PIL import Image

# Abrir imagem
img = Image.open('documento.jpg')

# Salvar em outro formato
img.save('documento.png', format='PNG')
```


## 3. Conversão para Escala de Cinza

Transformar em tons de cinza reduz complexidade e prepara para binarização:

```python
gray = img.convert('L')
```

*“L”* indica modo de 8 bits em cinza[^2].

## 4. Redimensionamento para Aumentar Legibilidade

Aumentar resolução melhora detecção de caracteres:

```python
scale = 2
width, height = gray.size
resized = gray.resize((width*scale, height*scale), Image.LANCZOS)
```

O filtro *LANCZOS* preserva nitidez em ampliações[^3].

## 5. Aplicação de Filtros de Ruído e Nitidez

### 5.1 Remoção de Ruído

Use filtro de média ou mediana para atenuar “sal e pimenta”:

```python
from PIL import ImageFilter

# Desfoque gaussiano
denoised = resized.filter(ImageFilter.GaussianBlur(radius=1))

# Ou filtro mediano
denoised = resized.filter(ImageFilter.MedianFilter(size=3))
```

*GaussianBlur* suaviza ruídos leves; *MedianFilter* preserva bordas[^2].

### 5.2 Realce de Detalhes

Para melhorar definição de contornos:

```python
from PIL import ImageEnhance

enhancer = ImageEnhance.Sharpness(denoised)
sharp = enhancer.enhance(2.0)  # 1.0 = original, >1 aumenta nitidez[^13]
```


## 6. Binarização (Thresholding)

Converter imagem em preto-e-branco puro destaca texto:

```python
# Threshold global (Otsu-like manual)
threshold = 128
binary = sharp.point(lambda p: 255 if p > threshold else 0, mode='1')
```

Para limiar adaptativo, divida em blocos e aplique limiares locais via `crop` e `point`[^4].

## 7. Operações Morfológicas Básicas

Combinando filtros do Pillow e OpenCV via array NumPy:

```python
import cv2
import numpy as np

# Converter Pillow→NumPy
arr = np.array(binary.convert('L'))

# Erosão e dilatação com kernel 3×3
kernel = np.ones((3,3), np.uint8)
morph = cv2.morphologyEx(arr, cv2.MORPH_OPEN, kernel)
morph = cv2.morphologyEx(morph, cv2.MORPH_CLOSE, kernel)

# Voltar para Pillow
processed = Image.fromarray(morph)
```


## 8. Detecção de Regiões de Interesse (ROI) e Recorte

Identificar caixas de texto e recortar para OCR segmentado:

```python
import numpy as np

# Encontrar contornos
contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
rois = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    if w*h > 1000:  # área mínima
        roi = processed.crop((x, y, x+w, y+h))
        rois.append(roi)
```

Isso isola blocos de texto de formulários e tabelas[^5].

## 9. Integração com Tesseract (pytesseract)

```python
import pytesseract

# OCR na imagem pré-processada
text = pytesseract.image_to_string(processed, lang='eng', config='--psm 6')
print(text)
```

Para tabelas e caixas, use:

```python
data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DATAFRAME)
```


## 10. Pipeline Completo de Exemplo

```python
from PIL import Image, ImageFilter, ImageEnhance
import pytesseract
import cv2, numpy as np

def preprocess_for_ocr(path):
    img = Image.open(path)
    # Cinza e resize
    gray = img.convert('L')
    w, h = gray.size
    gray = gray.resize((w*2, h*2), Image.LANCZOS)
    # Ruído e nitidez
    gray = gray.filter(ImageFilter.MedianFilter(3))
    gray = ImageEnhance.Sharpness(gray).enhance(2.0)
    # Binarização
    binary = gray.point(lambda p: 255 if p>128 else 0, '1')
    # Morfologia
    arr = np.array(binary.convert('L'))
    kernel = np.ones((3,3), np.uint8)
    arr = cv2.morphologyEx(arr, cv2.MORPH_OPEN, kernel)
    arr = cv2.morphologyEx(arr, cv2.MORPH_CLOSE, kernel)
    return Image.fromarray(arr)

# Uso
proc = preprocess_for_ocr('documento.jpg')
resultado = pytesseract.image_to_string(proc, lang='por+eng', config='--psm 6')
print(resultado)
```

**Conclusão**
A combinação de conversão de espaço de cor, redimensionamento, filtros de redução de ruído, realce de nitidez, binarização e operações morfológicas via Pillow (e ocasionalmente OpenCV) maximiza significativamente a **acurácia de OCR**[^2][^6][^4]. Este fluxo modular pode ser adaptado para documentos impressos ou manuscritos, suportando diversas condições de iluminação e qualidade de escaneamento.

<div style="text-align: center">⁂</div>

[^1]: https://pypi.org/project/pytesseract/

[^2]: https://www.dynamicguy.com/post/how-to-pre-process-your-image-for-better-ocr-results-using-python/

[^3]: https://www.nutrient.io/blog/how-to-use-tesseract-ocr-in-python/

[^4]: https://stackoverflow.com/questions/68957686/pillow-how-to-binarize-an-image-with-threshold

[^5]: https://stackoverflow.com/questions/66492341/how-to-crop-images-using-pillow-and-pytesseract

[^6]: https://www.pythonforall.com/modules/pillow/pwfilter

[^7]: https://wseas.com/journals/isa/2023/a465109-013(2023).pdf

[^8]: https://ijsrem.com/download/optimizing-ocr-performance-an-investigation-into-image-preprocessing-techniques/

[^9]: https://arxiv.org/abs/2410.13622

[^10]: https://ieeexplore.ieee.org/document/10763065/

[^11]: https://ieeexplore.ieee.org/document/10908135/

[^12]: https://www.mdpi.com/2079-9292/12/11/2449

[^13]: https://www.ijraset.com/best-journal/preprocessing-low-quality-handwritten-documents-for-ocr-model

[^14]: https://aclanthology.org/2023.emnlp-industry.44

[^15]: https://ieeexplore.ieee.org/document/9791698/

[^16]: https://pubs.aip.org/aip/acp/article-lookup/doi/10.1063/5.0247289

[^17]: https://www.iri.com/blog/data-protection/preprocessing-images-for-ocr-darkshield/

[^18]: https://www.educative.io/answers/how-to-enhance-image-in-python-pillow

[^19]: https://nextgeninvent.com/blogs/7-steps-of-image-pre-processing-to-improve-ocr-using-python-2/

[^20]: https://www.youtube.com/watch?v=HNCypVfeTdw

[^21]: https://www.tutorialspoint.com/python_pillow/python_pillow_enhancing_contrast.htm

[^22]: https://github.com/ocrmypdf/OCRmyPDF/issues/1374

[^23]: https://ieeexplore.ieee.org/document/8770662/

[^24]: https://link.springer.com/10.1007/s42979-025-03816-6

[^25]: https://ieeexplore.ieee.org/document/9617487/

[^26]: https://www.ssrn.com/abstract=4135966

[^27]: https://ejournal.ids.ac.id/index.php/sentinel/article/view/23

[^28]: https://www.semanticscholar.org/paper/f438804419e9de585544745765e979acd31872fa

[^29]: https://jurnal.ardenjaya.com/index.php/ajst/article/view/671

[^30]: https://indjst.org/articles/advancements-in-segmentation-of-unconstrained-malayalam-handwritten-documents-f-or-enhanced-ocr

[^31]: https://arxiv.org/pdf/2111.14075.pdf

[^32]: https://www.mdpi.com/1424-8220/23/6/3361/pdf?version=1679551865

[^33]: https://stackoverflow.com/questions/50951955/pytesseract-tesseractnotfound-error-tesseract-is-not-installed-or-its-not-i

[^34]: https://github.com/madmaze/pytesseract

[^35]: https://pyimagesearch.com/2017/07/10/using-tesseract-ocr-python/

[^36]: https://nanonets.com/blog/ocr-with-tesseract/

[^37]: https://www.youtube.com/watch?v=UxYJxcdLrs0

[^38]: https://www.nutrient.io/blog/tesseract-python-guide/

[^39]: https://cloudinary.com/guides/web-performance/extract-text-from-images-in-python-with-pillow-and-pytesseract

[^40]: https://trenton3983.github.io/posts/ocr-image-processing-pytesseract-cv2/

[^41]: https://arxiv.org/pdf/2105.07983.pdf

[^42]: https://arxiv.org/pdf/2206.00311.pdf

[^43]: https://arxiv.org/pdf/2109.03144.pdf

[^44]: http://arxiv.org/pdf/2109.10282v3.pdf

[^45]: https://www.mdpi.com/2224-2708/11/4/63/pdf?version=1664777460

[^46]: http://arxiv.org/pdf/2311.09612.pdf

[^47]: https://arxiv.org/pdf/2212.09297.pdf

[^48]: http://arxiv.org/pdf/2409.01704v1.pdf

[^49]: http://arxiv.org/pdf/2209.05534v1.pdf

[^50]: https://arxiv.org/pdf/2204.00052.pdf

[^51]: https://www.pythoncentral.io/create-ocr-with-pytesseract/

[^52]: https://stackoverflow.com/questions/4142687/using-pythons-pil-how-do-i-enhance-the-contrast-saturation-of-an-image

[^53]: https://www.youtube.com/watch?v=ADV-AjAXHdc

[^54]: https://realpython.com/image-processing-with-the-python-pillow-library/

[^55]: https://pillow.readthedocs.io/en/stable/reference/ImageEnhance.html

[^56]: https://pyimagesearch.com/2021/08/16/installing-tesseract-pytesseract-and-python-ocr-packages-on-your-system/

[^57]: https://onlinelibrary.wiley.com/doi/pdfdirect/10.1111/jmi.12474

[^58]: https://thescipub.com/pdf/jcssp.2020.784.801.pdf

[^59]: http://arxiv.org/pdf/2409.04117.pdf

[^60]: https://arxiv.org/pdf/2110.01661.pdf

[^61]: https://pmc.ncbi.nlm.nih.gov/articles/PMC9398848/

[^62]: https://www.mdpi.com/2571-5577/6/5/87/pdf?version=1695978531

