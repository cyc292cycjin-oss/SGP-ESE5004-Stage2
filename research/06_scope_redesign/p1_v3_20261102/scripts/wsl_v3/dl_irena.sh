#!/bin/bash
D=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/intake/lit
mkdir -p $D
curl -sS -L --max-time 200 --max-filesize 52428800 -A "Mozilla/5.0" -o $D/IRENA_Global_Trade_Hydrogen_2022.pdf -w "http=%{http_code} size=%{size_download} type=%{content_type}\n" "https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2022/Apr/IRENA_Global_Trade_Hydrogen_2022.pdf"
ls -la $D; sha256sum $D/* ; head -c 8 $D/IRENA_Global_Trade_Hydrogen_2022.pdf | xxd | head -1
