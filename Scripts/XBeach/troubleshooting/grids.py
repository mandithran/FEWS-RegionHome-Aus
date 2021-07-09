import numpy as np
import os

workingPath = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Modules\\XBeach\\Narrabeen\\runs\\2021050300_3\\workDir"
working_xgrd = os.path.join(workingPath, "x.grd")
working_ygrd = os.path.join(workingPath, "y.grd")
working_zgrd = os.path.join(workingPath, "bed.DEP")

problemPath = "C:\\Users\\z3531278\\Documents\\01_FEWS-RegionHome-Aus\\Modules\\XBeach\\Narrabeen\\2021070700SystemTime-Narrabeen"
problem_xgrd = os.path.join(problemPath, "x.grd")
problem_ygrd = os.path.join(problemPath, "y.grd")
problem_zgrd = os.path.join(problemPath, "z.grd")

w_xgrd = np.loadtxt(working_xgrd)
p_xgrd = np.loadtxt(problem_xgrd)
print(w_xgrd.shape)
print(p_xgrd.shape)

w_ygrd = np.loadtxt(working_ygrd)
p_ygrd = np.loadtxt(problem_ygrd)
print(w_ygrd.shape)
print(p_ygrd.shape)

w_zgrd = np.loadtxt(working_zgrd)
p_zgrd = np.loadtxt(problem_zgrd)
print(w_zgrd.shape)
print(p_zgrd.shape)