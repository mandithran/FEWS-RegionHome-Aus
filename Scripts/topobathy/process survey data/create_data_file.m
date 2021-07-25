%read the transect survey files of the embayment and create a separate file
%combining all this data
clear
close all
fclose all;

files=dir(['*.csv']);
files={files.name};

x=[];
y=[];
z=[];
for ii=1:length(files)
    [~, easting, northing, elevation, ~] = textread(files{ii},'%s %f %f %f %s','delimiter', ',', 'headerlines',  1);
    if easting(1)>370000 || easting(1)<320000 || northing(1)>7000000 || northing(1)<6000000
        error('Easting and northing may be switched')
    end
    x=vertcat(x, easting);
    y=vertcat(y, northing);
    z=vertcat(z, elevation);
    clear easting northing elevation
end
ind=find(z<0); %remove everything below MSL because the average bathy will be used
x(ind)=[];
y(ind)=[];
z(ind)=[];

%write into a txt file with xyz data in xyz coordiantes
saveloc=['..\RTKGPS_survey.xyz'];
tmp(:, 1)=x;
tmp(:, 2)=y;
tmp(:, 3)=z;
dlmwrite(saveloc, tmp, 'precision', 15)

    
    
    
