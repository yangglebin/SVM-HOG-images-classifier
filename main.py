# -*- coding: utf-8 -*-
# @Author  : Huangcc

import os
import numpy as np
from skimage import feature as skif
from skimage import io, transform
import random
from sklearn.multiclass import OneVsRestClassifier
from sklearn.svm import SVR

# 全局变量
IMAGES_DIR = os.path.join(os.path.dirname(__file__), 'images')  # images的绝对路径
POS_IMAGE_DIR = os.path.join(IMAGES_DIR, 'positive')
NEG_IMAGE_DIR = os.path.join(IMAGES_DIR, 'negative')
RESIZE_POS_IMAGE_DIR = os.path.join(IMAGES_DIR, 'resize_positive')
RESIZE_NEG_IMAGE_DIR = os.path.join(IMAGES_DIR, 'resize_negative')
IMG_TYPE = 'png'  # 图片类型
IMG_WIDTH = 256
IMG_HEIGHT = 256


def resize_image(file_in, file_out, width, height):
    img = io.imread(file_in)
    out = transform.resize(img, (width, height),
                           mode='reflect')  # mode {'constant', 'edge', 'symmetric', 'reflect', 'wrap'}
    io.imsave(file_out, out)


def load_images(images_list, width, height):
    data = np.zeros((len(images_list), width, height))  # 创建多维数组存放图片
    for index, image in enumerate(images_list):
        image_data = io.imread(image, as_grey=True)
        data[index, :, :] = image_data  # 读取图片存进numpy数组
    return data


def split_data(file_path_list, lables_list, rate=0.5):
    if rate == 1.0:
        return file_path_list, lables_list, file_path_list, lables_list
    list_size = len(file_path_list)
    train_list_size = int(list_size * rate)
    selected_indexes = random.sample(range(list_size), train_list_size)
    train_file_list = []
    train_label_list = []
    test_file_list = []
    test_label_list = []
    for i in range(list_size):
        if i in selected_indexes:
            train_file_list.append(file_path_list[i])
            train_label_list.append(lables_list[i])
        else:
            test_file_list.append(file_path_list[i])
            test_label_list.append(lables_list[i])
    return train_file_list, train_label_list, test_file_list, test_label_list


def get_hog_data(images_data, hist_size=256, pixels_per_cell=(8, 8), cells_per_block=(3, 3)):
    n_images = images_data.shape[0]
    hist = np.zeros((n_images, hist_size))
    for i in np.arange(n_images):
        # 使用HOG方法提取图像的纹理特征.
        hog = skif.hog(images_data[i], pixels_per_cell=pixels_per_cell, cells_per_block=cells_per_block)
        # 统计图像的直方图
        # max_bins = int(hog.max() + 1)
        # hist size:256
        # hist[i], _ = np.histogram(hog, normed=True, bins=max_bins, range=(0, max_bins))
        hist[i] = hog

    return hist


def main():
    # 检测resize文件夹是否存在，不存在则创建
    if not os.path.exists(RESIZE_POS_IMAGE_DIR):
        os.makedirs(RESIZE_POS_IMAGE_DIR)
    if not os.path.exists(RESIZE_NEG_IMAGE_DIR):
        os.makedirs(RESIZE_NEG_IMAGE_DIR)
    # 获取图片列表
    pos_file_path_list = map(lambda x: os.path.join(POS_IMAGE_DIR, x), os.listdir(POS_IMAGE_DIR))
    neg_file_path_list = map(lambda x: os.path.join(NEG_IMAGE_DIR, x), os.listdir(NEG_IMAGE_DIR))
    # 调整图片大小
    for index, pic in enumerate(pos_file_path_list):
        f_out = os.path.join(RESIZE_POS_IMAGE_DIR, '{}.{}'.format(index, IMG_TYPE))
        resize_image(pic, f_out, IMG_WIDTH, IMG_HEIGHT)
    for index, pic in enumerate(neg_file_path_list):
        f_out = os.path.join(RESIZE_NEG_IMAGE_DIR, '{}.{}'.format(index, IMG_TYPE))
        resize_image(pic, f_out, IMG_WIDTH, IMG_HEIGHT)
    # 调整后的图片列表
    pos_file_path_list = map(lambda x: os.path.join(RESIZE_POS_IMAGE_DIR, x), os.listdir(RESIZE_POS_IMAGE_DIR))
    neg_file_path_list = map(lambda x: os.path.join(RESIZE_NEG_IMAGE_DIR, x), os.listdir(RESIZE_NEG_IMAGE_DIR))
    # 切分数据集
    train_file_list0, train_label_list0, test_file_list0, test_label_list0 = split_data(pos_file_path_list,
                                                                                        [1] * len(pos_file_path_list),
                                                                                        rate=0.5)
    train_file_list1, train_label_list1, test_file_list1, test_label_list1 = split_data(neg_file_path_list,
                                                                                        [-1] * len(neg_file_path_list),
                                                                                        rate=0.5)
    # 合并数据集
    train_file_list = train_file_list0 + train_file_list1
    train_label_list = train_label_list0 + train_label_list1
    test_file_list = test_file_list0 + test_file_list1
    test_label_list = test_label_list0 + test_label_list1
    # 载入图片
    train_image_array = load_images(train_file_list, width=IMG_WIDTH, height=IMG_HEIGHT)
    train_label_array = np.array(train_label_list)
    test_image_array = load_images(test_file_list, width=IMG_WIDTH, height=IMG_HEIGHT)
    test_label_array = np.array(test_label_list)
    # 获取HOG特征
    # train_hist_array = get_hog_data(train_image_array, hist_size=256, pixels_per_cell=(8, 8), cells_per_block=(3, 3))
    # test_hist_array = get_hog_data(test_image_array, hist_size=256, pixels_per_cell=(8, 8), cells_per_block=(3, 3))
    train_hist_array = get_hog_data(train_image_array, hist_size=72900, pixels_per_cell=(8, 8), cells_per_block=(3, 3))
    test_hist_array = get_hog_data(test_image_array, hist_size=72900, pixels_per_cell=(8, 8), cells_per_block=(3, 3))
    # 选取svm里面的SVR作为训练模型
    svr_rbf = SVR(kernel='rbf', C=1e3, gamma=0.1)  # SVC, NuSVC, SVR, NuSVR, OneClassSVM, LinearSVC, LinearSVR
    # 训练和测试
    score = OneVsRestClassifier(svr_rbf, n_jobs=-1).fit(train_hist_array, train_label_array).score(test_hist_array,
                                                                                                   test_label_array)  # n_jobs是cpu数量, -1代表所有
    print score
    return score


if __name__ == '__main__':
    n = 10
    scores = []
    for i in range(n):
        s = main()
        scores.append(s)
    max_s = max(scores)
    min_s = min(scores)
    avg_s = sum(scores) / float(n)
    print '==========\nmax: %s\nmin: %s\navg: %s' % (max_s, min_s, avg_s)
