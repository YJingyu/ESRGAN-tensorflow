import os
import glob

import cv2
import numpy as np


def create_dirs(target_dirs):
    """create necessary directories to save output files"""
    for dir_path in target_dirs:
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)


def normalize_images(*arrays):
    """normalize input image arrays by divining 255"""
    return [arr / 255 for arr in arrays]


def de_normalize_image(image):
    """de-normalize input image array by multiplying 255"""
    return image * 255


def save_image(FLAGS, images, phase, global_iter, save_max_num=5):
    """save images in specified directory"""
    if phase == 'train' or phase == 'pre-train':
        save_dir = FLAGS.train_result_dir
    elif phase == 'inference':
        save_dir = FLAGS.inference_result_dir
        save_max_num = len(images)
    else:
        print('specified phase is invalid')

    for i, img in enumerate(images):
        if i >= save_max_num:
            break

        cv2.imwrite(save_dir + '/{0}_HR_{1}_{2}.jpg'.format(phase, global_iter, i), de_normalize_image(img))


def crop(img, FLAGS):
    """crop patch from an image with specified size"""
    img_h, img_w, _ = img.shape

    rand_h = np.random.randint(img_h - FLAGS.crop_size)
    rand_w = np.random.randint(img_w - FLAGS.crop_size)

    return img[rand_h:rand_h + FLAGS.crop_size, rand_w:rand_w + FLAGS.crop_size, :]


def load_and_save_data(FLAGS):
    """make HR and LR data. And save them as npz files"""
    all_file_path = glob.glob(FLAGS.data_dir + '/*')

    ret_HR_image = []
    ret_LR_image = []

    for file in all_file_path:
        img = cv2.imread(file)
        filename = file.rsplit('/', 1)[-1]

        # crop patches if flag is true. Otherwise just resize HR and LR images
        if FLAGS.crop:
            img_h, img_w, _ = img.shape

            if (img_h < FLAGS.crop_size) or (img_w < FLAGS.crop_size):
                print('Skip crop target image because of insufficient size')
                continue

            HR_image = crop(img, FLAGS)
            LR_crop_size = np.int(np.floor(FLAGS.crop_size / FLAGS.scale_SR))
            LR_image = cv2.resize(HR_image, (LR_crop_size, LR_crop_size), interpolation=cv2.INTER_LANCZOS4)
        else:
            HR_image = cv2.resize(img, (FLAGS.HR_image_size, FLAGS.HR_image_size), interpolation=cv2.INTER_LANCZOS4)
            LR_image = cv2.resize(img, (FLAGS.LR_image_size, FLAGS.LR_image_size), interpolation=cv2.INTER_LANCZOS4)

        cv2.imwrite(FLAGS.HR_data_dir + '/' + filename, HR_image)
        cv2.imwrite(FLAGS.LR_data_dir + '/' + filename, LR_image)

        ret_HR_image.append(HR_image)
        ret_LR_image.append(LR_image)

    ret_HR_image = np.array(ret_HR_image)
    ret_LR_image = np.array(ret_LR_image)

    np.savez(FLAGS.npz_data_dir + '/' + FLAGS.HR_npz_filename, images=ret_HR_image)
    np.savez(FLAGS.npz_data_dir + '/' + FLAGS.LR_npz_filename, images=ret_LR_image)

    return ret_HR_image, ret_LR_image


def load_npz_data(FLAGS):
    """load array data from data_path"""
    return np.load(FLAGS.npz_data_dir + '/' + FLAGS.HR_npz_filename)['images'], \
           np.load(FLAGS.npz_data_dir + '/' + FLAGS.LR_npz_filename)['images']


def load_inference_data(FLAGS):
    """load data from directory for inference"""
    all_file_path = glob.glob(FLAGS.data_dir + '/*')

    ret_LR_image = []
    ret_filename = []

    for file in all_file_path:
        img = cv2.imread(file)
        img = normalize_images(img)
        ret_LR_image.append(img[0][np.newaxis, ...])

        ret_filename.append(file.rsplit('/', 1)[-1])

    return ret_LR_image, ret_filename