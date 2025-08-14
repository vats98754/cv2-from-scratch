import numpy as np
from typing import Tuple

def to_homogeneous(pts: np.ndarray) -> np.ndarray:
    """
    Convert Nx2 points to Nx3 homogeneous coordinates.
    """
    pts = np.asarray(pts, dtype=np.float64)
    if pts.ndim != 2 or pts.shape[1] != 2:
        raise ValueError("pts must be Nx2")
    ones = np.ones((pts.shape[0], 1), dtype=np.float64)
    return np.hstack([pts, ones])


def from_homogeneous(pts_h: np.ndarray) -> np.ndarray:
    """
    Convert Nx3 homogeneous to Nx2 Cartesian (divide by last coordinate).
    """
    pts_h = np.asarray(pts_h, dtype=np.float64)
    if pts_h.ndim != 2 or pts_h.shape[1] != 3:
        raise ValueError("pts_h must be Nx3")
    denom = pts_h[:, 2:3]
    # avoid division by zero
    denom[denom == 0] = 1e-12
    return pts_h[:, :2] / denom


def normalize_points(pts: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute similarity transform T and normalized points.
    T is a 3x3 matrix applied on homogeneous coords: x_norm = T @ x
    The output points are Nx2 Cartesian normalized coordinates.
    """
    pts = np.asarray(pts, dtype=np.float64)
    if pts.ndim != 2 or pts.shape[1] != 2:
        raise ValueError("pts must be Nx2")

    mean = pts.mean(axis=0)
    pts_centered = pts - mean
    avg_dist = np.mean(np.sqrt(np.sum(pts_centered**2, axis=1)))
    if avg_dist == 0:
        scale = 1.0
    else:
        scale = np.sqrt(2) / avg_dist

    T = np.array([
        [scale, 0, -scale * mean[0]],
        [0, scale, -scale * mean[1]],
        [0, 0, 1.0]
    ], dtype=np.float64)

    pts_h = to_homogeneous(pts)
    pts_norm_h = (T @ pts_h.T).T
    pts_norm = from_homogeneous(pts_norm_h)
    return T, pts_norm


def construct_A(src_pts: np.ndarray, dst_pts: np.ndarray) -> np.ndarray:
    """
    Build the 2N x 9 matrix A for DLT from Nx2 src and dst points (cartesian).
    """
    src = np.asarray(src_pts, dtype=np.float64)
    dst = np.asarray(dst_pts, dtype=np.float64)
    if src.shape != dst.shape or src.ndim != 2 or src.shape[1] != 2:
        raise ValueError("src and dst must be Nx2 and same shape")

    N = src.shape[0]
    A = np.zeros((2 * N, 9), dtype=np.float64)
    for i in range(N):
        x, y = src[i]
        u, v = dst[i]
        A[2*i]   = [-x, -y, -1,  0,  0,  0, u*x, u*y, u]
        A[2*i+1] = [ 0,  0,  0, -x, -y, -1, v*x, v*y, v]
    return A


def solve_homography_dlt(src_pts: np.ndarray, dst_pts: np.ndarray,
                         normalize: bool = True) -> np.ndarray:
    """
    Compute homography H (3x3) that maps src_pts -> dst_pts using DLT.
    If normalize=True, points are normalized (recommended).
    Returns H with H[2,2] == 1 (if possible).
    """
    src = np.asarray(src_pts, dtype=np.float64)
    dst = np.asarray(dst_pts, dtype=np.float64)
    if src.shape[0] < 4:
        raise ValueError("At least 4 correspondences required")

    if normalize:
        T_src, src_n = normalize_points(src)
        T_dst, dst_n = normalize_points(dst)
    else:
        T_src = np.eye(3, dtype=np.float64)
        T_dst = np.eye(3, dtype=np.float64)
        src_n = src
        dst_n = dst

    A = construct_A(src_n, dst_n)
    # SVD solution of Ah=0
    U, S, Vt = np.linalg.svd(A)
    h = Vt[-1, :]  # last row of V^T
    Hn = h.reshape(3, 3)

    # Denormalize
    H = np.linalg.inv(T_dst) @ Hn @ T_src
    # Normalize so H[2,2] == 1 (if close to zero, normalize by norm)
    if abs(H[2, 2]) > 1e-12:
        H = H / H[2, 2]
    else:
        H = H / np.linalg.norm(H)

    return H


def warp_points(H: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """
    Apply homography H to Nx2 points and return Nx2 warped points.
    """
    pts_h = to_homogeneous(pts)
    warped_h = (H @ pts_h.T).T
    return from_homogeneous(warped_h)


def reprojection_errors(H: np.ndarray, src_pts: np.ndarray, dst_pts: np.ndarray) -> np.ndarray:
    """
    Returns per-point Euclidean reprojection errors.
    """
    projected = warp_points(H, src_pts)
    dst = np.asarray(dst_pts, dtype=np.float64)
    errs = np.linalg.norm(projected - dst, axis=1)
    return errs


def is_degenerate_sample(src_sample: np.ndarray) -> bool:
    """
    Check degeneracy: if sample pts are collinear (rank < 3), it's degenerate.
    src_sample: 4x2 array
    """
    assert src_sample.shape[0] >= 3
    src_h = to_homogeneous(src_sample[:4])  # ensure at most 4
    rank = np.linalg.matrix_rank(src_h.T)
    return rank < 3
