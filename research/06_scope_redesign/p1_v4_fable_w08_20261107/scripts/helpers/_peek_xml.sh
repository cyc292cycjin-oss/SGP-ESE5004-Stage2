cd /home/jin/wt_v4_fable/research_inputs/assembly_v1/sources/unsd_sdmx_2019 || exit 1
echo "== header =="; head -c 1500 ID_2019_all.xml; echo
echo "== one series (hard coal 0100, industry 121) =="
python3 - <<'PY'
import xml.etree.ElementTree as ET
NS={"g":"http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic"}
root=ET.parse("ID_2019_all.xml").getroot()
n=0
for s in root.iter(f"{{{NS['g']}}}Series"):
    key={v.get("id"):v.get("value") for v in s.find("g:SeriesKey",NS)}
    if key.get("COMMODITY") in ("0100","5110","7000","4670") and key.get("TRANSACTION") in ("121","1214G","1231","1221"):
        sa=s.find("g:Attributes",NS); satt={v.get("id"):v.get("value") for v in (sa if sa is not None else [])}
        for o in s.findall("g:Obs",NS):
            oa=o.find("g:Attributes",NS); att={a.get("id"):a.get("value") for a in (oa if oa is not None else [])}
            print(key, "SERIES_ATT", satt, "OBS", o.find("g:ObsValue",NS).get("value"), att); n+=1
    if n>12: break
PY
echo "== codelists file =="; ls -la ../unsd_targeted/ | head; python3 -c "
import json; c=json.load(open('../unsd_targeted/codelists.json')); print(list(c.keys())); print({k:c['CL_TRANSACTION_NRG'][k] for k in ['121','1211','1213','1214B','1214F','1214G','1214O','1231','1221','1222','1225']}); print({k:c['CL_COMMODITY_NRG'].get(k) for k in ['0100','0129','0210','0311','3000','4670','4652','5110','5120','5140','5150','5160','7000']})"
