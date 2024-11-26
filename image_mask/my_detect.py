# YOLOv3 🚀 by Ultralytics, GPL-3.0 license
"""
Run YOLOv3 detection inference on images, videos, directories, globs, YouTube, webcam, streams, etc.

Usage - sources:
    $ python detect.py --weights yolov5s.pt --source 0                               # webcam
                                                     img.jpg                         # image
                                                     vid.mp4                         # video
                                                     screen                          # screenshot
                                                     path/                           # directory
                                                     list.txt                        # list of images
                                                     list.streams                    # list of streams
                                                     'path/*.jpg'                    # glob
                                                     'https://youtu.be/Zgi9g1ksQHc'  # YouTube
                                                     'rtsp://example.com/media.mp4'  # RTSP, RTMP, HTTP stream

Usage - formats:
    $ python detect.py --weights yolov5s.pt                 # PyTorch
                                 yolov5s.torchscript        # TorchScript
                                 yolov5s.onnx               # ONNX Runtime or OpenCV DNN with --dnn
                                 yolov5s_openvino_model     # OpenVINO
                                 yolov5s.engine             # TensorRT
                                 yolov5s.mlmodel            # CoreML (macOS-only)
                                 yolov5s_saved_model        # TensorFlow SavedModel
                                 yolov5s.pb                 # TensorFlow GraphDef
                                 yolov5s.tflite             # TensorFlow Lite
                                 yolov5s_edgetpu.tflite     # TensorFlow Edge TPU
                                 yolov5s_paddle_model       # PaddlePaddle
"""

import argparse
import os
import platform
import sys
from pathlib import Path
import pickle 

import torch
from PIL import Image
import numpy as np 
from tqdm import tqdm 

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLOv3 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

from models.common import DetectMultiBackend
from utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadImages, LoadScreenshots, LoadStreams
from utils.general import (LOGGER, Profile, check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
                           increment_path, non_max_suppression, print_args, scale_boxes, strip_optimizer, xyxy2xywh)
from utils.plots import Annotator, colors, save_one_box
from utils.torch_utils import select_device, smart_inference_mode

#yolov5s.pt
#yolov3-spp-ultralytics.pt

