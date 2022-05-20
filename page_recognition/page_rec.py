import math
import os

import cv2
import fitz
import numpy as np
import pandas as pd
import pytesseract
from keras.models import load_model
from scipy.ndimage.measurements import center_of_mass

from borderFunc import extract_table

PATH_TO_OUTPUT = ''
PATH_TO_TMP = 'tmp'
PATH_TO_IMG = PATH_TO_TMP + '/images/'

SECTIONS = {
    'CH': 'химия',
    'MA': 'математика',
    'PH': 'физика',
    'T': 'техника',
    'RB': 'робототехника',
    'B': 'биология',
    'CS': 'системное',
    'ME': 'физиология',
    'EC': 'экология',
    'GE': 'науки',
}
JURY = {
    'научного': [11] * 5,
    'учительского': [11] * 2,
    'молодежного': [13] * 3}
COLUMNS = (
    'Тип жюри',
    'Номер проекта',
    'Выберите группу, к которой можно отнести проект / Группа проекта',
    'Оценивание проекта / Соответствие целей проекта или исследования полученным результатам',
    'Оценивание проекта / Новизна и оригинальность',
    'Оценивание проекта / Актуальность, востребованность',
    'Оценивание проекта / Сложность',
    'Оценивание проекта / Методологичность (качество инструментов, технологий, методов)',
    'Оценивание проекта / Трудоемкость (вложенные интеллектуальные, временные и иные ресурсы)',
    'Оценивание проекта / Законченность',
    'Оценивание проекта / Грамотность, системность, коммуникативная культура',
    'Критерии молодёжного жюри / Доступность для неспециалиста',
    'Критерии молодёжного жюри / Нестандартный подход к работе',
    'Критерии учительского жюри / Свободное владение материалом',
    'Критерии учительского жюри / Влияние на личность участника, уровень работы относительно опыта',
    'Критерии учительского жюри / Видение перспективы работы',
    'Комментарий'
)


def get_path_to_output(out: str):
    global PATH_TO_OUTPUT
    PATH_TO_OUTPUT = out


def sort_contours(cnts, method="left-to-right"):
    """Get a sequence of contours and sort them."""
    reverse = False
    i = 0
    if method == "right-to-left" or method == "bottom-to-top":
        reverse = True

    if method == "top-to-bottom" or method == "bottom-to-top":
        i = 1
    bounding_boxes = [cv2.boundingRect(c) for c in cnts]
    (cnts, bounding_boxes) = zip(*sorted(zip(cnts, bounding_boxes),
                                         key=lambda b: b[1][i],
                                         reverse=reverse))
    return cnts, bounding_boxes


def best_shift(img):
    """Calculate center of mass and shift direction."""
    cy, cx = center_of_mass(img)

    rows, cols = img.shape
    shiftx = np.round(cols / 2.0 - cx).astype(int)
    shifty = np.round(rows / 2.0 - cy).astype(int)

    return shiftx, shifty


def shift(img, sx, sy):
    """Shift the image."""
    rows, cols = img.shape
    M = np.float32([[1, 0, sx], [0, 1, sy]])
    shifted = cv2.warpAffine(img, M, (cols, rows))
    return shifted


def recognize_number(model, img):
    """Recognize blocks with handwritten digit."""
    cv2.imwrite('tmp.jpg', img)
    img = cv2.imread('tmp.jpg', cv2.IMREAD_GRAYSCALE)
    img = 255 - img
    (thresh, gray) = cv2.threshold(img, 128, 255,
                                   cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    try:
        while np.sum(gray[0]) == 0:
            gray = gray[1:]

        while np.sum(gray[:, 0]) == 0:
            gray = np.delete(gray, 0, 1)

        while np.sum(gray[-1]) == 0:
            gray = gray[:-1]

        while np.sum(gray[:, -1]) == 0:
            gray = np.delete(gray, -1, 1)
    except IndexError:
        return ''

    rows, cols = gray.shape

    if rows > cols:
        factor = 20.0 / rows
        rows = 20
        cols = int(round(cols * factor))
        if cols == 0:
            return ''
        gray = cv2.resize(gray, (cols, rows))
    else:
        factor = 20.0 / cols
        cols = 20
        rows = int(round(rows * factor))
        if rows == 0:
            return ''
        gray = cv2.resize(gray, (cols, rows))
    colsPadding = (
        int(math.ceil((28 - cols) / 2.0)), int(math.floor((28 - cols) / 2.0)))
    rowsPadding = (
        int(math.ceil((28 - rows) / 2.0)), int(math.floor((28 - rows) / 2.0)))
    gray = np.lib.pad(gray, (rowsPadding, colsPadding), 'constant')
    shiftx, shifty = best_shift(gray)
    shifted = shift(gray, shiftx, shifty)
    img = shifted
    img = img / 255.0
    img = np.array(img).reshape(-1, 28, 28, 1)

    out = str(np.argmax(model.predict(img)))

    return out


def recognize_text(img):
    """Recognize blocks with sample text."""
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 1))
    border = cv2.copyMakeBorder(
        img, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value=[255, 255],
    )
    resizing = cv2.resize(
        border, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC,
    )
    dilation = cv2.dilate(resizing, kernel, iterations=1)
    erosion = cv2.erode(dilation, kernel, iterations=1)
    out = pytesseract.image_to_string(erosion, lang='rus')
    if len(out) == 0:
        out = pytesseract.image_to_string(erosion, config='--psm 3', lang='rus')
    return out


