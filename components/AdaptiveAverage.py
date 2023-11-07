import numpy as np

def adaptive_average(waveR, phase_threshold=0.5, n_avg=8):
    """
    Compute the adaptive average of the input data.

    Args:
        waveR (array-like): The input data representing BPM phase error.
        phase_threshold (float, optional): The phase change threshold to disable averaging. Default is 0.5.
        n_avg (int, optional): The number of points to average over. Default is 8.

    Returns:
        waveA (ndarray): The adaptive average of the input data.
    """
    # Check if the input data is a numpy array
    if not isinstance(waveR, np.ndarray):
        waveR = np.array(waveR)

    if len(waveR) < 2:
        return np.array([])

    recentPts = [waveR[0]]
    waveA = np.zeros(len(waveR))

    for n in range(1, len(waveR)):
        newPts = np.append(recentPts, waveR[n])

        if len(newPts) > n_avg:
            newPts = newPts[1:(n_avg + 1)]

        waveA[n] = np.mean(newPts)

        if abs(waveR[n] - waveA[n - 1]) > phase_threshold:
            waveA[n] = waveR[n]
            recentPts = [waveR[n]]
        else:
            recentPts = newPts

    return waveA
