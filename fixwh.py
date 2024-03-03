import os
import argparse
import xml.etree.ElementTree as ET
from PIL import Image

def correct_size_in_xml(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    image_path = root.find('path').text
    image_path = os.path.join(os.path.dirname(xml_path), image_path)
    with Image.open(image_path) as img:
        width, height = img.size

    # update width and height in XML
    size = root.find('size')
    size.find('width').text = str(width)
    size.find('height').text = str(height)
    tree.write(xml_path)

def correct_all_xmls_in_folder(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith('.xml'):
            correct_size_in_xml(os.path.join(folder_path, filename))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='correct w & h in xml annotation')
    parser.add_argument('--path', type=str, required=True, help='path to voc xml annotation folder')
    args = parser.parse_args()

    correct_all_xmls_in_folder(args.path)
