import json
from meta_mapper import MetaMapper
import os
from pathlib import Path

dirs = [ "/archive/GT/legacy/150611_D00138_0249_AHMMHKADXX_Project_15NGS-001-jxb/CHU1351",
        "/archive/GT/2020/JacquesBanchereau_Lab_CT/20200106_19-banchereau-049"]

dirs = [ "/archive/GT/legacy/pacbio/helix/20160323-NS76NS119NS118F308F309-42248_125"]

dirs = [ "/archive/GT/2019/CharlesLee_Lab_CT/20190906_19-lee-004-run3.old/4_D01"]

dirs = [ "/archive/GT/2019/JacquesBanchereau_Lab_CT/20191002_19-banchereau-026-run3/1_A01"]

dirs = [ "/archive/GT/legacy/pacbio/aws/20150403_m1m2test_gwlib_42225_91",
         "/archive/GT/legacy/pacbio/amp/20150528-bmx2-42225_105",
         "/archive/GT/legacy/pacbio/helix/20151019-IsoseqHIPC1014_FluD60_CD19_Bcell_T0-42248_95" ]

dirs = [ "/archive/GT/2018/JacquesBanchereau_Lab_CT/20180116_17-banchereau-054-run5.old"]


dirs = [ "/archive/GT/2017/BillSkarnes_Lab_CT/20170329_17-cel-001" ]

dirs = [ "/archive/GT/2019/CharlesLee_Lab_CT/20190823_19-lee-004"]

dirs = [ "/archive/services/singlecell/shares/singlecell-delivery/Opera_Phenix_1400L17156/Ed_Liu-lab/pkumar-20181109" ]

dirs = [ "/archive/GT/legacy/160920_NS500460_0193_AHKJHHBGXY/ROS3254" ]

dirs = [ "/archive/faculty/clee-lab/qzhu/2020-07-08/Eichler_HIFI_data", 
         "/archive/faculty/banchereau-lab/adeslat/2017-09-21/BLCA043"]

dirs = [ "/archive/faculty/verhar-lab/amins/2019-11-12/i_E2CD-T1-A2-J01" ]

mapper = MetaMapper()


def get_json_dirs(root_dir):
    json_dirs = set()
    json_filenames = Path(root_dir).rglob("*.json")
    for filename in json_filenames:
        dir = os.path.dirname(filename)
        json_dirs.add(dir)
    return json_dirs

#for dir in dirs: #get_json_dirs("/archive/services/singlecell/shares"):
for dir in get_json_dirs("/archive"):

    print("For directory: " + dir)
    new_doc = mapper.create_new_document(dir)
    if not new_doc:
        print("Failed to get doc for " + dir)
        continue
    if "_id" in new_doc:
        new_doc["_id"] = str(new_doc["_id"])
    #print(json.dumps(new_doc, indent=4, sort_keys=True))

