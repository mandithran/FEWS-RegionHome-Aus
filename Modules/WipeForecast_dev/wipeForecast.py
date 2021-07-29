    ############ Remove Excess XBeach output to save space ################
    postProcTools.delete_files(hotspotFcst.xbWorkDir,"*.nc")
    postProcTools.delete_files(hotspotFcst.xbWorkDir,"*.bcf")

    ############ Remove Module Directory where original run took place #############
    shutil.rmtree(hotspotFcst.moduleDir)