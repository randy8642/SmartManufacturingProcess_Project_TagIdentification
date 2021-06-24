import json
import numpy as np
from numpy.lib.shape_base import expand_dims


locationPoints = json.load(open('./data/location.json', mode='r'))['locationPoint']


def getlocation(x_pixel: int):
    global locationPoints

    if x_pixel > locationPoints[0][1]:
        return -1
    if x_pixel < locationPoints[-1][1]:
        return -1

    upperIndex, lowerIndex = -1, -1
    for n in range(len(locationPoints)):
        if locationPoints[n][1] == x_pixel:
            return locationPoints[n][0]

        if locationPoints[n][1] > x_pixel:
            upperIndex = n

        if locationPoints[n][1] < x_pixel:
            lowerIndex = n
            break

    # 內插
    upperReal, upperPixel = locationPoints[upperIndex]
    lowerReal, lowerPixel = locationPoints[lowerIndex]
    # print(locationPoints[upperIndex])
    # print(locationPoints[lowerIndex])

    return lowerReal + (x_pixel - lowerPixel)/(upperPixel - lowerPixel) * (upperReal - lowerReal)


def get_distance(x1, x2):
    return np.abs(x1-x2)


def get_index(pre_result: np.ndarray, new_xs):
    THRESHOLD = 20

    result = pre_result

    if pre_result.shape[0] > 0:
        for loc, *box in new_xs:
            
            dis = [get_distance(loc, pre) for pre,*_ in pre_result]
            min_index = np.argmin(dis)

            if dis[min_index] < THRESHOLD:
                # UPDATE
                result[min_index, :] = loc, *box
            else:
                # NEW
                if loc < 50:                
                    result = np.concatenate((result, np.expand_dims([loc, *box], axis=0)), axis=0)

    else:
        for loc, *box in new_xs:
            if loc < 50: 
                result = np.concatenate((result, np.expand_dims([loc, *box], axis=0)), axis=0)
    
    locations = np.array(result)[:, 0]
    sort_index = np.argsort(locations)[::-1]
    result = result[sort_index]

    return result

