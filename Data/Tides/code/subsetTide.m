tide = load('..\raw\SYDNEY_ASTRO_TIDE_1979_2050.mat')

index1 = 700000; %1998
index2 = 1800000; %2030

formatOut = 'dd-mm-yyyy HH:MM';
time_AEST2 = datetime(tide.tide.time_AEST(1,index1:index2),'ConvertFrom','datenum');
time_AEST2 = datestr(tide.tide.time_AEST(1,index1:index2),formatOut);
astro_tide2 = tide.tide.astro_tide(1,index1:index2);

time_AEST2 = string(time_AEST2);
astro_tide2 = transpose(double(astro_tide2))

arr = [time_AEST2, astro_tide2];

header = {"Time (dd/mm/yyyy HH:MM AEST)","Elevation (m AHD)"};
output = [header; num2cell(arr)];
writecell(output,'..\processed\SydneyTidesAEST.csv');
