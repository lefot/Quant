# -*- coding:utf8 -*-
import tushare as ts
import re
import numpy as np
from pandas import DataFrame
import matplotlib.pyplot as plt
import pandas as pd
import datetime
import talib as ta
import random
import pymysql


class data_collect2(object):
    code = ''
    date_seq = []
    open_list = []
    close_list = []
    high_list = []
    low_list = []
    vol_list = []
    amount_list = []
    tor_list = []
    vr_list = []
    ma5_list = []
    ma10_list = []
    ma20_list = []
    ma30_list = []
    ma60_list = []
    avg = []
    good_factor = 0.02
    bad_factor = 0.05
    cnt_bad_sell = 0
    cnt_good_buy = 0
    cnt_good_sell = 0
    cnt_risk = 0
    af = []
    fq = []
    process = []
    dd_list = []
    dd_list_show = []
    macd_list = []
    kdj_list = []
    bool_up = 0.00
    bool_mid = 0.00
    bool_dn = 0.00
    data_train = []
    data_target = []
    test_case = []

    def __init__(self, in_code,start_dt,end_dt):
        self.collectDATA(in_code,start_dt,end_dt)

    def collectDATA(self,in_code,start_dt,end_dt):
        # 建立数据库连接,剔除已入库的部分
        db = pymysql.connect(host='127.0.0.1', user='root', passwd='admin', db='stock', charset='utf8')
        cursor = db.cursor()
        try:
            sql_done_set = "SELECT * FROM stock_price_day_list a where stock_code = '%s' and state_dt >= '%s' and state_dt <= '%s' order by state_dt asc" % (in_code, start_dt,end_dt)
            cursor.execute(sql_done_set)
            done_set = cursor.fetchall()
            if len(done_set) == 0:
                raise Exception
            print('Mark3333')
            for i in range(len(done_set)):
                self.date_seq.append(done_set[i][0])
                self.open_list.append(float(done_set[i][2]))
                self.close_list.append(float(done_set[i][3]))
                self.high_list.append(float(done_set[i][4]))
                self.low_list.append(float(done_set[i][5]))
                self.vol_list.append(float(done_set[i][6]))
                self.amount_list.append(float(done_set[i][7]))
                self.tor_list.append(float(done_set[i][8]))
                self.vr_list.append(float(done_set[i][9]))
                self.ma5_list.append(float(done_set[i][10]))
                self.ma10_list.append(float(done_set[i][11]))
                self.ma20_list.append(float(done_set[i][12]))
                self.ma30_list.append(float(done_set[i][13]))
                self.ma60_list.append(float(done_set[i][14]))
        except Exception as excp:
            print(excp)
        db.close()

        if len(self.close_list) > 0:
            self.open_list = np.array(self.open_list)
            self.close_list = np.array(self.close_list)
            self.high_list = np.array(self.high_list)
            self.low_list = np.array(self.low_list)
            print('Mark4444')
            self.code = in_code
            period = min(20,len(self.close_list))
            self.avg = ta.MA(self.close_list, period)
            self.avg = np.array([x for x in self.avg if str(x) != 'nan'])
            self.good_buy = np.array([x * (1.00 - self.good_factor) for x in self.avg])
            self.good_sell = np.array([x * (1.00 + self.good_factor) for x in self.avg])
            self.bad_sell = np.array([x * (1.00 - self.bad_factor) for x in self.avg])
            self.cnt_risk = [0] * len(self.avg)
            self.cnt_good_sell = [0] * len(self.avg)
            self.cnt_good_buy = [0] * len(self.avg)
            self.cnt_bad_sell = [0] * len(self.avg)
            for a in range(len(self.avg)):
                self.cnt_bad_sell[a] = len([x for x in self.close_list[:a + period - 1] if x <= self.bad_sell[a]])
                self.cnt_good_sell[a] = len([x for x in self.close_list[:a + period - 1] if x >= self.good_sell[a]])
                self.cnt_good_buy[a] = len([x for x in self.close_list[:a + period - 1] if self.bad_sell[a] < x <= self.good_buy[a]])
                self.cnt_risk[a] = len([x for x in self.close[:a + period - 1] if x <= self.close_list[a + period - 1]])
            # ARFQ
            for b in range(len(self.avg)):
                af, fq, process = get_arfq(np.array(self.close_list[b:b + period]),np.array(self.close_list[b:b + period]), self.good_sell[b],self.bad_sell[b], self.good_buy[b])
                af2 = ((np.array(self.high_list[b:b + period]) - np.array(self.low_list[b:b + period])).sum()) / (period)
                self.af.append(af2)
                self.fq.append(fq)
                self.process.append(process)

        # #获取大单数据
        # for m in range(obv):
        #     dd_start_dt = time_index + datetime.timedelta(m)
        #     try:
        #         temp2 = ts.get_sina_dd(self.code,dd_start_dt)
        #         error = len(temp2)
        #     except Exception as exp:
        #         temp2 = []
        #         self.dd_list.append(0)
        #         self.dd_list_show.append([0, dd_start_dt])
        #     if len(temp2) > 0:
        #         list_dd_all = temp2.iloc[0:, [4,6]]
        #         df_buy = list_dd_all[0:][list_dd_all.type =='买盘']
        #         list_buy = np.array(df_buy.iloc[0:,[0]]).ravel()
        #         df_sell = list_dd_all[0:][list_dd_all.type =='卖盘']
        #         list_sell = np.array(df_sell.iloc[0:, [0]]).ravel()
        #         dd_resu = np.array(list_buy).sum() - np.array(list_sell).sum()
        #         self.dd_list.append(dd_resu)
        #         self.dd_list_show.append([dd_resu,dd_start_dt])


        # MACD
        macd_temp = list(ta.MACD(np.array([float(x) for x in self.close_list]), 10, 20, 5))
        self.macd_list = [x for x in macd_temp[2] if str(x) != 'nan']


        # KDJ
        data = []
        for c in range(len(self.close_list)):
            data.append([self.date_seq[c],self.open_list[c],self.close_list[c],self.high_list[c],self.low_list[c]])
        resu_kdj = kdj(data)
        self.kdj_list = [x[-1] for x in resu_kdj]

        # BOLL
        bool_up_list, bool_mid_list, bool_dn_list = ta.BBANDS(np.array([float(x) for x in self.close_list]), timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
        self.bool_up = [x for x in bool_up_list if str(x)!='nan']
        self.bool_mid = [x for x in bool_mid_list if str(x)!='nan']
        self.bool_dn = [x for x in bool_dn_list if str(x)!='nan']
        self.get_data_src()

    def refreshDATA(self,resu):
        randseed = random.random()*random.choice([-1,1])
        new_high = max(randseed*self.af[-1],(1-randseed)*self.af[-1])
        new_low = self.af[-1]-new_high
        #self.data_src.loc[self.data_src.index[-1]+1] = {'high': float(resu)+float(new_high), 'low': float(resu)-float(new_low), 'volume': 0.00, 'code': self.code}
        #print(self.data_src)
        #temp_day2 = self.data_src
        self.open_list = np.array(list(self.open_list).append(float(resu)))
        self.close_list = np.array(list(self.close_list).append(float(resu)))
        self.high_list = np.array(list(self.high_list).append(float(resu)+float(new_high)))
        self.low_list = np.array(list(self.low_list).append(float(resu)-float(new_low)))
        self.vol_list = np.array(list(self.vol_list).append(float(0.00)))
        period = 20
        self.avg = ta.MA(self.close_list,period)
        self.avg = [x for x in self.avg if str(x) != 'nan']
        self.good_buy = [x* (1.00 - self.good_factor) for x  in self.avg]
        self.good_sell = [x * (1.00 + self.good_factor) for x in self.avg]
        self.bad_sell = [x * (1.00 - self.bad_factor) for x in self.avg]
        self.cnt_risk = [0]*len(self.avg)
        self.cnt_good_sell = [0]*len(self.avg)
        self.cnt_good_buy = [0]*len(self.avg)
        self.cnt_bad_sell = [0]*len(self.avg)
        for a in range(len(self.avg)):
            self.cnt_bad_sell[a] = len([x for x in self.low_list[:a+period-1] if x <= self.bad_sell[a]])
            self.cnt_good_sell[a] = len([x for x in self.high_list[:a + period - 1] if x >= self.good_sell[a]])
            self.cnt_bad_sell[a] = len([x for x in self.low_list[:a + period - 1] if self.bad_sell[a] < x <= self.good_buy[a]])
            self.cnt_risk[a] = len([x for x in self.low_list[:a+period-1] if x <= self.close_list[a+period-1]])


        # MACD
        macd_temp = list(ta.MACD(self.close_list, 10, 20, 5))
        self.macd_list = [x for x in macd_temp[2] if str(x) != 'nan']


        # BOLL
        bool_up_list, bool_mid_list, bool_dn_list = ta.BBANDS(list_close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
        self.bool_up = [x for x in bool_up_list if str(x)!='nan']
        self.bool_mid = [x for x in bool_mid_list if str(x)!='nan']
        self.bool_dn = [x for x in bool_dn_list if str(x)!='nan']
        self.get_data_src()

    def get_data_src(self):
        self.data_train = []
        self.data_target = []
        for i in range(1,len(self.macd_list)):
            train = [self.avg[len(self.avg)-1-i],self.vol_list[len(self.vol_list)-1-i],self.cnt_bad_sell[len(self.cnt_bad_sell)-1-i],self.cnt_good_buy[len(self.cnt_good_buy)-1-i],self.cnt_good_sell[len(self.cnt_good_sell)-1-i],self.cnt_risk[len(self.cnt_risk)-1-i],self.af[len(self.af)-1-i],self.fq[len(self.fq)-1-i],self.macd_list[len(self.macd_list)-1-i],self.kdj_list[len(self.kdj_list)-1-i],self.bool_up[len(self.bool_up)-1-i],self.bool_mid[len(self.bool_mid)-1-i],self.bool_dn[len(self.bool_dn)-1-i]]
            self.data_train.append(np.array(train))
            self.data_target.append(self.close[len(self.close) - i])
            #self.data_target.append(self.avg[len(self.avg)-i])
        self.test_case = np.array([self.avg[-1],self.vol_list[-1],self.cnt_bad_sell[-1],self.cnt_good_buy[-1],self.cnt_good_sell[-1],self.cnt_risk[-1],self.af[-1],self.fq[-1],self.macd_list[-1],self.kdj_list[-1],self.bool_up[-1],self.bool_mid[-1],self.bool_dn[-1]])
        self.data_train = np.array(self.data_train[::-1])
        self.data_target = np.array(self.data_target[::-1])


#
# def kdj(date, N=9, M1=3, M2=3):
#     datelen = len(date)
#     array = np.array(date)
#     kdjarr = []
#     for i in range(datelen):
#         if i - N < 0:
#             b = 0
#         else:
#             b = i - N + 1
#         rsvarr = array[b:i + 1, 0:5]
#         if (float(max(rsvarr[:, 3])) - float(min(rsvarr[:, 2]))) == 0:
#             rsv = -777
#         else:
#             rsv = (float(rsvarr[-1, 2]) - float(min(rsvarr[:, 4]))) / (float(max(rsvarr[:, 3])) - float(min(rsvarr[:, 2]))) * 100
#         if i == 0:
#             k = rsv
#             d = rsv
#         else:
#             k = 1 / float(M1) * rsv + (float(M1) - 1) / M1 * float(kdjarr[-1][2])
#             d = 1 / float(M2) * k + (float(M2) - 1) / M2 * float(kdjarr[-1][3])
#         j = 3 * k - 2 * d
#         kdjarr.append(list((rsvarr[-1, 0], rsv, k, d, j)))
#     return kdjarr

if __name__ == '__main__':
    a = data_collect2('601117','2017-12-01','2017-12-31')
    print('XXX')
