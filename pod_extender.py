#!/usr/bin/env python

import json
import subprocess


class BodegaOrder:
    def __init__(self, sid, status, time_created, ejection_time):
        self.sid = sid
        self.status = status
        self.time_created = time_created
        self.ejection_time = ejection_time

    def encodeJSON(self):
        return self.__dict__


if __name__ == '__main__':
    bodega_cmd = '/home/ubuntu/sdmain/lab/bin/bodega'
    output = subprocess.check_output([bodega_cmd, 'list', 'orders'])
    print output

    output = output.split('\n')
    for line in output[1:]:
        order_info = line.split('\t')
        bodega_order = BodegaOrder(order_info[0].strip(), order_info[1].strip(),
                                   order_info[2].strip(), order_info[3].strip())
        print json.dumps(bodega_order.encodeJSON())
        print subprocess.check_output([bodega_cmd, 'extend', 'order', bodega_order.sid, '-t', '1d'])
