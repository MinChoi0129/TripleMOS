import numpy as np
import random
import cv2
from scipy.spatial import Delaunay


def parse_calibration(filename):
    """read calibration file with given filename
    Returns
    -------
    dict
        Calibration matrices as 4x4 numpy arrays.
    """
    calib = {}
    calib_file = open(filename, "r")
    for line in calib_file:
        key, content = line.strip().split(":")
        values = [float(v) for v in content.strip().split()]

        pose = np.zeros((4, 4))
        pose[0, 0:4] = values[0:4]
        pose[1, 0:4] = values[4:8]
        pose[2, 0:4] = values[8:12]
        pose[3, 3] = 1.0
        calib[key] = pose
    calib_file.close()
    return calib


def parse_poses(filename, calibration):
    """read poses file with per-scan poses from given filename
    Returns
    -------
    list
        list of poses as 4x4 numpy arrays.
    """
    file = open(filename, "r")
    poses = []
    Tr = calibration["Tr"]
    Tr_inv = np.linalg.inv(Tr)

    for line in file:
        values = [float(v) for v in line.strip().split()]
        pose = np.zeros((4, 4))
        pose[0, 0:4] = values[0:4]
        pose[1, 0:4] = values[4:8]
        pose[2, 0:4] = values[8:12]
        pose[3, 3] = 1.0
        poses.append(np.matmul(Tr_inv, np.matmul(pose, Tr)))
    return poses


def in_hull(p, hull):
    if not isinstance(hull, Delaunay):
        hull = Delaunay(hull)
    return hull.find_simplex(p) >= 0


def compute_box_3d(center, size, yaw):
    c = np.cos(yaw)
    s = np.sin(yaw)
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

    # 3d bounding box dimensions
    l = size[0]
    w = size[1]
    h = size[2]

    # 3d bounding box corners
    x_corners = [l / 2, l / 2, -l / 2, -l / 2, l / 2, l / 2, -l / 2, -l / 2]
    y_corners = [w / 2, -w / 2, -w / 2, w / 2, w / 2, -w / 2, -w / 2, w / 2]
    z_corners = [h / 2, h / 2, h / 2, h / 2, -h / 2, -h / 2, -h / 2, -h / 2]
    # rotate and translate 3d bounding box
    corners_3d = np.dot(R, np.vstack([x_corners, y_corners, z_corners]))

    corners_3d[0, :] = corners_3d[0, :] + center[0]
    corners_3d[1, :] = corners_3d[1, :] + center[1]
    corners_3d[2, :] = corners_3d[2, :] + center[2]
    return corners_3d.T


def random_float(v_range):
    v = random.random()
    v = v * (v_range[1] - v_range[0]) + v_range[0]
    return v


def in_range(v, r):
    return (v >= r[0]) * (v < r[1])


def filter_pcds(pcds, range_x=(-40, 60), range_y=(-40, 40), range_z=(-3, 5)):
    valid_x = (pcds[:, 0] >= range_x[0]) * (pcds[:, 0] < range_x[1])
    valid_y = (pcds[:, 1] >= range_y[0]) * (pcds[:, 1] < range_y[1])
    valid_z = (pcds[:, 2] >= range_z[0]) * (pcds[:, 2] < range_z[1])

    pcds_filter = pcds[valid_x * valid_y * valid_z]
    return pcds_filter


def filter_pcds_mask(pcds, range_x=(-40, 60), range_y=(-40, 40), range_z=(-3, 5)):
    valid_x = (pcds[:, 0] >= range_x[0]) * (pcds[:, 0] < range_x[1])
    valid_y = (pcds[:, 1] >= range_y[0]) * (pcds[:, 1] < range_y[1])
    valid_z = (pcds[:, 2] >= range_z[0]) * (pcds[:, 2] < range_z[1])

    valid_mask = valid_x * valid_y * valid_z
    return valid_mask


def Trans(pcds, mat):
    pcds_out = pcds.copy()

    pcds_tmp = pcds_out[:, :4].T
    pcds_tmp[-1] = 1
    pcds_tmp = mat.dot(pcds_tmp)
    pcds_tmp = pcds_tmp.T

    pcds_out[..., :3] = pcds_tmp[..., :3]
    pcds_out[..., 3:] = pcds[..., 3:]
    return pcds_out


def relabel(pcds_labels, label_map):
    result_labels = np.zeros((pcds_labels.shape[0],), dtype=pcds_labels.dtype)
    for key in label_map:
        value = label_map[key]
        mask = pcds_labels == key
        result_labels[mask] = value

    return result_labels


def recolor(pcds_labels, color_map):
    result_color = np.zeros((pcds_labels.shape[0], 3), dtype=np.uint8)
    for key in color_map:
        value = color_map[key]
        mask = pcds_labels == key
        result_color[mask, 0] = value[0]
        result_color[mask, 1] = value[1]
        result_color[mask, 2] = value[2]

    return result_color


##############################################################################################


