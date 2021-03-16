tide = load('..\raw\SYDNEY_ASTRO_TIDE_1979_2050.mat')

index1 = 700000; %1998
index2 = 1800000; %2030

formatOut = 'dd-mm-yyyy HH:MM';
time_AEST2 = datetime(tide.tide.time_AEST(1,index1:index2),'ConvertFrom','datenum');
time_GMT = time_AEST2 - hours(10);
time_GMT = datestr(time_GMT,formatOut);
astro_tide2 = tide.tide.astro_tide(1,index1:index2);
time_GMT = string(time_GMT);
astro_tide2 = transpose(double(astro_tide2));
arr = [time_GMT, astro_tide2];
header = {"Time (dd/mm/yyyy HH:MM GMT)","Elevation (m AHD)"};
output = [header; num2cell(arr)];
writecell(output,'..\processed\SydneyTidesGMT.csv');
