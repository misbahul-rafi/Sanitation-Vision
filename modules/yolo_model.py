from ultralytics import YOLO
import logging

logger = logging.getLogger("SanitationVision")

class YOLOModel:
    def __init__(self, model_path):
        try:
            logger.info(f"loading YOLO model from {model_path}")
            self._model = YOLO(model_path)
            logger.info("YOLO model loaded successfully")
        except Exception as e:
            logger.critical(f"failed to load YOLO model: {e}")
            raise
        

    def predict(self, image, set_annotated):
        logger.debug("running prediction...")
        try:
            results = self._model.predict(
                image,
                verbose=False,
                save=False,
                imgsz=640,
                exist_ok=True
            )
        except Exception as e:
            logger.error(f"YOLO prediction failed: {e}")
            return None, None
        
        if not results or len(results) == 0:
            logger.warning("YOLO returned empty result")
            return None, None

        try:
            objects = results[0]
        except Exception as e:
            logger.error(f"failed reading YOLO result object: {e}")
            return None, None
        
        try:
            annotated_image = objects.plot()
        except Exception as e:
            logger.error(f"failed generating annotated image: {e}")
            annotated_image = None

        if annotated_image is not None:
            try:
                set_annotated(annotated_image)
            except Exception as e:
                logger.error(f"failed sending annotated image to camera: {e}")
        # if objects.boxes is None or len(objects.boxes) == 0:
        #     logger.debug("Tidak ada objek terdeteksi pada frame ini")
        # else:
        #     items = []
        #     for box in objects.boxes:
        #         cls_id = int(box.cls.item())
        #         label = objects.names[cls_id]
        #         items.append(label)
            # print(items)
        logger.debug("prediction completed successfully")
        return objects
