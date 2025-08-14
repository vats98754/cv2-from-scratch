import numpy as np
from typing import Tuple
from find_homography import solve_homography_dlt, is_degenerate_sample, reprojection_errors


def ransac_homography(src_pts: np.ndarray, dst_pts: np.ndarray,
                      thresh: float = 3.0,
                      max_iters: int = 2000,
                      confidence: float = 0.99,
                      verbose: bool = False) -> Tuple[np.ndarray, np.ndarray]:
    """
    Robust homography estimation via RANSAC.
    Returns best_H, inlier_mask (boolean array of length N).
    thresh: reprojection error threshold in pixels.
    """
    src = np.asarray(src_pts, dtype=np.float64)
    dst = np.asarray(dst_pts, dtype=np.float64)
    N = src.shape[0]
    if N < 4:
        raise ValueError("Need at least 4 points for RANSAC")

    best_H = None
    best_inliers = np.zeros(N, dtype=bool)
    best_count = 0
    it = 0
    # initial required iterations (p = confidence)
    required_iters = max_iters

    while it < required_iters and it < max_iters:
        # random sample
        idx = np.random.choice(N, 4, replace=False)
        s_src = src[idx]
        s_dst = dst[idx]

        # skip degenerate samples
        if is_degenerate_sample(s_src) or is_degenerate_sample(s_dst):
            it += 1
            continue

        try:
            H_candidate = solve_homography_dlt(s_src, s_dst, normalize=True)
        except np.linalg.LinAlgError:
            it += 1
            continue

        errs = reprojection_errors(H_candidate, src, dst)
        inliers_mask = errs < thresh
        count = int(np.sum(inliers_mask))

        if count > best_count:
            best_count = count
            best_H = H_candidate
            best_inliers = inliers_mask

            # update required iterations (adaptive)
            w = best_count / float(N)  # inlier ratio
            # avoid log(0) and pow saturation
            eps = 1e-9
            nom = np.log(1 - confidence + eps)
            denom = np.log(max(1e-9, 1 - (w**4)))
            if denom != 0:
                required_iters = int(min(max_iters, np.ceil(nom / denom)))
            else:
                required_iters = 1

            if verbose:
                print(f"[RANSAC] it={it}, best_count={best_count}, new required_iters={required_iters}")

        it += 1

    # final refinement: re-estimate H using all inliers if we have enough
    if best_count >= 4:
        inlier_src = src[best_inliers]
        inlier_dst = dst[best_inliers]
        H_refined = solve_homography_dlt(inlier_src, inlier_dst, normalize=True)
        return H_refined, best_inliers
    else:
        # fallback: return best candidate without refinement
        return best_H, best_inliers
