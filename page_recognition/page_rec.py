import PyPDF2
import cv2
import numpy as np
import pandas as pd
import pytesseract
import tensorflow as tf
from keras.models import load_model
from keras.preprocessing.image import img_to_array
import os

JB = 0
PATH_TO_OUTPUT = ''


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
    return (cnts, bounding_boxes)


def contour_first(img):
    """Detect digit contour."""
    thresh = \
        cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    x, y, w, h = [0] * 4
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
    return x, y, w, h


def contour_second(img):
    """Detect digit contour."""
    thresh = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY)[1]
    cnt = cv2.bitwise_not(thresh)
    x, y, w, h = cv2.boundingRect(cnt)
    return x, y, w, h


def contour_third(img):
    """Detect digit contour."""
    thresh = cv2.threshold(img, 64, 255, cv2.THRESH_BINARY)[1]
    cnt = cv2.bitwise_not(thresh)
    x, y, w, h = cv2.boundingRect(cnt)
    return x, y, w, h


def recognize_number(model, img):
    """Recognize blocks with handwritten digit."""
    global JB
    cv2.imwrite('tmp.jpg'.format(JB), img)
    img = cv2.imread('tmp.jpg'.format(JB))
    img = cv2.copyMakeBorder(img, 10, 10, 10, 10,
                             cv2.BORDER_CONSTANT,
                             value=(255, 255, 255))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    x, y, w, h = contour_first(img)
    if h < img.shape[0] / 15 or w < img.shape[1] / 15 or (
            h == img.shape[0]) or (w == img.shape[1]):
        x, y, w, h = contour_second(img)
    if h < img.shape[0] / 15 or w < img.shape[1] / 15 or \
            (h == img.shape[0]) or (w == img.shape[1]):
        x, y, w, h = contour_third(img)

    roi = img[y:y + h, x:x + w]
    delta = abs(h - w)
    if h > w:
        top, bottom = 0, 0
        right, left = delta // 2, (delta + 1) // 2
    else:
        top, bottom = delta // 2, (delta + 1) // 2
        right, left = 0, 0
    roi = cv2.copyMakeBorder(roi, top, bottom, left, right,
                             cv2.BORDER_CONSTANT,
                             value=(255, 255, 255))
    try:
        img = cv2.resize(roi, (20, 20), interpolation=cv2.INTER_AREA)
    except:
        img = cv2.resize(img, (20, 20), interpolation=cv2.INTER_AREA)
    img = cv2.copyMakeBorder(img, 4, 4, 4, 4,
                             cv2.BORDER_CONSTANT,
                             value=(255, 255, 255))
    img = 255 - img
    img = tf.keras.utils.normalize(img, axis=1)
    img = np.array(img).reshape(-1, 28, 28, 1)

    out = str(np.argmax(model.predict(img)))

    JB += 1
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


def box_preparation(img):
    """Prepare tabular structure."""
    thresh, img_bin = cv2.threshold(img, 128, 255,
                                    cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    img_bin = 255 - img_bin

    kernel_len = np.array(img).shape[1] // 100
    ver_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_len))
    hor_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))

    image_1 = cv2.erode(img_bin, ver_kernel, iterations=5)
    vertical_lines = cv2.dilate(image_1, ver_kernel, iterations=5)

    image_2 = cv2.erode(img_bin, hor_kernel, iterations=5)
    horizontal_lines = cv2.dilate(image_2, hor_kernel, iterations=5)

    img_vh = cv2.addWeighted(vertical_lines, 0.5, horizontal_lines, 0.5, 0.0)
    img_vh = cv2.erode(~img_vh, kernel, iterations=2)
    thresh, img_vh = cv2.threshold(img_vh, 128, 255,
                                   cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    bitxor = cv2.bitwise_xor(img, img_vh)
    bitnot = cv2.bitwise_not(bitxor)

    contours, hierarchy = cv2.findContours(img_vh, cv2.RETR_TREE,
                                           cv2.CHAIN_APPROX_SIMPLE)
    contours, boundingBoxes = sort_contours(contours, method='top-to-bottom')
    heights = [boundingBoxes[i][3] for i in range(len(boundingBoxes))]
    mean = np.mean(heights)

    box = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if (w < 1000 and h < 500):
            box.append([x, y, w, h])
    return box, mean, bitnot


def page_recognition(img):
    """Return dataframe of the main table and save it to csv."""
    box, mean, bitnot = box_preparation(img)

    row = []
    column = []
    j = 0
    for i in range(len(box)):
        if (i == 0):
            column.append(box[i])
            previous = box[i]
        else:
            if (box[i][1] <= previous[1] + mean / 2):
                column.append(box[i])
                previous = box[i]
                if (i == len(box) - 1):
                    row.append(column)
            else:
                row.append(column)
                column = []
                previous = box[i]
                column.append(box[i])
    print(column)
    print(row)

    countcol = 0
    for i in range(len(row)):
        countcol = len(row[i])
        if countcol > countcol:
            countcol = countcol

    center = [int(row[i][j][0] + row[i][j][2] / 2) for j in range(len(row[i]))
              if row[0]]
    center = np.array(center)
    center.sort()

    finalboxes = []
    for i in range(len(row)):
        lis = []
        for k in range(countcol):
            lis.append([])
        for j in range(len(row[i])):
            diff = abs(center - (row[i][j][0] + row[i][j][2] / 4))
            minimum = min(diff)
            indexing = list(diff).index(minimum)
            lis[indexing].append(row[i][j])
        finalboxes.append(lis)

    outer = []
    model = load_model('../page_recognition/digit_rec/final_model2.h5')
    for i in range(len(finalboxes)):
        for j in range(len(finalboxes[i])):
            inner = ''
            if len(finalboxes[i][j]) == 0:
                outer.append(' ')
            else:
                for k in range(len(finalboxes[i][j])):
                    y, x, w, h = finalboxes[i][j][k][0], finalboxes[i][j][k][1], \
                                 finalboxes[i][j][k][2], finalboxes[i][j][k][3]
                    finalimg = bitnot[x:x + h, y:y + w]
                    if i > 0 and j > 1 and j < len(finalboxes[i]) - 1:
                        out = recognize_number(model, finalimg)
                    else:
                        out = recognize_text(finalimg)
                    out = out.replace('\n', ' ')
                    out = out.replace('- ', '')
                    inner = inner + " " + out
                outer.append(inner)

    arr = np.array(outer)
    df = pd.DataFrame(arr.reshape(len(row), countcol))
    df = df.drop(df[df[1].map(len) < 3].index)
    global PATH_TO_OUTPUT
    df.to_csv(PATH_TO_OUTPUT)
    os.remove('tmp.jpg')
    return df

#page_recognition(cv2.imread(r'CH_list1-1.png', 0))
