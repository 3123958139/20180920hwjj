#!/bin/bash

# 1. 数据库间迁移数据 以便补全
# 2. 迁移前可以删除相应时间不对的1d 
# 3. 更新时间段限制
# 4. 更新数据（update set）
# 5. 非行情数据之外的主从

mysql -h47.74.179.216 -P3308 -uops -p'ops!@#9988' -e'select * from vic_1d.1d  where ts>="2018-06-13";' -N -s -q | awk -F'\t' '{printf("insert into vic_1d.1d values(\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\");", $1,$2,$3,$4,$5,$6,$7,$8,$9)}' | mysql -h47.74.249.179 -P3308 -uops -p'ops!@#9988' vic_1d  -f

mysql -h47.74.179.216 -P3308 -uops -p'ops!@#9988' -e'select * from vic_1h.1h  where ts>"2018-06-13";' -N -s -q | awk -F'\t' '{printf("insert into vic_1h.1h values(\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\");", $1,$2,$3,$4,$5,$6,$7,$8,$9)}' | mysql -h47.74.249.179 -P3308 -uops -p'ops!@#9988' vic_1h  -f

mysql -h47.74.179.216 -P3308 -uops -p'ops!@#9988' -e'select * from vic_5mk.5mk where ts>"2018-06-13";' -N -s -q | awk -F'\t' '{printf("insert into vic_5mk.5mk values(\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\");", $1,$2,$3,$4,$5,$6,$7,$8,$9)}' | mysql -h47.74.249.179 -P3308 -uops -p'ops!@#9988' vic_5mk  -f

mysql -h47.74.179.216 -P3308 -uops -p'ops!@#9988' -e'select * from vic_1mk.1mk  where ts>"2018-06-13";' -N -s -q | awk -F'\t' '{printf("insert into vic_1mk.1mk values(\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\");", $1,$2,$3,$4,$5,$6,$7,$8,$9)}' | mysql -h47.74.249.179 -P3308 -uops -p'ops!@#9988' vic_1mk  -f

mysql -h47.74.179.216 -P3308 -uops -p'ops!@#9988' -e'select * from vic_ticker.ticker  where ts>"2018-06-13";' -N -s -q | awk -F'\t' '{printf("insert into vic_ticker.ticker values(\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\");", $1,$2,$3,$4,$5,$6)}' | mysql -h47.74.249.179 -P3308 -uops -p'ops!@#9988' vic_ticker  -f

#mysql -h47.74.249.179 -P3308 -uops -p'ops!@#9988' -e'select * from vic_1d.1d;' -N -s -q | awk -F'\t' '{printf("insert into vic_1d.1d values(\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\");", $1,$2,$3,$4,$5,$6,$7,$8,$9)}' | mysql -h47.74.179.216 -P3308 -uops -p'ops!@#9988' vic_1d  -f

#mysql -h47.74.249.179 -P3308 -uops -p'ops!@#9988' -e'select * from vic_1h.1h;' -N -s -q | awk -F'\t' '{printf("insert into vic_1h.1h values(\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\");", $1,$2,$3,$4,$5,$6,$7,$8,$9)}' | mysql -h47.74.179.216 -P3308 -uops -p'ops!@#9988' vic_1h  -f

#mysql -h47.74.249.179 -P3308 -uops -p'ops!@#9988' -e'select * from vic_5mk.5mk;' -N -s -q | awk -F'\t' '{printf("insert into vic_5mk.5mk values(\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\");", $1,$2,$3,$4,$5,$6,$7,$8,$9)}' | mysql -h47.74.179.216 -P3308 -uops -p'ops!@#9988' vic_5mk  -f

#mysql -h47.74.249.179 -P3308 -uops -p'ops!@#9988' -e'select * from vic_1mk.1mk;' -N -s -q | awk -F'\t' '{printf("insert into vic_1mk.1mk values(\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\");", $1,$2,$3,$4,$5,$6,$7,$8,$9)}' | mysql -h47.74.179.216 -P3308 -uops -p'ops!@#9988' vic_1mk  -f


#mysql -h47.74.249.179 -P3308 -uops -p'ops!@#9988' -e'select * from vic_ticker.ticker;' -N -s -q | awk -F'\t' '{printf("insert into vic_ticker.ticker values(\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\");", $1,$2,$3,$4,$5,$6)}' | mysql -h47.74.179.216 -P3308 -uops -p'ops!@#9988' vic_ticker  -f




