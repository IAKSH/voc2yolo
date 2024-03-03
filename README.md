# voc2yolo
Convert VOC XML annotation data set to YOLO data set.

## usage

```shell
python ./voc2yolo.py --xml path/to/xml/ --img path/to/img --out output/path --ratio 0.8 --recursive true --max_workers 4
```

The default "path" in the outputting yaml config is ".", you may need to edit it to fet your own directory structure.

```yaml
names:
  0: cat
  1: dog
  2: bird
nc: 3
path: ../datasets/xxx # the path which relative to your YOLO
train: images/train/
val: images/val/
```

# fixwh
This is to correct the width and height in your VOC XML, some times they will turn to be zero, which will cause errors.

## usage
``` shell
python ./fixwh.py --path path/to/xml/
```