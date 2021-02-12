# =================== Import Modules =================== #
import netCDF4 as nc
import numpy as numpy
import os
import matplotlib.pyplot as plt

# =================== Paths =================== #
# Relative to Region Home, since that is where executable is called from
importDir = ".\Import\AusSurge"
fname = 'IDZ00154_StormSurge_national_2020122400.nc'
importPath = os.path.join(importDir,fname)

import numpy as np
import netCDF4 as nc

def readNetcdf(ncObj, varname='surge', verbose=False):
  '''
  context: 
      assume dims are (time, x, y) or (point,time)
      regular grid or point array only
  '''
  
  varObj  = ncObj.variables[varname]
  dims    = varObj.dimensions
  allVars = ncObj.variables.keys()

  # try to identify coords
  try:
      varY,varX = varObj.coordinates.strip().split(' ')            # mixed-bag as to how this meta data is used: 'lat lon' or 'lon lat'   
  except:
      print("!! couldnt use coorindates metadata")
      print(varObj)
      varY = 'lat'
      varX = 'lon'

  if (('y'   in (varX).lower()) and ('x'   in (varY).lower())) or \
     (('lat' in (varX).lower()) and ('lon' in (varY).lower())):
         print("!! looks like coordinate metadata is mis-ordered ...try to flip!!")
         oldX = varX; oldY = varY
         varY = oldX; varX = oldY
  if verbose:  
      print("x/y coord names from metadata: ", varX,varY)

  # time
  if   len(dims)==3:
      varT  = varObj.dimensions[0]  # assume time is 1st and varname==dimname
  elif len(dims)==2:
      varT  = varObj.dimensions[1]  # assume time is 2nd and varname==dimname
  else:
      print("!! problem with assumed data shape !!")
      sys.exit(1)

  # check   
  if (varX not in allVars) or (varY not in allVars):
      if verbose:  
          print("!! override x/y coord names with guesses")
      varX = 'lon'    # guess
      varY = 'lat'    # guess
  if (varT not in allVars):
      if verbose:  
          print("!! override t coord names with guesses")
      varT = 'Time'   # guess

  # read array
  data = ncObj.variables[varname]
  X    = ncObj.variables[varX]     
  Y    = ncObj.variables[varY]
  T    = ncObj.variables[varT]

  # spatial slice  
  if len(dims)==3:
      data_slice = data[0,:,:]
  elif len(dims)==2:
      data_slice = data[:,0]

  # wet mask
  if 'wet' in allVars:
      wet  = ncObj.variables['wet']
      if len( wet.dimensions ) != 2:
          wet = wet[0,:,:]
  elif 'sea_lnd_ice_mask' in allVars:
      wet  = (ncObj.variables['sea_lnd_ice_mask'][:,:] == 0).astype("f")     # 0=ocean, 1=ice, 2=land    ! sic = want float, not int
  else:
      try:
          mask = data_slice.mask
      except:
          if verbose:  
              print("no mask field, derive...")
          try:
              vmin,vmax = data.valid_range
              if verbose:  
                  print("valid minmax", vmin,vmax)
                  print("mask field from valid_range attr")
              data_masked = np.ma.masked_outside( data_slice, vmin, vmax)
              mask = data_masked.mask
          except:
              if verbose:  
                  print("no mask info at all ...assume all points are valid")
              mask = np.zeros( data_slice.shape )
      # ...derive wet from land/sea 
      wet = np.abs((mask-1))*1.0

  # note order
  return T,Y,X,data,wet

ds = nc.Dataset(importPath)
time,y,x,data,wet = readNetcdf(ds)