@smart_inference_mode()
def run(
        weights=ROOT / 'yolov3-spp-ultralytics.pt',  # model path or triton URL
        source=ROOT / 'data/images',  # file/dir/URL/glob/screen/0(webcam)
        data=ROOT / 'data/coco128.yaml',  # dataset.yaml path
        imgsz=(640, 640),  # inference size (height, width)
        conf_thres=0.25,  # confidence threshold
        iou_thres=0.45,  # NMS IOU threshold
        max_det=1000,  # maximum detections per image
        device='',  # cuda device, i.e. 0 or 0,1,2,3 or cpu
        view_img=False,  # show results
        save_txt=False,  # save results to *.txt
        save_conf=False,  # save confidences in --save-txt labels
        save_crop=False,  # save cropped prediction boxes
        nosave=False,  # do not save images/videos
        classes=None,  # filter by class: --class 0, or --class 0 2 3
        agnostic_nms=False,  # class-agnostic NMS
        augment=False,  # augmented inference
        visualize=False,  # visualize features
        update=False,  # update all models
        project=ROOT / 'runs/detect',  # save results to project/name
        name='exp',  # save results to project/name
        exist_ok=False,  # existing project/name ok, do not increment
        line_thickness=3,  # bounding box thickness (pixels)
        hide_labels=False,  # hide labels
        hide_conf=False,  # hide confidences
        half=False,  # use FP16 half-precision inference
        dnn=False,  # use OpenCV DNN for ONNX inference
        vid_stride=1,  # video frame-rate stride
        split_id=-1,
):
    #assert split_id!=-1
    source = str(source)
    save_img = not nosave and not source.endswith('.txt')  # save inference images
    is_file = Path(source).suffix[1:] in (IMG_FORMATS + VID_FORMATS)
    is_url = source.lower().startswith(('rtsp://', 'rtmp://', 'http://', 'https://'))
    webcam = source.isnumeric() or source.endswith('.streams') or (is_url and not is_file)
    screenshot = source.lower().startswith('screen')
    if is_url and is_file:
        source = check_file(source)  # download

    # Directories
    save_dir = increment_path(Path(project) / name, exist_ok=exist_ok)  # increment run
    (save_dir / 'labels' if save_txt else save_dir).mkdir(parents=True, exist_ok=True)  # make dir

    # Load model
    device = select_device(device)
    model = DetectMultiBackend(weights, device=device, dnn=dnn, data=data, fp16=half)
    stride, names, pt = model.stride, model.names, model.pt
    imgsz = check_img_size(imgsz, s=stride)  # check image size

    # Dataloader
    bs = 1  # batch_size
    if webcam:
        view_img = check_imshow(warn=True)
        dataset = LoadStreams(source, img_size=imgsz, stride=stride, auto=pt, vid_stride=vid_stride)
        bs = len(dataset)
    elif screenshot:
        dataset = LoadScreenshots(source, img_size=imgsz, stride=stride, auto=pt)
    else:
        dataset = LoadImages(source, img_size=imgsz, stride=stride, auto=pt, vid_stride=vid_stride)
    vid_path, vid_writer = [None] * bs, [None] * bs

    # Run inference
    model.warmup(imgsz=(1 if pt or model.triton else bs, 3, *imgsz))  # warmup
    seen, windows, dt = 0, [], (Profile(), Profile(), Profile())

    file_type = 'valid'
    id2image_hash_file = '/home/zhangjunzhe/news-image-caption/model/transform-and-tell-master/data/nytimes_train/'+file_type+'/image_hashs/id2image_hash.'+file_type+'.pkl'.format(split_id)
    print('id2image_hash_file', id2image_hash_file)
    #id2image_hash
    id2image_hash_op = open(id2image_hash_file, 'rb')
    id2image_hash = pickle.load(id2image_hash_op)
    id2image_hash_op.close()
    #运行代码 CUDA_VISIBLE_DEVICES=3 python my_detect.py --weights yolov5s.pt --img 224 --conf 0.3 --iou-thres 0.6 --agnostic-nms --source data/images

    # for path, im, im0s, vid_cap, s in dataset:
    id2yolo_box = {}
    for id in tqdm(id2image_hash):
        path = id2image_hash[id]
        #/home/zhangjunzhe/news-image-caption/model/transform-and-tell-master/data/nytimes/images_processed
        path = '/home/zhangjunzhe/news-image-caption/model/transform-and-tell-master/data/nytimes/images_processed/'+path+'.jpg'

        im0s = cv2.imread(path)
        #print(im0s.shape)
        #本身就是224 应该不用改吧
        img = im0s[:,:,::-1].transpose(2, 0, 1) # BGR -> RGB
        #他默认是416 size 我这里弄成224可以吗 
        #print(img.shape)
        img = np.ascontiguousarray(img)

    # for path, img, im0s, _ in tqdm(dataset):
        #dataset的iter

        if img is None:
            assert False

        img = torch.from_numpy(img).to(device)
        img = img.float()
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        pil_image = Image.open(path)

        # with dt[0]:
        #     #im = torch.from_numpy(im).to(model.device)
        #     img = img.half() if model.fp16 else im.float()  # uint8 to fp16/32
        #     im /= 255  # 0 - 255 to 0.0 - 1.0
        #     if len(im.shape) == 3:
        #         im = im[None]  # expand for batch dim

        # Inference
        with dt[1]:
            #visualize = increment_path(save_dir / Path(path).stem, mkdir=True) if visualize else False
            pred = model(img, augment=augment)

        # NMS
        with dt[2]:
            pred = non_max_suppression(pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)

        # Second-stage classifier (optional)
        # pred = utils.general.apply_classifier(pred, classifier_model, im, im0s)

        # Process predictions
        for i, det in enumerate(pred):  # per image
            seen += 1
            # if webcam:  # batch_size >= 1
            #     p, im0, frame = path[i], im0s[i].copy(), dataset.count
            #     s += f'{i}: '
            # else:
            #     p, im0, frame = path, im0s.copy(), getattr(dataset, 'frame', 0)

            # p = Path(p)  # to Path
            # # save_path = str(save_dir / p.name)  # im.jpg
            # # txt_path = str(save_dir / 'labels' / p.stem) + ('' if dataset.mode == 'image' else f'_{frame}')  # im.txt
            # s += '%gx%g ' % im.shape[2:]  # print string
            # gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
            # imc = im0.copy() if save_crop else im0  # for save_crop
            # annotator = Annotator(im0, line_width=line_thickness, example=str(names))
            #if len(det):
                # Rescale boxes from img_size to im0 size
                #det[:, :4] = scale_boxes(im.shape[2:], det[:, :4], im0.shape).round()

                # Print results
                # for c in det[:, 5].unique():
                #     n = (det[:, 5] == c).sum()  # detections per class
                #     s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string

                # Write results
                #[x, y, x, y, conf, cls] det应该死boxes
                # print(det)
        final_det = pred[0].cpu()
        if len(final_det)!=0:
            id2yolo_box[id] = final_det
        else:
            id2yolo_box[id] = []
    
    id2yolo_box_file = './id2yolov5_boxes.valid.pkl'
    id2yolo_box_op = open(id2yolo_box_file, 'wb')
    pickle.dump(id2yolo_box, id2yolo_box_op)
    id2yolo_box_op.close()




                # for *xyxy, conf, cls in reversed(det):
                #     if save_txt:  # Write to file
                #         xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
                #         line = (cls, *xywh, conf) if save_conf else (cls, *xywh)  # label format
                #         with open(f'{txt_path}.txt', 'a') as f:
                #             f.write(('%g ' * len(line)).rstrip() % line + '\n')

                #     if save_img or save_crop or view_img:  # Add bbox to image
                #         c = int(cls)  # integer class
                #         label = None if hide_labels else (names[c] if hide_conf else f'{names[c]} {conf:.2f}')
                #         annotator.box_label(xyxy, label, color=colors(c, True))
                #     if save_crop:
                #         save_one_box(xyxy, imc, file=save_dir / 'crops' / names[c] / f'{p.stem}.jpg', BGR=True)

            # Stream results
            # im0 = annotator.result()
            # if view_img:
            #     if platform.system() == 'Linux' and p not in windows:
            #         windows.append(p)
            #         cv2.namedWindow(str(p), cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)  # allow window resize (Linux)
            #         cv2.resizeWindow(str(p), im0.shape[1], im0.shape[0])
            #     cv2.imshow(str(p), im0)
            #     cv2.waitKey(1)  # 1 millisecond

            # Save results (image with detections)
            # if save_img:
            #     if dataset.mode == 'image':
            #         cv2.imwrite(save_path, im0)
            #     else:  # 'video' or 'stream'
            #         if vid_path[i] != save_path:  # new video
            #             vid_path[i] = save_path
            #             if isinstance(vid_writer[i], cv2.VideoWriter):
            #                 vid_writer[i].release()  # release previous video writer
            #             if vid_cap:  # video
            #                 fps = vid_cap.get(cv2.CAP_PROP_FPS)
            #                 w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            #                 h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            #             else:  # stream
            #                 fps, w, h = 30, im0.shape[1], im0.shape[0]
            #             save_path = str(Path(save_path).with_suffix('.mp4'))  # force *.mp4 suffix on results videos
            #             vid_writer[i] = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
            #         vid_writer[i].write(im0)

        # Print time (inference-only)
        # LOGGER.info(f"{s}{'' if len(det) else '(no detections), '}{dt[1].dt * 1E3:.1f}ms")

    # Print results
    # t = tuple(x.t / seen * 1E3 for x in dt)  # speeds per image
    # LOGGER.info(f'Speed: %.1fms pre-process, %.1fms inference, %.1fms NMS per image at shape {(1, 3, *imgsz)}' % t)
    # if save_txt or save_img:
    #     s = f"\n{len(list(save_dir.glob('labels/*.txt')))} labels saved to {save_dir / 'labels'}" if save_txt else ''
    #     LOGGER.info(f"Results saved to {colorstr('bold', save_dir)}{s}")
    # if update:
    #     strip_optimizer(weights[0])  # update model (to fix SourceChangeWarning)


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights',
                        nargs='+',
                        type=str,
                        default=ROOT / 'yolov3-tiny.pt',
                        help='model path or triton URL')
    parser.add_argument('--source', type=str, default=ROOT / 'data/images', help='file/dir/URL/glob/screen/0(webcam)')
    parser.add_argument('--data', type=str, default=ROOT / 'data/coco128.yaml', help='(optional) dataset.yaml path')
    parser.add_argument('--imgsz', '--img', '--img-size', nargs='+', type=int, default=[640], help='inference size h,w')
    parser.add_argument('--conf-thres', type=float, default=0.25, help='confidence threshold')
    parser.add_argument('--iou-thres', type=float, default=0.45, help='NMS IoU threshold')
    parser.add_argument('--max-det', type=int, default=1000, help='maximum detections per image')
    parser.add_argument('--split_id', type=int, default=-1)
    parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--view-img', action='store_true', help='show results')
    parser.add_argument('--save-txt', action='store_true', help='save results to *.txt')
    parser.add_argument('--save-conf', action='store_true', help='save confidences in --save-txt labels')
    parser.add_argument('--save-crop', action='store_true', help='save cropped prediction boxes')
    parser.add_argument('--nosave', action='store_true', help='do not save images/videos')
    parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --classes 0, or --classes 0 2 3')
    parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
    parser.add_argument('--augment', action='store_true', help='augmented inference')
    parser.add_argument('--visualize', action='store_true', help='visualize features')
    parser.add_argument('--update', action='store_true', help='update all models')
    parser.add_argument('--project', default=ROOT / 'runs/detect', help='save results to project/name')
    parser.add_argument('--name', default='exp', help='save results to project/name')
    parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
    parser.add_argument('--line-thickness', default=3, type=int, help='bounding box thickness (pixels)')
    parser.add_argument('--hide-labels', default=False, action='store_true', help='hide labels')
    parser.add_argument('--hide-conf', default=False, action='store_true', help='hide confidences')
    parser.add_argument('--half', action='store_true', help='use FP16 half-precision inference')
    parser.add_argument('--dnn', action='store_true', help='use OpenCV DNN for ONNX inference')
    parser.add_argument('--vid-stride', type=int, default=1, help='video frame-rate stride')
    opt = parser.parse_args()
    opt.imgsz *= 2 if len(opt.imgsz) == 1 else 1  # expand
    print_args(vars(opt))
    return opt


