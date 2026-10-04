"""Extract frozen workbook cell evidence; compare pinned output to existing input bytes."""
from pathlib import Path
import hashlib,json,openpyxl,pandas as pd
ROOT=Path(__file__).resolve().parent
def main():
    d=ROOT/'official/technology-data';out={}
    items=[('data_sheets_for_renewable_fuels.xlsx',['86 AEC 100 MW','Intro']),('technology_data_catalogue_for_energy_storage.xlsx',['151a Hydrogen Storage - Tanks','151c Hydrogen Storage - Caverns']),('technology_data_for_el_and_dh.xlsx',['12 LT-PEMFC CHP'])]
    for fn,sheets in items:
        p=d/'inputs'/fn;wb=openpyxl.load_workbook(p,read_only=True,data_only=True)
        rec={'sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),'properties':{k:str(getattr(wb.properties,k)) for k in ['title','created','modified','description']},'sheets':{}}
        for sheet in sheets:
            if sheet not in wb.sheetnames:rec['sheets'][sheet]={'not_found':True};continue
            s=wb[sheet];rows=[]
            for rownum,row in enumerate(s.iter_rows(),1):
                vals=[{'cell':c.coordinate,'value':c.value} for c in row if c.value is not None]
                text=' '.join(str(c['value']) for c in vals).lower()
                if rownum<=7 or any(t in text for t in ['hydrogen output','technical life','fixed o&m','investment','round trip','efficiency','total input','higher heating','lower heating','lhv','hhv','2020','2030','january','october','april','version']):
                    rows.append(vals)
            rec['sheets'][sheet]=rows
        out[fn]=rec
    cmp=[]
    prev=ROOT.parent/'00_model_audit/input_snapshot/resources/baseline-aims-3H-tutorial'
    for yr in [2030,2040,2050]:
        a=d/f'outputs/costs_{yr}.csv'; matches=list(prev.rglob(f'pre_costs_{yr}.csv'))
        if matches:
            b=matches[0];df=pd.read_csv(a,index_col=[0,1]);df2=pd.read_csv(b,index_col=[0,1])
            cmp.append({'year':yr,'upstream_sha256':hashlib.file_digest(a.open('rb'),'sha256').hexdigest(),'model_sha256':hashlib.file_digest(b.open('rb'),'sha256').hexdigest(),'byte_equal':a.read_bytes()==b.read_bytes(),'dataframe_equal':df.equals(df2)})
    out['cost_file_comparison']=cmp
    (ROOT/'DEA_WORKBOOK_EVIDENCE.json').write_text(json.dumps(out,indent=2,ensure_ascii=False,default=str),encoding='utf-8')
    print(json.dumps({k:v if k=='cost_file_comparison' else {x:y for x,y in v.items() if x!='sheets'} for k,v in out.items()},indent=2,ensure_ascii=False))
if __name__=='__main__':main()
