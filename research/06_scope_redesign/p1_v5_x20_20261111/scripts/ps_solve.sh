#!/bin/bash
ps -eo pid,etime,rss,args | grep -E '[s]2_solve\.py|[g]urobi_cl|[p]ytest' | cut -c1-250
