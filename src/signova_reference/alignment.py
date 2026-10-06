"""One temporal alignment per complete reference, shared by every joint."""
import numpy as np


def align(user, reference, tolerance, required, mode="linear", band_fraction=0.2):
    if mode == "linear":
        indexes = np.arange(len(user))
        return indexes, indexes
    if mode != "dtw" or not np.isfinite(band_fraction) or not 0 <= band_fraction <= 1:
        raise ValueError("Unsupported alignment/band")
    # Bounded broadcast cost; each cell compares all required joints together.
    distance = np.linalg.norm(user[:, None, required] - reference[None, :, required], axis=-1)
    ratios = distance / tolerance[None, :, required]
    cost = np.where(np.isfinite(ratios), np.minimum(ratios, 5), 5).mean(axis=-1)
    size = len(user)
    band = int(np.ceil(size * band_fraction))
    dp = np.full((size + 1, size + 1), np.inf)
    parent = np.full((size, size), -1, dtype=np.int8)
    dp[0, 0] = 0
    for i in range(size):
        for j in range(max(0, i - band), min(size, i + band + 1)):
            choices = (dp[i, j], dp[i, j + 1], dp[i + 1, j])
            which = int(np.argmin(choices))
            dp[i + 1, j + 1] = cost[i, j] + choices[which]
            parent[i, j] = which
    i = j = size - 1
    pairs = []
    while i >= 0 and j >= 0:
        pairs.append((i, j))
        which = parent[i, j]
        if which == 0:
            i -= 1
            j -= 1
        elif which == 1:
            i -= 1
        elif which == 2:
            j -= 1
        else:
            raise ValueError("No valid alignment")
    if i != -1 or j != -1:
        raise ValueError("Incomplete alignment")
    return tuple(np.array(values, dtype=int) for values in zip(*pairs[::-1]))
