import os
import cv2
import numpy as np

def analyze_multiview_image(image_path, debug_dir="/Users/workspace/ai_short_company/ai-short-drama/debug_multiview"):
    os.makedirs(debug_dir, exist_ok=True)
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        raise ValueError(f"Cannot load image: {image_path}")
    
    h, w, c = img_bgr.shape
    print(f"[MultiView] Loaded image: {w}x{h}")

    # Step 1: Estimate background color from corners and top banner
    corners = np.concatenate([
        img_bgr[0:15, 0:15].reshape(-1, 3),
        img_bgr[0:15, -15:].reshape(-1, 3),
        img_bgr[0:15, w//2-10:w//2+10].reshape(-1, 3)
    ], axis=0)
    bg_color = np.median(corners, axis=0)
    print(f"[MultiView] Estimated Background BGR: {bg_color.tolist()}")

    # Compute color distance from background
    diff = np.linalg.norm(img_bgr.astype(np.float32) - bg_color.astype(np.float32), axis=2)
    # Mask of foreground
    fg_mask = (diff > 18.0).astype(np.uint8) * 255

    # Morphology to close small holes in clothing
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)

    cv2.imwrite(os.path.join(debug_dir, "01_fg_mask.png"), fg_mask)

    # Step 2: Vertical projection (density along X axis)
    col_density = np.sum(fg_mask > 0, axis=0).astype(np.float32)
    
    # Smooth the curve
    window_size = max(5, int(w * 0.03))
    if window_size % 2 == 0:
        window_size += 1
    smoothed = np.convolve(col_density, np.ones(window_size)/window_size, mode='same')
    
    # Normalize density
    max_dens = np.max(smoothed)
    if max_dens == 0:
        print("[MultiView] Empty image, treating as N=1")
        return [(0, w)]
    
    norm_dens = smoothed / max_dens

    # Step 3: Find peaks and valleys
    peak_thresh = 0.35
    peaks = []
    min_peak_dist = int(w * 0.18) # Minimum distance between distinct subjects

    for x in range(1, w - 1):
        if norm_dens[x] > peak_thresh:
            if norm_dens[x] >= norm_dens[x-1] and norm_dens[x] >= norm_dens[x+1]:
                if not peaks or (x - peaks[-1]) >= min_peak_dist:
                    peaks.append(x)
                elif norm_dens[x] > norm_dens[peaks[-1]]:
                    peaks[-1] = x

    print(f"[MultiView] Detected Peaks at X: {peaks}")
    N = len(peaks)
    print(f"[MultiView] Detected N = {N}")

    if N <= 1:
        print("[MultiView] Single subject detected.")
        return [(0, w)]

    # Find valleys between consecutive peaks
    cut_points = []
    for i in range(len(peaks) - 1):
        p1 = peaks[i]
        p2 = peaks[i+1]
        valley_x = p1 + np.argmin(norm_dens[p1:p2])
        cut_points.append(valley_x)
        print(f"[MultiView] Valley between Peak {i} & {i+1} at X={valley_x} (density={norm_dens[valley_x]:.2f})")

    intervals = []
    for i in range(N):
        x_start = 0 if i == 0 else cut_points[i-1]
        x_end = w if i == N - 1 else cut_points[i]
        intervals.append((x_start, x_end))
        print(f"[MultiView] Interval {i}: [{x_start}, {x_end}]")

    return intervals

if __name__ == "__main__":
    test_img = "/Users/workspace/ai_short_company/ai-short-drama/test_multiview_input.png"
    intervals = analyze_multiview_image(test_img)
