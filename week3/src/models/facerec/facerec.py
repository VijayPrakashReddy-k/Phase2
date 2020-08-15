import os

import cv2
import dlib
import numpy as np
import src.models.facerec.faceblendcommon as fbc


class FaceRecognition:
    def __init__(self):
        self._haarcascade_frontalface_default = "model/haarcascade_frontalface_default.xml"
        self._shape_predictor_5_face_landamarks = "model/shape_predictor_5_face_landmarks.dat"
        self._shape_predictor_68_face_landamarks = "model/shape_predictor_68_face_landmarks.dat"
        self._init_objects()

    def _init_objects(self):
        faceDetector = dlib.get_frontal_face_detector()
        landmarkDetector = dlib.shape_predictor(self._shape_predictor_68_face_landamarks)
        return (faceDetector, landmarkDetector)

    @staticmethod
    def downloadArtifacts(self):
        urls = [
            ("model", "http://dlib.net/files/shape_predictor_5_face_landmarks.dat.bz2"),
            ("model", "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2"),
            (
                "model",
                "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml",
            ),
            ("data", "https://github.com/EVA4-RS-Group/Phase2/releases/download/s2/3M-KN95-9501-Dust-Mask_v1.jpg"),
        ]
        for url in urls:
            os.system(f"wget {url[1]} -P ./{url[0]}/")
            if "bz2" in url[1]:
                os.system(f"bzip2 -dk ./{url[0]}/{url[1].split('/')[-1]}")

    def _checkHumanFaces(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + self._haarcascade_frontalface_default)
        faces = faceCascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=3, minSize=(70, 70))
        return faces

    def hasValidHumanFace(self, image):
        faces = self._checkHumanFaces(image)
        if len(faces) == 1:
            return True
        else:
            return False

    def detect_landmarks(self, src_face_img, dest_face_img):
        detector, predictor = self._init_objects()
        src_points = fbc.getLandmarks(detector, predictor, src_face_img)
        dest_points = fbc.getLandmarks(detector, predictor, dest_face_img)
        return src_points, dest_points

    def get_convex_hull(self, src_landmark_points, dest_landmark_points, points_slice=None):
        # 2. Find convex hull
        hull_index = cv2.convexHull(np.array(dest_landmark_points), returnPoints=False)

        # Create convex hull lists
        src_hull = []
        dest_hull = []

        if points_slice:
            src_hull = src_landmark_points[points_slice]
            dest_hull = dest_landmark_points[points_slice]
        else:
            for i in range(0, len(hull_index)):
                src_hull.append(src_landmark_points[hull_index[i][0]])
                dest_hull.append(dest_landmark_points[hull_index[i][0]])

        # Calculate Mask for Seamless cloning
        hull8U = []
        for i in range(0, len(dest_hull)):
            hull8U.append((dest_hull[i][0], dest_hull[i][1]))

        return (src_hull, dest_hull, hull8U)

    def calculate_delaunay_triangles(self, src_face_img, dest_face_img, src_hull, dest_hull):
        # 3. Find Delaunay triangulation for convex hull points
        dest_img_size = dest_face_img.shape
        dest_rect = (0, 0, dest_img_size[1], dest_img_size[0])
        dest_dt = fbc.calculateDelaunayTriangles(dest_rect, dest_hull)

        # If no Delaunay Triangles were found, quit
        if len(dest_dt) == 0:
            quit()

        src_triangles = []
        dest_triangles = []
        for i in range(0, len(dest_dt)):
            src_tri = []
            dest_tri = []
            for j in range(0, 3):
                src_tri.append(src_hull[dest_dt[i][j]])
                dest_tri.append(dest_hull[dest_dt[i][j]])

            src_triangles.append(src_tri)
            dest_triangles.append(dest_tri)

        dest_img_warped = np.copy(dest_face_img)
        # Simple Alpha Blending
        # Apply affine transformation to Delaunay triangles
        for i in range(0, len(src_triangles)):
            fbc.warpTriangle(src_face_img, dest_img_warped, src_triangles[i], dest_triangles[i])

        return dest_img_warped

    def do_seamless_clone(self, dest_face_img, dest_img_warped, hull8U):
        # 4. Clone seamlessly.
        dest_mask = np.zeros(dest_face_img.shape, dtype=dest_face_img.dtype)
        cv2.fillConvexPoly(dest_mask, np.int32(hull8U), (255, 255, 255))

        # Find Centroid
        m = cv2.moments(dest_mask[:, :, 1])
        center = (int(m["m10"] / m["m00"]), int(m["m01"] / m["m00"]))

        output = cv2.seamlessClone(np.uint8(dest_img_warped), dest_face_img, dest_mask, center, cv2.NORMAL_CLONE)
        return output[:, :, ::-1]

    def faceSwap(self, src_face_img, dest_face_img, points_slice=None):
        if self.hasValidHumanFace(src_face_img) and self.hasValidHumanFace(dest_face_img):
            src_points, dest_points = self.detect_landmarks(src_face_img, dest_face_img)
            src_hull, dest_hull, hull8U = self.get_convex_hull(src_points, dest_points, points_slice)
            dest_img_warped = self.calculate_delaunay_triangles(src_face_img, dest_face_img, src_hull, dest_hull)
            transformed_img = self.do_seamless_clone(dest_face_img, dest_img_warped, hull8U)
            return transformed_img
        else:
            raise Exception("No human face detected in the image")

    def faceMask(self, src_face_img, dest_face_img):
        return self.faceSwap(src_face_img, dest_face_img, slice(1, 16, None))
