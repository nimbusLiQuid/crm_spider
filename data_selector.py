#!/usr/bin/python3
#! coding: utf-8
import sys
from data_divide import data_selecter

if __name__ == '__main__':
    token, date, tag_id  = sys.argv[1], sys.argv[2], int(sys.argv[3])
    if '-' in date:
        date = date.replace('-', '')
    data_selecter(token, date, tag_id)
