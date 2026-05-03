import json
import numpy as np
from scipy.interpolate import make_interp_spline, interp1d
import matplotlib.pyplot as plt
import argparse

__INNER_VERSION__ = 'Alpha_0.0.1_202605'
print(f"MathLine Transform Module - Version: {__INNER_VERSION__}")

X_cache = np.array([])
Y_cache = np.array([])
Line_cache = []

def _to_bool(a):
    if a.lower() in ['true', '1', 't', 'y', 'yes']:
        return True
    elif a.lower() in ['false', '0', 'f', 'n', 'no']:
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def read_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def clip(a:list,b):
    return np.clip(b,a[1],a[0])

def get_smooth(a:np.ndarray,b:np.ndarray):
    x_smooth = np.linspace(a.min(), a.max(), 300)
    if len(a) == 1:
        return a, b
    elif len(a) == 2:
        spl = interp1d(a, b, kind='quadratic', fill_value="extrapolate")
    elif len(a) == 3:
        spl = interp1d(a, b, kind='cubic', fill_value="extrapolate")
    else:
        spl = make_interp_spline(a, b, k=3)
        y_smooth = spl(x_smooth)
    return x_smooth,y_smooth

def fill_line(y:np.ndarray,line_fill=0):
    return np.nan_to_num(y, nan=line_fill)

def merge_two_curve_keep_original(x1, y1, x2, y2, num_full=1000):
    """
    合并两条定义域不重合曲线，原点位不变，中间断开保留 NaN
    :param x1,y1: 曲线1坐标
    :param x2,y2: 曲线2坐标
    :param num_full: 全局完整x轴采样点数
    :return: x_full, y_merge 合并后完整曲线，空隙为NaN
    """
    # 全局x范围
    x_min = min(np.min(x1), np.min(x2))
    x_max = max(np.max(x1), np.max(x2))
    
    # 生成完整全局x轴
    x_full = np.linspace(x_min, x_max, num_full)
    # 初始全部填 NaN
    y_merge = np.full_like(x_full, np.nan)
    
    # 把曲线1原样映射回填
    for xi, yi in zip(x1, y1):
        idx = np.argmin(np.abs(x_full - xi))
        y_merge[idx] = yi
    
    # 把曲线2原样映射回填
    for xi, yi in zip(x2, y2):
        idx = np.argmin(np.abs(x_full - xi))
        y_merge[idx] = yi

    return x_full, y_merge
def merge_multi_curve_keep_original(x_list, y_list, num_full=1000):
    ret_cache = []
    if len(x_list) == 1:
        return x_list[0], y_list[0]
    for i in range(len(x_list)):
        if i == 0:
            x_full, y_merge = merge_two_curve_keep_original(x_list[0], y_list[0], x_list[1], y_list[1], num_full=num_full)
            ret_cache.append((x_full, y_merge))
        else:
            x_full, y_merge = merge_two_curve_keep_original(ret_cache[-1][0], ret_cache[-1][1], x_list[i], y_list[i], num_full=num_full)
            ret_cache = [(x_full, y_merge)]
    return ret_cache[0][0], ret_cache[0][1]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Transform JSON data to numpy array')
    parser.add_argument('--json_file','-j' ,type=str, required=True, help='Path to the input JSON file')
    parser.add_argument('--output_file','-o',type=str, required=False, default='output.npz', help='Path to the output numpy array file')
    parser.add_argument('--show', '-s', type=str, required=False, default=False, help='Show the result')
    parser.add_argument('--version', '-v', action='version', version=f'Version: {__INNER_VERSION__}')
    args = parser.parse_args()
    data = read_json(args.json_file)
    for dot in data["Line"]:
        if dot[2] < 0:
            if_conn = False
        else:
            if_conn = True
        dot_x = dot[0]
        dot_y = dot[1]
        X_cache = np.append(X_cache, dot_x)
        Y_cache = np.append(Y_cache, dot_y)
        if if_conn:
            pass
        else:
            Line_ = get_smooth(X_cache, Y_cache)
            Line_cache.append(Line_)
            X_cache = np.array([])
            Y_cache = np.array([])
    if len(X_cache) > 0:
        Line_ = get_smooth(X_cache, Y_cache)
        Line_cache.append(Line_)
    ret_X, ret_Y = merge_multi_curve_keep_original([line[0] for line in Line_cache],
                                                   [line[1] for line in Line_cache], 
                                                   num_full=1000)

    if args.show:
        plt.figure(figsize=(10,5))
        plt.plot(ret_X, ret_Y, linewidth=2)
        plt.grid(True)
        plt.title("Merged Curve")
        plt.show()
    np.savez(args.output_file, X=ret_X, Y=ret_Y)