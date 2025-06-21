import abc
import cv2
import numpy as np
import ast
import onnx
import onnxruntime
from pkg.projectvar import constants as consts
# from huggingface_hub import hf_hub_download


class DocLayoutModel(abc.ABC):
    @staticmethod
    def load_onnx():
        model = OnnxModel.from_pretrained(
            repo_id="wybxc/DocLayout-YOLO-DocStructBench-onnx",
            filename="doclayout_yolo_docstructbench_imgsz1024.onnx",
        )
        return model

    @staticmethod
    def load_available():
        return DocLayoutModel.load_onnx()

    @property
    @abc.abstractmethod
    def stride(self) -> int:
        """Stride of the model input."""
        pass

    @abc.abstractmethod
    def predict(self, image, imgsz=1024, **kwargs) -> list:
        """
        Predict the layout of a document page.

        Args:
            image: The image of the document page.
            imgsz: Resize the image to this size. Must be a multiple of the stride.
            **kwargs: Additional arguments.
        """
        pass


class YoloResult:
    """Helper class to store detection results from ONNX model."""

    def __init__(self, boxes, names):
        self.boxes = [YoloBox(data=d) for d in boxes]
        self.boxes.sort(key=lambda x: x.conf, reverse=True)
        self.names = names


class YoloBox:
    """Helper class to store detection results from ONNX model."""

    def __init__(self, data):
        self.xyxy = data[:4]
        self.conf = data[-2]
        self.cls = data[-1]


