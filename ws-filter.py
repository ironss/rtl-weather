import math
import time


class Exponential_smoothing_1:
    def __init__(self, alpha=None, tau=None, values=[]):
        if alpha is not None:
            self.alpha = alpha
            self.tau = -1 / math.log(1-alpha)
        elif tau is not None:
            self.tau = tau
            self.alpha = 1-math.exp(-1/tau)
        else:
            raise ValueError

        self.value = None
        self.filtered = None

        for v in values:
            self.update(v)

    def update(self, value):
        self.value = value

        if self.filtered is None:
            self.filtered = value
        else:
            self.filtered = (1 - self.alpha) * self.filtered + self.alpha * value

        return self.filtered, None


class Circular_filter:
    def __init__(self, filter_type, args):
        self.filter_x = filter_type(*args)
        self.filter_y = filter_type(*args)
        self.filtered = None

    def update(self, v):
        x = math.cos(v)
        y = math.sin(v)
        xf, _ = self.filter_x.update(x)
        yf, _ = self.filter_y.update(y)
        self.filtered = math.atan2(yf, xf)

        return self.filtered, None


class Rain_record:
    def __init__(self, duration_s):
        self.duration_s = duration_s
        self.records = []

    def update(self, ts, rain_mm):
        self.records.append((ts, rain_mm))
        ts_first = ts - self.duration_s

        self.records = [ r for r in self.records if r[0] >= ts_first ]
        return rain_mm - self.records[0][1]

if __name__ == '__main__':
    import sys
    import json
    import math

    verbosity = 0
    print_output = 1

    wind_dir1 = Circular_filter(Exponential_smoothing_1, (0.05, ))
    wind1 = Exponential_smoothing_1(0.05)
    wind2 = Exponential_smoothing_1(0.05)
    rain_1h = Rain_record(3600)
    rain_24 = Rain_record(86400)

    for l in sys.stdin:
        j = json.loads(l)
        if verbosity >= 2:
            print(j, file=sys.stderr)


        # Wind direction smoothing
        try:
            wind_dir_deg = j['wind_dir_deg']
        except KeyError:
            wind_dir_deg = None

        if wind_dir_deg is not None:
            wind_dir_smooth1_deg = math.degrees(wind_dir1.update(math.radians(wind_dir_deg))[0]) % 360
            j['wind_dir_smooth_deg'] = round(wind_dir_smooth1_deg)
            if verbosity >= 1:
                print('Wind dir: {}, {}'.format(wind_dir_deg, wind_dir_smooth1_deg), file=sys.stdout)


        # Wind speed smoothing
        try:
            wind_avg_kmh = j['wind_avg_km_h']
        except KeyError:
           wind_avg_kmh = None

        if wind_avg_kmh is not None:
            wind_avg_smooth_kmh = wind1.update(wind_avg_kmh)[0]
            j['wind_avg_smooth_km_h'] = round(wind_avg_smooth_kmh, 1)
            if verbosity >= 1:
                print('Wind avg: {}, {}'.format(wind_avg_kmh, wind_avg_smooth_kmh))


        try:
            wind_max_kmh = j['wind_max_km_h']
        except KeyError:
            wind_max_kmh = None

        if wind_max_kmh is not None:
            wind_max_smooth_kmh = wind2.update(wind_max_kmh)[0]
            j['wind_max_smooth_km_h'] = wind_max_smooth_kmh
            if verbosity >= 1:
                print('Wind max: {}, {}'.format(wind_avg_kmh, wind_avg_smooth_kmh))


        # Rain calculations
        try:
            ts = int(j['time'])
            rain_mm = j['rain_mm']
        except KeyError:
            ts = None

        if ts is not None:
            rain_1h_mm  = rain_1h.update(ts, rain_mm)
            rain_24h_mm = rain_24.update(ts, rain_mm)
            j['rain_1h_mm'] = round(rain_1h_mm, 1)
            j['rain_24h_mm'] = round(rain_24h_mm, 1)
            if verbosity >= 1:
                print('Rain: {}, {}, {}'.format(rain_mm, rain_1h_mm, rain_24h_mm))


        if print_output:
            print(json.dumps(j), flush=True)
