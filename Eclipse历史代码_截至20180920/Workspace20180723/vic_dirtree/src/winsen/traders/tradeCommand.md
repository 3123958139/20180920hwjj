1. 查看成交记录:
  mysql -h47.74.249.179 -P3308 -uops -p'ops!@#9988';
  show databases;
  use positions;
  select * from BW1Slippage order by  updatetime desc limit 100;

2. 查看持仓情况:
  select * from BW1Trend;


<<<<<<< HEAD
=======
3.统计策略持仓



>>>>>>> d8a4ca88494299afe78eb6a6f04d4849c0bf00c5

3.talib---ImportError: libta_lib.so.0: cannot open shared object file: No such file or directory
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
