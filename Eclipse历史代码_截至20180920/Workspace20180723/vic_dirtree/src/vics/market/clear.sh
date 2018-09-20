#!/bin/bash


mysql -uops  -h127.0.0.1  -p'ops!@#9988'  -P3308 -e'delete  from vic_ticker.ticker'
mysql -uops  -h127.0.0.1  -p'ops!@#9988'  -P3308 -e'delete  from vic_1mk.1mk'
mysql -uops  -h127.0.0.1  -p'ops!@#9988'  -P3308 -e'delete  from vic_5mk.5mk'
mysql -uops  -h127.0.0.1  -p'ops!@#9988'  -P3308 -e'delete  from vic_1h.1h'
mysql -uops  -h127.0.0.1  -p'ops!@#9988'  -P3308 -e'delete  from vic_1d.1d'