def page_recognition(img, model):
    """Return dataframe of the main table and save it to csv."""
    box, rows, cols = extract_table(img, 1, lines=None)
    print('Table rows-cols: {}-{}'.format(rows, cols))
    if len(box) == 0 or rows == 1 or cols == 0:
        return None
    outer = []
    for i in range(rows):
        for j in range(cols):
            k = box[i + j * rows]
            crop = img[k[1] + 2:k[7] - 2, k[0] + 2:k[6] - 2]
            if i == 0 or 0 <= j <= 1:
                out = recognize_text(crop)
            else:
                out = recognize_number(model, crop)
            outer.append(out)
    arr = np.array(outer)
    df = pd.DataFrame(arr.reshape(rows, cols))

    df.drop(df[df[1].map(len) < 3].index, inplace=True)
    if not df.empty:
        df.drop([0, 1], axis=1, inplace=True)
        df.drop([0], axis=0, inplace=True)
    # print(df)
    df.to_csv('GOVNO.csv')
    if df.empty:
        df = None
    # global PATH_TO_OUTPUT

    try:
        os.remove('tmp.jpg')
    except:
        pass
    return df


def pdf_processing(src):
    sec_dataframes = {
        'CH': None,
        'MA': None,
        'PH': None,
        'T': None,
        'RB': None,
        'B': None,
        'CS': None,
        'ME': None,
        'EC': None,
        'GE': None,
    }
    cur_section = None
    cur_jury = None

    doc = fitz.open(src)
    global PATH_TO_IMG
    for page in doc:
        # Save pages as images in the pdf
        pix = page.get_pixmap()
        pix.save(PATH_TO_IMG + 'img' + str(page.number) + '.png')
    images = os.listdir(PATH_TO_IMG)

    model = load_model('page_recognition/final_model.h5')
    project_num = 1
    for num in range(len(images)):
        print('PROCESSING {} page'.format(num))
        image = cv2.imread(
            os.path.abspath(PATH_TO_IMG + 'img{}.png'.format(num)))
        df = page_recognition(image, model)

        text = pytesseract.image_to_string(image, lang='rus').lower().split()
        for key, val in SECTIONS.items():
            if len(text[6]) > len(val) and text[6][1:len(val) + 1] == val:
                cur_section = key

        for name in JURY.keys():
            if name in text:
                cur_jury = name

        if 'подпись' in text or 'расшифровкой' in text:
            project_num = 1

        if df is not None:
            if sec_dataframes[cur_section] is None:
                sec_dataframes[cur_section] = pd.DataFrame(columns=COLUMNS)
            project_nums = [project_num + i for i in range(df.shape[0])]
            df.insert(0, COLUMNS[1], project_nums)
            project_num += df.shape[0]
            df.insert(0, COLUMNS[0], cur_jury)
            for i, col_index in enumerate(JURY[cur_jury]):
                df.insert(col_index, str(col_index) + str(i), '', True)
            new_columns = dict(zip(df.columns, COLUMNS))
            df.rename(columns=new_columns, inplace=True)
            sec_dataframes[cur_section] = sec_dataframes[cur_section].append(df,
                                                                             ignore_index=True)

        for key, df in sec_dataframes.items():
            if df is not None:
                df.to_csv('{}.csv'.format(key))
        os.remove(os.path.abspath(PATH_TO_IMG + 'img{}.png'.format(num)))
    return sec_dataframes