class OnnxModel(DocLayoutModel):
    def __init__(self, model_path: str):
        self.model_path = model_path

        model = onnx.load(model_path)
        metadata = {d.key: d.value for d in model.metadata_props}
        self._stride = ast.literal_eval(metadata["stride"])
        self._names = ast.literal_eval(metadata["names"])

        self.model = onnxruntime.InferenceSession(model.SerializeToString())

    @staticmethod
    def from_pretrained(repo_id: str, filename: str):
        # pth = hf_hub_download(repo_id=repo_id, filename=filename, etag_timeout=1)\
        if consts.SYSTEM == consts.WINDOWS:
            pth = r'./_internal/models--wybxc--DocLayout-YOLO-DocStructBench-onnx/snapshots/ee7c3d744e5c47c58e267044ac825f95abe69653/doclayout_yolo_docstructbench_imgsz1024.onnx'
        else:
            import sys,os
            if getattr(sys, 'frozen', False):
                # 打包环境
                base_path = os.path.abspath(os.path.join(os.path.dirname(sys.executable),'../Resources'))
                pth = os.path.join(
                    base_path,
                    "resources/models/snapshots/ee7c3d744e5c47c58e267044ac825f95abe69653/doclayout_yolo_docstructbench_imgsz1024.onnx"
                )
            else:
                # 开发环境
                pth = os.path.abspath(
                    './_internal/models--wybxc--DocLayout-YOLO-DocStructBench-onnx/snapshots/ee7c3d744e5c47c58e267044ac825f95abe69653/doclayout_yolo_docstructbench_imgsz1024.onnx'
                )
            if not os.path.exists(pth):
                raise FileNotFoundError(f"模型路径不存在：{pth}")
        return OnnxModel(pth)

    @property
    def stride(self):
        return self._stride

    def resize_and_pad_image(self, image, new_shape):
        """
        Resize and pad the image to the specified size, ensuring dimensions are multiples of stride.

        Parameters:
        - image: Input image
        - new_shape: Target size (integer or (height, width) tuple)
        - stride: Padding alignment stride, default 32

        Returns:
        - Processed image
        """
        if isinstance(new_shape, int):
            new_shape = (new_shape, new_shape)

        h, w = image.shape[:2]
        new_h, new_w = new_shape

        # Calculate scaling ratio
        r = min(new_h / h, new_w / w)
        resized_h, resized_w = int(round(h * r)), int(round(w * r))

        # Resize image
        image = cv2.resize(
            image, (resized_w, resized_h), interpolation=cv2.INTER_LINEAR
        )

        # Calculate padding size and align to stride multiple
        pad_w = (new_w - resized_w) % self.stride
        pad_h = (new_h - resized_h) % self.stride
        top, bottom = pad_h // 2, pad_h - pad_h // 2
        left, right = pad_w // 2, pad_w - pad_w // 2

        # Add padding
        image = cv2.copyMakeBorder(
            image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114)
        )

        return image

    def scale_boxes(self, img1_shape, boxes, img0_shape):
        """
        Rescales bounding boxes (in the format of xyxy by default) from the shape of the image they were originally
        specified in (img1_shape) to the shape of a different image (img0_shape).

        Args:
            img1_shape (tuple): The shape of the image that the bounding boxes are for,
                in the format of (height, width).
            boxes (torch.Tensor): the bounding boxes of the objects in the image, in the format of (x1, y1, x2, y2)
            img0_shape (tuple): the shape of the target image, in the format of (height, width).

        Returns:
            boxes (torch.Tensor): The scaled bounding boxes, in the format of (x1, y1, x2, y2)
        """

        # Calculate scaling ratio
        gain = min(img1_shape[0] / img0_shape[0], img1_shape[1] / img0_shape[1])

        # Calculate padding size
        pad_x = round((img1_shape[1] - img0_shape[1] * gain) / 2 - 0.1)
        pad_y = round((img1_shape[0] - img0_shape[0] * gain) / 2 - 0.1)

        # Remove padding and scale boxes
        boxes[..., :4] = (boxes[..., :4] - [pad_x, pad_y, pad_x, pad_y]) / gain
        return boxes

    def predict(self, image, imgsz=1024, **kwargs):
        # Preprocess input image
        orig_h, orig_w = image.shape[:2]
        pix = self.resize_and_pad_image(image, new_shape=imgsz)
        pix = np.transpose(pix, (2, 0, 1))  # CHW
        pix = np.expand_dims(pix, axis=0)  # BCHW
        pix = pix.astype(np.float32) / 255.0  # Normalize to [0, 1]
        new_h, new_w = pix.shape[2:]

        # Run inference
        preds = self.model.run(None, {"images": pix})[0]

        # Postprocess predictions
        preds = preds[preds[..., 4] > 0.25]
        preds[..., :4] = self.scale_boxes(
            (new_h, new_w), preds[..., :4], (orig_h, orig_w)
        )
        return [YoloResult(boxes=preds, names=self._names)]


    def save_layout_as_image(self,pdf_image, output_image_file):
        """
        使用 doclayout.py 提取 PDF 图像的布局并保存为图像文件。
        """
        from PIL import Image, ImageDraw
        # 获取布局预测结果
        result = self.predict(pdf_image)

        # 获取页面的宽度和高度
        width, height = pdf_image.shape[1], pdf_image.shape[0]

        # 创建一个白色背景的图像
        # img = Image.new("RGB", (int(width), int(height)), "white")
        img = Image.fromarray(cv2.cvtColor(pdf_image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img)

        # 遍历预测结果，绘制边界框和标签
        for result_obj in result:
            boxes = result_obj.boxes  # 获取所有预测的边界框
            for box in boxes:
                # 获取每个框的坐标
                x0, y0, x1, y1 = box.xyxy
                # print(f"x0,y0, x1,y1:{x0,y0, x1,y1}")
                # 绘制边界框
                draw.rectangle([x0, y0, x1, y1], outline="black", width=2)

                # 可选：可以在框内绘制标签
                label = result_obj.names[box.cls]  # 获取标签名称
                draw.text((x0, y0), f"{x0, y0,label}", fill="green") # +是向下 -是向上

        # 保存图像到文件
        img.save(output_image_file)
        print(f"Layout saved as image: {output_image_file}")