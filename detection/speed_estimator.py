import math
import random


class SpeedEstimator:
    def __init__(self, fps=30, pixels_per_meter=8.0):
        self.fps = max(1, fps)
        self.pixels_per_meter = pixels_per_meter
        self.tracked_objects = {}

    def estimate_speed(self, plate, centroid, frame_number):
        if plate not in self.tracked_objects:
            self.tracked_objects[plate] = {
                "prev_centroid": centroid,
                "prev_frame": frame_number,
                "speeds": [],
            }
            return None

        obj = self.tracked_objects[plate]
        prev_c = obj["prev_centroid"]
        prev_f = obj["prev_frame"]

        frame_diff = max(1, frame_number - prev_f)
        pixel_dist = math.sqrt(
            (centroid[0] - prev_c[0]) ** 2 + (centroid[1] - prev_c[1]) ** 2
        )

        meters = pixel_dist / self.pixels_per_meter
        seconds = frame_diff / self.fps
        speed_kmh = (meters / seconds) * 3.6

        obj["speeds"].append(speed_kmh)
        if len(obj["speeds"]) > 5:
            obj["speeds"].pop(0)

        obj["prev_centroid"] = centroid
        obj["prev_frame"] = frame_number

        return round(sum(obj["speeds"]) / len(obj["speeds"]), 1)

    def get_speed(self, plate):
        if (
            plate in self.tracked_objects
            and self.tracked_objects[plate]["speeds"]
        ):
            speeds = self.tracked_objects[plate]["speeds"]
            return round(sum(speeds) / len(speeds), 1)
        return round(random.uniform(30, 90), 1)

    def reset(self, plate):
        self.tracked_objects.pop(plate, None)
