import json
import numpy as np

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
    result = lowerReal + (x_pixel - lowerPixel)/(upperPixel - lowerPixel) * (upperReal - lowerReal)

    return result


def get_distance(x1, x2):
    return np.abs(x1-x2)


def get_index(pre_result: np.ndarray, new_xs):
    '''
    參數格式
    pre_result ： [[location, x, y, w, h], ...]
    new_xs ： [[location, x, y, w, h], ...]
    '''
    # 距離20cm內視為同物體的移動
    THRESHOLD = 20

    result = pre_result

    if pre_result.shape[0] > 0:
        for loc, *box in new_xs:
            # 計算直線距離
            dis = [get_distance(loc, pre) for pre, *_ in pre_result]
            # 尋找最小距離
            min_index = np.argmin(dis)

            if dis[min_index] < THRESHOLD:                
                # 發現新舊物體框之間的距離小於閥值，將更新最近的物體框
                result[min_index, :] = loc, *box
            else:
                # 新物體框附近未有以存在的物體框，因此當作是新的物體進入追蹤範圍
                # 物體在50cm(定義的開始位置)內才會新增
                if loc < 50:
                    result = np.concatenate(
                        (result, np.expand_dims([loc, *box], axis=0)), axis=0)
    # 若為第一個追蹤點，則直接加入
    else:
        for loc, *box in new_xs:
            # 物體在50cm(定義的開始位置)內才會新增
            if loc < 50:
                result = np.concatenate(
                    (result, np.expand_dims([loc, *box], axis=0)), axis=0)
    # 將物體框依照位置排序
    locations = np.array(result)[:, 0]
    sort_index = np.argsort(locations)[::-1]
    result = result[sort_index]

    return result