def main(opt):
    check_requirements(exclude=('tensorboard', 'thop'))
    run(**vars(opt))


if __name__ == '__main__':
    opt = parse_opt()
    main(opt)


'''
yolov5 image_size 640
tensor([[6.72000e+02, 3.95000e+02, 8.10000e+02, 8.78000e+02, 8.96192e-01, 0.00000e+00],
        [2.21000e+02, 4.08000e+02, 3.46000e+02, 8.67000e+02, 8.70318e-01, 0.00000e+00],
        [4.90000e+01, 3.90000e+02, 2.48000e+02, 9.12000e+02, 8.51478e-01, 0.00000e+00],
        [1.30000e+01, 2.23000e+02, 8.10000e+02, 7.88000e+02, 8.49443e-01, 5.00000e+00],
        [0.00000e+00, 5.52000e+02, 6.80000e+01, 8.75000e+02, 5.35296e-01, 0.00000e+00]], device='cuda:0')


tensor([[7.43000e+02, 4.80000e+01, 1.14200e+03, 7.20000e+02, 8.79875e-01, 0.00000e+00],
        [4.42000e+02, 4.37000e+02, 4.97000e+02, 7.10000e+02, 6.75375e-01, 2.70000e+01],
        [1.23000e+02, 1.93000e+02, 7.15000e+02, 7.20000e+02, 6.66224e-01, 0.00000e+00],
        [9.79000e+02, 3.14000e+02, 1.02500e+03, 4.16000e+02, 2.61955e-01, 2.70000e+01]], device='cuda:0')

det in tell




yolov5 image_size 800 image_size 影响不大
tensor([[4.80000e+01, 3.89000e+02, 2.42000e+02, 9.09000e+02, 8.71773e-01, 0.00000e+00],
        [2.22000e+02, 4.02000e+02, 3.45000e+02, 8.67000e+02, 8.61636e-01, 0.00000e+00],
        [6.67000e+02, 3.83000e+02, 8.10000e+02, 8.84000e+02, 8.31897e-01, 0.00000e+00],
        [0.00000e+00, 1.74000e+02, 8.03000e+02, 8.18000e+02, 6.64067e-01, 5.00000e+00],
        [1.00000e+00, 5.53000e+02, 7.90000e+01, 8.93000e+02, 4.65944e-01, 0.00000e+00]], device='cuda:0')
tensor([[7.39000e+02, 4.80000e+01, 1.14500e+03, 7.19000e+02, 7.62167e-01, 0.00000e+00],
        [4.34000e+02, 4.36000e+02, 5.09000e+02, 7.15000e+02, 7.06525e-01, 2.70000e+01],
        [9.77000e+02, 3.15000e+02, 1.02700e+03, 4.18000e+02, 5.45057e-01, 2.70000e+01],
        [1.45000e+02, 1.86000e+02, 7.08000e+02, 7.20000e+02, 4.62852e-01, 0.00000e+00]], device='cuda:0')

myfile

'''

#myconfig
'''
    img_size = (224, 224)
    ob_conf = 0.3#目标检测置信度阈值
    iou_thres = 0.6 #IOU threshold for NMS [default: 0.6].
    pred = non_max_suppression(pred, ob_conf, iou_thres,
                                classes=None, agnostic=True)
'''

#my test image
'''
yolov5
默认 python my_detect.py --weights yolov5s.pt --img 224 --conf 0.25 --source data/images
tensor([[  0.00000,   0.00000, 116.00000, 223.00000,   0.88016,   0.00000],
        [ 83.00000,  79.00000, 126.00000, 216.00000,   0.68833,   0.00000],
        [133.00000,   2.00000, 223.00000, 215.00000,   0.61674,   0.00000]], device='cuda:0')

#先分析一下
默认 CUDA_VISIBLE_DEVICES=1 python my_detect.py --weights yolov5s.pt --img 224 --conf 0.3 --iou-thres 0.6 --agnostic-nms --split_id 0

'''