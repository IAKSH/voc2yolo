import os
import shutil
import random
import argparse
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import yaml
import xml.etree.ElementTree as ET

# a dictionary to store the class mapping
class_mapping = {}

def copy_and_convert_file(src, dst):
    if src.endswith('.jpg'):
        img = Image.open(src)
        img.save(dst.replace('.jpg', '.png'))
    elif src.endswith('.png'):
        shutil.copy(src, dst)

def convert_annotation(xml_path):
    # parse the XML file
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # get the size of the image
    size = root.find('size')
    width = int(size.find('width').text)
    height = int(size.find('height').text)

    # initialize a list to store the annotations
    annotations = []

    # Iterate over each object in the XML
    for obj in root.iter('object'):
        # get the class name
        class_name = obj.find('name').text

        # if the class name is not in the class mapping, add it
        if class_name not in class_mapping:
            class_mapping[class_name] = len(class_mapping)

        # get the class index
        class_index = class_mapping[class_name]

        # get the bounding box coordinates
        xmlbox = obj.find('bndbox')
        xmin = int(xmlbox.find('xmin').text)
        ymin = int(xmlbox.find('ymin').text)
        xmax = int(xmlbox.find('xmax').text)
        ymax = int(xmlbox.find('ymax').text)

        # convert the coordinates to YOLO format
        x_center = (xmin + xmax) / (2 * width)
        y_center = (ymin + ymax) / (2 * height)
        box_width = (xmax - xmin) / width
        box_height = (ymax - ymin) / height

        # add the annotation to the list
        annotations.append((class_index, x_center, y_center, box_width, box_height))

    # return the list of annotations
    return annotations

def convert_all_annotations(input_folder, output_folder):
    # iterate over each XML file in the input folder
    for filename in os.listdir(input_folder):
        if filename.endswith('.xml'):
            # convert the XML annotations to YOLO format
            annotations = convert_annotation(os.path.join(input_folder, filename))

            # write the annotations to a .txt file in the output folder
            with open(os.path.join(output_folder, os.path.splitext(filename)[0] + '.txt'), 'w') as f:
                for annotation in annotations:
                    f.write(' '.join(map(str, annotation)) + '\n')

def split_dataset(txt_folder, img_folder, out_folder, ratio=0.8, recursive=False, max_workers=1):
    # create temp folder
    temp_txt = os.path.join(out_folder, 'temp_txt')
    temp_img = os.path.join(out_folder, 'temp_img')
    os.makedirs(temp_txt, exist_ok=True)
    os.makedirs(temp_img, exist_ok=True)

    # get all file names from txt_folder
    if recursive:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for root, _, files in os.walk(txt_folder):
                for f in files:
                    if f.endswith('.txt'):
                        executor.submit(shutil.copy, os.path.join(root, f), os.path.join(temp_txt, f))
            for root, _, files in os.walk(img_folder):
                for f in files:
                    if f.endswith('.jpg') or f.endswith('.png'):
                        executor.submit(copy_and_convert_file, os.path.join(root, f), os.path.join(temp_img, os.path.splitext(f)[0] + '.png'))
        filenames = [os.path.splitext(f)[0] for f in os.listdir(temp_txt) if f.endswith('.txt')]
    else:
        filenames = [os.path.splitext(f)[0] for f in os.listdir(txt_folder) if f.endswith('.txt')]

    # shuffle the file names to split train & val
    random.shuffle(filenames)

    # split to train & val
    split_index = int(len(filenames) * ratio)
    train_filenames = filenames[:split_index]
    val_filenames = filenames[split_index:]

    # mkdir if not exist
    os.makedirs(os.path.join(out_folder, 'images', 'train'), exist_ok=True)
    os.makedirs(os.path.join(out_folder, 'images', 'val'), exist_ok=True)
    os.makedirs(os.path.join(out_folder, 'labels', 'train'), exist_ok=True)
    os.makedirs(os.path.join(out_folder, 'labels', 'val'), exist_ok=True)

    # copy train to output folder
    for filename in train_filenames:
        shutil.move(os.path.join(temp_txt, filename + '.txt'), os.path.join(out_folder, 'labels', 'train', filename + '.txt'))
        shutil.move(os.path.join(temp_img, filename + '.png'), os.path.join(out_folder, 'images', 'train', filename + '.png'))

    # copy val to output folder
    for filename in val_filenames:
        shutil.move(os.path.join(temp_txt, filename + '.txt'), os.path.join(out_folder, 'labels', 'val', filename + '.txt'))
        shutil.move(os.path.join(temp_img, filename + '.png'), os.path.join(out_folder, 'images', 'val', filename + '.png'))

    # delete temp folder
    shutil.rmtree(temp_txt)
    shutil.rmtree(temp_img)

    # create the yaml file
    data = {
        'path': '.',
        'train': 'images/train/',
        'val': 'images/val/',
        'nc': len(class_mapping),
        'names': {v: k for k, v in class_mapping.items()}
    }

    with open(os.path.join(out_folder, os.path.basename(out_folder) + '.yaml'), 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='packup')
    parser.add_argument('--xml', type=str, required=True, help='path to voc xml annotation folder')
    parser.add_argument('--img', type=str, required=True, help='path to jpeg image folder')
    parser.add_argument('--out', type=str, required=True, help='output path')
    parser.add_argument('--ratio', type=float, required=False, default=0.8, help='train/val ratio')
    parser.add_argument('--recursive', type=bool, required=False, default=False, help='recursively search each folder')
    parser.add_argument('--max_workers', type=int, required=False, default=1, help='maximum number of threads')
    args = parser.parse_args()

    yolo_txt_path = "./temp_yolo"

    # create a temp folder, for i'm to lazy to add this into functions
    if not os.path.exists(yolo_txt_path):
        os.makedirs(yolo_txt_path)

    convert_all_annotations(args.xml, yolo_txt_path)
    split_dataset(yolo_txt_path, args.img, args.out, args.ratio, args.recursive, args.max_workers)

    # remove temp folder
    shutil.rmtree(yolo_txt_path)