def Quantize(pcds, range_x, range_y, range_z, size):
    x = pcds[:, 0].copy()
    y = pcds[:, 1].copy()
    z = pcds[:, 2].copy()

    size_x = size[0]
    size_y = size[1]
    size_z = size[2]

    dx = (range_x[1] - range_x[0]) / size_x
    dy = (range_y[1] - range_y[0]) / size_y
    dz = (range_z[1] - range_z[0]) / size_z

    x_quan = (x - range_x[0]) / dx
    y_quan = (y - range_y[0]) / dy
    z_quan = (z - range_z[0]) / dz

    pcds_quan = np.stack((x_quan, y_quan, z_quan), axis=-1)
    return pcds_quan


def SphereQuantize(pcds, phi_range, theta_range, r_range, size):
    H, W, R = size

    phi_rad_min = phi_range[0] * np.pi / 180.0
    phi_rad_max = phi_range[1] * np.pi / 180.0
    theta_rad_min = theta_range[0] * np.pi / 180.0
    theta_rad_max = theta_range[1] * np.pi / 180.0

    dphi = (phi_rad_max - phi_rad_min) / W
    dtheta = (theta_rad_max - theta_rad_min) / H
    dr = (r_range[1] - r_range[0]) / R

    x, y, z = pcds[:, 0], pcds[:, 1], pcds[:, 2]
    d = np.sqrt(x**2 + y**2 + z**2) + 1e-12  # 반경

    phi = phi_rad_max - np.arctan2(x, y)
    phi_quan = phi / dphi

    theta = theta_rad_max - np.arcsin(z / d)
    theta_quan = theta / dtheta

    r_quan = (d - r_range[0]) / dr

    sphere_coords = np.stack((theta_quan, phi_quan, r_quan), axis=-1)
    return sphere_coords


def CylinderQuantize(pcds, phi_range, z_range, r_range, size):
    H, W, R = size

    phi_rad_min = phi_range[0] * np.pi / 180.0
    phi_rad_max = phi_range[1] * np.pi / 180.0

    dphi = (phi_rad_max - phi_rad_min) / W
    dz = (z_range[1] - z_range[0]) / H
    dr = (r_range[1] - r_range[0]) / R

    x, y, z = pcds[:, 0], pcds[:, 1], pcds[:, 2]
    r = np.sqrt(x**2 + y**2) + 1e-12  # 반경 (xy 평면에서의 거리)

    phi = phi_rad_max - np.arctan2(x, y)
    phi_quan = phi / dphi

    z_quan = (z - z_range[0]) / dz
    r_quan = (r - r_range[0]) / dr

    cylinder_coords = np.stack((z_quan, phi_quan, r_quan), axis=-1)
    return cylinder_coords


def PolarQuantize(pcds, phi_range, r_range, size):
    H, W, Z = size

    phi_rad_min = phi_range[0] * np.pi / 180.0
    phi_rad_max = phi_range[1] * np.pi / 180.0

    dphi = (phi_rad_max - phi_rad_min) / W
    dr = (r_range[1] - r_range[0]) / H
    dz = (pcds[:, 2].max() - pcds[:, 2].min()) / Z

    x, y, z = pcds[:, 0], pcds[:, 1], pcds[:, 2]
    r = np.sqrt(x**2 + y**2) + 1e-12  # 반경

    phi = phi_rad_max - np.arctan2(x, y)
    phi_quan = phi / dphi

    r_quan = (r - r_range[0]) / dr
    z_quan = (z - pcds[:, 2].min()) / dz

    polar_coords = np.stack((r_quan, phi_quan, z_quan), axis=-1)
    return polar_coords


class DataAugment:
    def __init__(
        self,
        noise_mean=0,
        noise_std=0.01,
        theta_range=(-45, 45),
        shift_range=(0, 0),
        size_range=(0.95, 1.05),
    ):
        self.noise_mean = noise_mean
        self.noise_std = noise_std
        self.theta_range = theta_range
        self.shift_range = shift_range
        self.size_range = size_range
        assert len(self.shift_range) == 3

    def __call__(self, pcds):
        """Inputs:
         pcds: (N, C) N demotes the number of point clouds; C contains (x, y, z, i, ...)
        Output:
         pcds: (N, C)
        """
        # random noise
        xyz_noise = np.random.normal(self.noise_mean, self.noise_std, size=(pcds.shape[0], 3))
        pcds[:, :3] = pcds[:, :3] + xyz_noise

        # random shift
        shift_xyz = [random_float(self.shift_range[i]) for i in range(3)]
        pcds[:, 0] = pcds[:, 0] + shift_xyz[0]
        pcds[:, 1] = pcds[:, 1] + shift_xyz[1]
        pcds[:, 2] = pcds[:, 2] + shift_xyz[2]

        # random scale
        scale = random_float(self.size_range)
        pcds[:, :3] = pcds[:, :3] * scale

        # random flip on xy plane
        h_flip = 0
        v_flip = 0
        if random.random() < 0.5:
            h_flip = 1
        else:
            h_flip = 0

        if random.random() < 0.5:
            v_flip = 1
        else:
            v_flip = 0

        if v_flip == 1:
            pcds[:, 0] = pcds[:, 0] * -1

        if h_flip == 1:
            pcds[:, 1] = pcds[:, 1] * -1

        # random rotate on xy plane
        theta_z = random_float(self.theta_range)
        rotateMatrix = cv2.getRotationMatrix2D((0, 0), theta_z, 1.0)[:, :2].T
        pcds[:, :2] = pcds[:, :2].dot(rotateMatrix)
        return pcds
