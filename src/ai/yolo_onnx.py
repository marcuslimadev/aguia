"""
Detector YOLO usando ONNX Runtime (sem Torch/Ultralytics em runtime)
"""
import logging
import numpy as np
import cv2
from typing import List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """Detecção de objeto"""
    class_id: int
    class_name: str
    confidence: float
    x1: int
    y1: int
    x2: int
    y2: int
    track_id: Optional[int] = None

    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        """Retorna bounding box (x1, y1, x2, y2)"""
        return (self.x1, self.y1, self.x2, self.y2)

    @property
    def center(self) -> Tuple[int, int]:
        """Retorna centro do bbox"""
        return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)

    @property
    def area(self) -> int:
        """Retorna área do bbox"""
        return (self.x2 - self.x1) * (self.y2 - self.y1)


class YoloOnnxDetector:
    """Detector YOLO com ONNX Runtime"""

    # Classes COCO padrão
    COCO_CLASSES = [
        'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train',
        'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign',
        'parking meter', 'bench', 'cat', 'dog', 'horse', 'sheep', 'cow',
        'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella',
        'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard',
        'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard',
        'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork',
        'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
        'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
        'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv',
        'laptop', 'mouse', 'remote', 'keyboard', 'microwave', 'oven',
        'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase',
        'scissors', 'teddy bear', 'hair drier', 'toothbrush'
    ]

    def __init__(self, model_path: Path, conf_threshold: float = 0.5):
        """
        Inicializa detector YOLO ONNX

        Args:
            model_path: Caminho para modelo ONNX
            conf_threshold: Threshold de confiança
        """
        self.model_path = Path(model_path)
        self.conf_threshold = conf_threshold
        self.session = None
        self.input_name = None
        self.output_names = None
        self.input_shape = None

        self._load_model()

    def _load_model(self):
        """Carrega modelo ONNX"""
        try:
            import onnxruntime as ort

            logger.info(f"Carregando modelo ONNX: {self.model_path}")

            if not self.model_path.exists():
                logger.warning(f"Modelo não encontrado: {self.model_path}")
                logger.info("Usando detector mock para desenvolvimento")
                self.session = None
                return

            # Criar sessão ONNX
            self.session = ort.InferenceSession(
                str(self.model_path),
                providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
            )

            # Obter informações de entrada/saída
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [o.name for o in self.session.get_outputs()]
            self.input_shape = self.session.get_inputs()[0].shape

            logger.info(f"✓ Modelo ONNX carregado com sucesso")
            logger.info(f"  Input: {self.input_name} {self.input_shape}")
            logger.info(f"  Outputs: {self.output_names}")

        except ImportError:
            logger.warning("onnxruntime não instalado. Use: pip install onnxruntime")
            self.session = None

        except Exception as e:
            logger.error(f"Erro ao carregar modelo ONNX: {e}")
            self.session = None

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Detecta objetos em frame

        Args:
            frame: Frame BGR numpy array

        Returns:
            Lista de detecções
        """
        if self.session is None:
            return self._mock_detect(frame)

        try:
            # Preprocessar frame
            input_data = self._preprocess(frame)

            # Inferência
            outputs = self.session.run(self.output_names, {self.input_name: input_data})

            # Pós-processar
            detections = self._postprocess(outputs, frame.shape)

            return detections

        except Exception as e:
            logger.error(f"Erro durante detecção: {e}")
            return []

    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        """Preprocessa frame para modelo"""
        # Redimensionar para tamanho do modelo
        h, w = frame.shape[:2]
        model_h, model_w = 640, 640  # Tamanho padrão YOLOv8

        # Manter aspect ratio com padding
        scale = min(model_w / w, model_h / h)
        new_w, new_h = int(w * scale), int(h * scale)

        resized = cv2.resize(frame, (new_w, new_h))

        # Adicionar padding
        padded = np.full((model_h, model_w, 3), 114, dtype=np.uint8)
        pad_x = (model_w - new_w) // 2
        pad_y = (model_h - new_h) // 2
        padded[pad_y:pad_y+new_h, pad_x:pad_x+new_w] = resized

        # Normalizar
        input_data = padded.astype(np.float32) / 255.0
        input_data = np.transpose(input_data, (2, 0, 1))
        input_data = np.expand_dims(input_data, 0)

        return input_data

    def _postprocess(self, outputs: List[np.ndarray], frame_shape: Tuple) -> List[Detection]:
        """Pós-processa saídas do modelo com NMS"""
        h, w = frame_shape[:2]
        detections = []

        # Saída típica YOLO: [batch, num_boxes, 85]
        # 85 = 4 (bbox) + 1 (objectness) + 80 (classes)
        output = outputs[0]

        if len(output.shape) == 3:
            output = output[0]  # Remove batch dimension

        # Coletar todas as detecções acima do threshold
        boxes = []
        scores = []
        class_ids = []

        for pred in output:
            objectness = pred[4]
            if objectness < self.conf_threshold:
                continue

            # Obter classe com maior confiança
            class_scores = pred[5:]
            class_id = np.argmax(class_scores)
            confidence = float(class_scores[class_id] * objectness)

            if confidence < self.conf_threshold:
                continue

            # Converter bbox (YOLO format: x_center, y_center, width, height)
            x_center, y_center, box_w, box_h = pred[:4]

            # Desnormalizar para dimensões do frame
            scale_x = w / 640
            scale_y = h / 640
            
            x_center = x_center * scale_x
            y_center = y_center * scale_y
            box_w = box_w * scale_x
            box_h = box_h * scale_y

            x1 = max(0, int(x_center - box_w / 2))
            y1 = max(0, int(y_center - box_h / 2))
            x2 = min(w, int(x_center + box_w / 2))
            y2 = min(h, int(y_center + box_h / 2))

            boxes.append([x1, y1, x2, y2])
            scores.append(confidence)
            class_ids.append(int(class_id))

        # Aplicar NMS (Non-Maximum Suppression) para remover duplicatas
        if len(boxes) > 0:
            indices = self._nms(boxes, scores, iou_threshold=0.45)
            
            for idx in indices:
                class_id = class_ids[idx]
                class_name = self.COCO_CLASSES[class_id] if class_id < len(self.COCO_CLASSES) else f"class_{class_id}"
                
                detection = Detection(
                    class_id=class_id,
                    class_name=class_name,
                    confidence=float(scores[idx]),
                    x1=boxes[idx][0],
                    y1=boxes[idx][1],
                    x2=boxes[idx][2],
                    y2=boxes[idx][3]
                )
                detections.append(detection)

        return detections
    
    def _nms(self, boxes: List, scores: List[float], iou_threshold: float = 0.45) -> List[int]:
        """
        Non-Maximum Suppression para remover boxes duplicadas
        
        Args:
            boxes: Lista de boxes [x1, y1, x2, y2]
            scores: Lista de scores
            iou_threshold: Threshold de IoU para supressão
            
        Returns:
            Índices das boxes mantidas
        """
        boxes = np.array(boxes)
        scores = np.array(scores)
        
        # Coordenadas
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]
        
        # Áreas
        areas = (x2 - x1) * (y2 - y1)
        
        # Ordenar por score (decrescente)
        order = scores.argsort()[::-1]
        
        keep = []
        while order.size > 0:
            # Manter o de maior score
            i = order[0]
            keep.append(i)
            
            # Calcular IoU com os restantes
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            
            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            intersection = w * h
            
            iou = intersection / (areas[i] + areas[order[1:]] - intersection)
            
            # Manter apenas os com IoU < threshold
            inds = np.where(iou <= iou_threshold)[0]
            order = order[inds + 1]
        
        return keep

    def _mock_detect(self, frame: np.ndarray) -> List[Detection]:
        """Detector mock para desenvolvimento (sem modelo ONNX)"""
        # Retornar detecções simuladas para testes
        h, w = frame.shape[:2]

        detections = [
            Detection(
                class_id=0,
                class_name='person',
                confidence=0.85,
                x1=int(w * 0.2),
                y1=int(h * 0.1),
                x2=int(w * 0.4),
                y2=int(h * 0.6)
            )
        ]

        return detections


class ObjectTracker:
    """Rastreador de objetos simples (Centroid Tracking)"""

    def __init__(self, max_distance: int = 50, max_disappeared: int = 30):
        """
        Inicializa rastreador

        Args:
            max_distance: Distância máxima para associação
            max_disappeared: Frames máximos antes de remover track
        """
        self.max_distance = max_distance
        self.max_disappeared = max_disappeared
        self.tracks = {}
        self.next_id = 0

    def update(self, detections: List[Detection]) -> List[Detection]:
        """
        Atualiza tracks com novas detecções

        Args:
            detections: Lista de detecções

        Returns:
            Detecções com track_id atualizado
        """
        if len(detections) == 0:
            # Incrementar disappeared counter
            for track_id in list(self.tracks.keys()):
                self.tracks[track_id]['disappeared'] += 1

                if self.tracks[track_id]['disappeared'] > self.max_disappeared:
                    del self.tracks[track_id]

            return []

        # Calcular centroides
        centroids = np.array([d.center for d in detections])

        # Se não há tracks, criar novos
        if len(self.tracks) == 0:
            for i, centroid in enumerate(centroids):
                self.tracks[self.next_id] = {
                    'centroid': centroid,
                    'disappeared': 0
                }
                detections[i].track_id = self.next_id
                self.next_id += 1

            return detections

        # Associar detecções a tracks existentes
        track_ids = list(self.tracks.keys())
        track_centroids = np.array([self.tracks[tid]['centroid'] for tid in track_ids])

        # Calcular distâncias
        distances = np.zeros((len(track_centroids), len(centroids)))
        for i, track_centroid in enumerate(track_centroids):
            for j, centroid in enumerate(centroids):
                distances[i, j] = np.linalg.norm(track_centroid - centroid)

        # Associação gulosa
        rows = np.argsort(distances.min(axis=1))
        cols = np.argsort(distances.argmin(axis=0))

        used_rows = set()
        used_cols = set()

        for row in rows:
            if row in used_rows:
                continue

            col = distances[row].argmin()
            if col in used_cols or distances[row, col] > self.max_distance:
                continue

            track_id = track_ids[row]
            self.tracks[track_id]['centroid'] = centroids[col]
            self.tracks[track_id]['disappeared'] = 0
            detections[col].track_id = track_id

            used_rows.add(row)
            used_cols.add(col)

        # Criar novos tracks para detecções não associadas
        for col in range(len(centroids)):
            if col not in used_cols:
                self.tracks[self.next_id] = {
                    'centroid': centroids[col],
                    'disappeared': 0
                }
                detections[col].track_id = self.next_id
                self.next_id += 1

        # Remover tracks desaparecidos
        for track_id in list(self.tracks.keys()):
            self.tracks[track_id]['disappeared'] += 1

            if self.tracks[track_id]['disappeared'] > self.max_disappeared:
                del self.tracks[track_id]

        return detections
