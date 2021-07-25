% This script is used to prepare the pre-storm and post-storm morphology
% for the 1DH XBeach runs. This is done by creating an spz surface and then
% extracting the transect


%% Initialisation
clear
close all
close all hidden

% storms2prep={...
%     '2020_02_09 storm',...
%     '2020_07_15 storm',...
%     '2020_07_28 storm',...
%     '2020_08_10 storm'};
storms2prep={...
    '2020_07_15 storm'};

%the grid used by xbeach. This has the first point (1,1) as the northern
%most offshore point
xbgrid='C:\Nash\UNSW\Postgrad\Research\Questions\Q5_1\xb_calibration\2DH\Model_Input_Data\morphology\Processed\Grid\xbgrid.mat';

%morphology location
basefolder='C:\Nash\UNSW\Postgrad\Research\Questions\Q5_1\Model_Input_Data\';

%deep bathy file location
deepbathyfile='C:\Nash\UNSW\Postgrad\Research\Data\Water Research Lab\Narrabeen Survey Data\Bathymetry\Deep bathy\narradeepbathydata.mat';

%location of all bathymetry data that is to be used to create the synthetic
%bathymetry
narrabathyfile='C:\Nash\UNSW\Postgrad\Research\Data\Water Research Lab\Narrabeen Survey Data\Bathymetry\narrabathy.mat';

%resolution of square grid to be used for the interpolation
p_res=0.5; %0.5 m resolution cross-shore
s_hires= -200:5:4000; %high resolution grid used for topography
s_lores= -200:50:4000; %low resolution grid used for bathymetry

%delaunay triangulation acceptable radius
dt_topo=120; %for topography because GPS transects were spaced this way
dt_bathy=80; %for bathymetry

%% create the input files

overwrite=0;

%load the storm data first
stormevents=[basefolder 'storms\stormevents.mat'];
stormevents=load(stormevents);
fns1=fieldnames(stormevents);
stormevents=stormevents.(fns1{1});
clear fns1

%deepbathy
deepbathyraw = load(deepbathyfile);
fns1=fieldnames(deepbathyraw);
deepbathyraw=deepbathyraw.(fns1{1});
%Add offset of 0.4m to 24/4/2014 survey due to observed offset
ind=find(deepbathyraw.info.date==735713);
deepbathyraw.rawdata(ind).z=deepbathyraw.rawdata(ind).z+0.4;
%create a structure to store the data
for ii=1:length(deepbathyraw.info.date)
    deepbathy.date(ii,1)=deepbathyraw.info.date(ii);
    deepbathy.data(ii).s=deepbathyraw.rawdata(ii).s;
    deepbathy.data(ii).p=deepbathyraw.rawdata(ii).p;
    deepbathy.data(ii).z=deepbathyraw.rawdata(ii).z;
end
clear deepbathyraw tmp fns1 ind deepbathyfile

%the individial bathymetry surveys
narrabathy=load(narrabathyfile);
fns1=fieldnames(narrabathy);
narrabathy=narrabathy.(fns1{1});
for ii=1:length(narrabathy.rawdata)
    %grab bathy date
    bathy.date(ii,1)=narrabathy.info.date(ii);
    
    %store the bathy spz dataset
    bathy.data(ii).s=narrabathy.rawdata(ii).s;
    bathy.data(ii).p=narrabathy.rawdata(ii).p;
    bathy.data(ii).z=narrabathy.rawdata(ii).z;
end
clear fnsl ii narrabathy narrabathyfile



%create the grid to interpolate the topo data onto
[Xtopo,Ytopo] = meshgrid(-200:p_res:1000, s_hires);

for mm=1:length(storms2prep)
    
    %find the row where the storm information is located
    stormdata_idx=find(ismember({stormevents.narrabeen.stormname}, storms2prep(mm)));
    if isempty(stormdata_idx)
        error('Unknown storm event')
    end
    
    foldername=[basefolder 'morphology\Rapid Response surveys\' stormevents.narrabeen(stormdata_idx).stormname '\'];
    
    %% prep the toporaphy
    for nn={'Poststorm', 'Prestorm'}
        
        %get the file with the data in it
        tmp=eval(['stormevents.narrabeen(stormdata_idx).' lower(nn{1}) '_topo']);
        filepath=[foldername datestr(tmp, 'yyyy_mm_dd') ' ' nn{1} '\'];
        dns1=dir([filepath '*.xyz']);
        dns1={dns1.name};
        survey_type=strsplit(dns1{1}, '_');
        survey_type=survey_type{1};
        if length(dns1)~=1
            error('There should be one file with the survey data')
        end
        
        %get the data in xyz from the file
        tmp=dlmread([foldername datestr(tmp, 'yyyy_mm_dd') ' ' nn{1} '\' dns1{1}], ',');
        surveydata_xyz.x=tmp(:, 1);
        surveydata_xyz.y=tmp(:, 2);
        surveydata_xyz.z=tmp(:, 3);
        %convert to spz
        surveydata_spz=xyz2spz(surveydata_xyz, 'NARRA');
        
        %convert the data to spz and interpolate onto the grid
        querysize = size(Xtopo);
        %data points
        datain.x=surveydata_spz.p(:);
        datain.y=surveydata_spz.s(:);
        datain.z=surveydata_spz.z(:);
        %query points
        query.x = Xtopo(:);
        query.y = Ytopo(:);
        %interpolation
        subar = delaunay_interpolation(datain, query, dt_topo, 0);
        Ztopo = reshape(subar.z, querysize);
        clear querysize datain query subar tmp
        
        %remove landward boundary interpolations that exceed the surveyed data
        Ztopo=remove_landward_interps(Xtopo, Ytopo, Ztopo, surveydata_spz, surveydata_xyz, survey_type, filepath);
        %remove the seaward boundary interpolations that exceed the
        %survey data of the topo. This causes issues with the boundary,
        %especially for the LiDAR data.
        Ztopo=remove_seaward_interps(Xtopo, Ytopo,  Ztopo, surveydata_spz, surveydata_xyz, survey_type, filepath);
        
        %if this is the post-storm surface then it is done at this point
        if strcmp(nn{1}, 'Poststorm')
            pfdata.metadata.event=[storms2prep{mm} ' Narrabeen']; %storm
            pfdata.metadata.morphology_type='Post-storm topography';
            pfdata.metadata.bathy_date=('N/A');
            pfdata.metadata.toposurvey_date=stormevents.narrabeen(stormdata_idx).poststorm_topo;
            pfdata.metadata.dune_data='2016 June Backbeach';
            pfdata.metadata.coordinates='spz';
            
            %grid the data into a higher resolution surface
            xx = -200:1:1000;
            yy=-200:5:4000;
            [post_surf.x, post_surf.y] = meshgrid(xx,yy);
            %grid into a surface using natural neighbour
            post_surf.z = griddata(Xtopo(:), Ytopo(:), Ztopo(:), post_surf.x, post_surf.y, 'natural');
            %remove landward boundary interpolations that exceed the surveyed data
            post_surf.z=remove_landward_interps(post_surf.x, post_surf.y,  post_surf.z, surveydata_spz, surveydata_xyz, survey_type, filepath);
            %remove the seaward boundary interpolations that exceed the
            %survey data of the topo. This causes issues with the boundary,
            %especially for the LiDAR data.
            post_surf.z=remove_seaward_interps(post_surf.x, post_surf.y,  post_surf.z, surveydata_spz, surveydata_xyz, survey_type, filepath);
            %there can sometimes be landward boundary locations where weird
            %things can happen during the interpolation so identify them and
            %remove them
            post_surf.z=cleanup_interpolation(post_surf.x, post_surf.y, post_surf.z);
            %fill in the remaining with the surface data from 2016 which extends
            %much further to the backbeach as the 2016 is a combination of the
            %UAV and LiDAR datasets. The reason that this data is added after
            %the interpolation onto the finer pre_surf grid is because the
            %backbeach data has a very high point density so rather then
            %decimating the data onto a coarse grid and then interpolating
            %onto the finer grid using 'griddata' and lose information, it is
            %better to just interpolate straight onto the finer grid and
            %maintain all the features in the data
            post_surf=fill_backbeach(post_surf);
            
            %there is no need to interpolate the post-storm profile onto
            %the xbeach grid. Instead it is used as is
            pfdata.data=post_surf;
            
            %check and correct if the 0.7 has been not reached
            pfdata=check_and_correct_shoreline(pfdata, storms2prep{mm});
            
            %save the surface
            saveloc=['..\Processed\' storms2prep{mm} '\' nn{1} '\'];
            variable_save_name='Poststorm_pfdata.mat';
            overwrite=save_variable(saveloc, variable_save_name, pfdata, overwrite);
            clear post_surf xx yy pfdata tmp temp saveloc variable_save_name...
                 xb_grid gridfile
            continue
        end
        
        
        %if it is the pre-storm surface then attach the average bathymetry
        %make the bathy grid
        [Xbathy,Ybathy] = meshgrid(-200:p_res:1000, s_lores); %use 0.5m east-west resolution
        querysize = size(Xbathy);
        %query points
        query.x = Xbathy(:);
        query.y = Ybathy(:);

        %each of the bathys
        for ii=1:length(bathy.date)
            %data points
            datain.x=bathy.data(ii).p;
            datain.y=bathy.data(ii).s;
            datain.z=bathy.data(ii).z;

            %delauny interpolation of the surveyed bathymetry onto the spz grid
            bathygrid = delaunay_interpolation(datain, query, dt_bathy, 0);

            %stored as a 3D array of xyz with the bathymetry values in the third
            %dimension
            Zbathy(:,:, ii) = reshape(bathygrid.z, querysize);
            clear bathygrid datain
        end
        clear query querysize ii

        %for each alongshore location calculate take the average value
        created_bathy=NaN(size(Xbathy)); %to store the range of the 95% confidence interval
        for ii=1:length(Xbathy(:,1)) %alongshore locations
            tmp=squeeze(Zbathy(ii, :, :));
            tmp=tmp'; %so that each bathy fills a row

            for jj=1:length(tmp(1, :)) %for each of the x-coordinates
                %if there are less than 3 datasets, ignore
                if sum(~isnan(tmp(:,jj)))>=3
                    %otherwise, for each x-coordinate find the 95% Confidence interval
                    [mew, ~]=normfit(tmp(~isnan(tmp(:,jj)),jj)); %mean and std for each x-coordiante
                    %mean of the gaussian distribution
                    created_bathy(ii, jj)=mew;
                    clear mew 
                end
            end
            
            clear tmp
        end
        
        %interpolate the deepbathy onto the same grid as the bathy data
        [Xdeepbathy,Ydeepbathy] = meshgrid(-200:p_res:1000, s_lores); %use 0.5m east-west resolution
        querysize = size(Xdeepbathy);
        %query points
        query.x = Xdeepbathy(:);
        query.y = Ydeepbathy(:);
        %data in- closest deep bathy
        [~, ind]=min(abs(deepbathy.date-datenum(stormevents.narrabeen(stormdata_idx).prestorm_topo)));
        datain.x=deepbathy.data(ind).p;
        datain.y=deepbathy.data(ind).s;
        datain.z=deepbathy.data(ind).z;
        bathygrid = delaunay_interpolation(datain, query, dt_bathy, 0);
        Zdeepbathy = reshape(bathygrid.z, querysize);
        clear querysize query bathygrid datain ind
        
        
        %for each alongshore location find the add the topo, bathy, and deep bathy
        xx_all = [];
        yy_all = [];
        zz_all = [];
        for ii=1:length(Ytopo(:,1)) %for each alongshore location on topo grid
            %add the topo data
            xx_all=[xx_all Xtopo(ii,:)];
            yy_all=[yy_all Ytopo(ii,:)];
            zz_all=[zz_all Ztopo(ii,:)];


            if ismember(Ytopo(ii,1), Ybathy(:,1))
                %if there is bathy and deep bathy data at the alongshore location
                row=find(ismember(Ybathy(:,1), Ytopo(ii,1)));

                %remove any points which are above zero and are landward of a point
                %that is above zero
                ind=find(created_bathy(row,:)>=0);
                if ~isempty(ind)
                    created_bathy(row, ind)=NaN;
                    x_offshore=Xbathy(row, ind(end))+10; %last x-point that was zero +10 for smooth
                    created_bathy(row, Xbathy(row, :)<=x_offshore)=NaN;
                    clear x_offshore
                end
                clear ind

                %smooth the transect using a 10 point moving average window
                if row>2 %first few alongshore locations ignore as there is too little data
                    tmp=smooth(Xbathy(row, :)', created_bathy(row, :)', 20, 'moving');
                    created_bathy(row, :)=tmp;
                    clear tmp
                end

                %remove all points which are a set meters from the end of the topo
                x_topo=find(~isnan(Ztopo(ii,:)), 1, 'last');
                if ~isempty(x_topo)
                    %if there are values
                    x_topo=Xtopo(ii, x_topo)+40; %most seaward point with topo data+35m to allow smooth transition
                    created_bathy(row, Xbathy(row, :)<=x_topo)=NaN; %removes all the points shoreward of that
                end
                clear x_topo

                xx_all=[xx_all Xbathy(row,:)];
                yy_all=[yy_all Ybathy(row,:)];
                zz_all=[zz_all created_bathy(row,:)];

                %find deepbathy
                ind=find(~isnan(created_bathy(row, :))); %where there is no bathy data
                if isempty(ind)
                    %if there is no bathy data then just add the whole deepbathy
                    xx_all=[xx_all Xdeepbathy(row,:)];
                    yy_all=[yy_all Ydeepbathy(row,:)];
                    zz_all=[zz_all Zdeepbathy(row,:)];
                else
                    %otherwise add to the seaward part of the bathy
                    xcutoff=max(Xbathy(row, ind))+10; %furthest point of data. Add an extra 10m to allow for smoother transition
                    ind1=find(Xdeepbathy(row,:)>xcutoff); %deep bathy data beyond that point

                    %add the deepbathy
                    xx_all=[xx_all Xdeepbathy(row,ind1)];
                    yy_all=[yy_all Ydeepbathy(row,ind1)];
                    zz_all=[zz_all Zdeepbathy(row,ind1)];
                    clear x_topo x_bathy xx_add zz_add tmp
                end
                clear ind ind1 xcutoff row
            end
        end
        %remove all NaN data as it cannot be present when creting the surface
        ind=find(isnan(zz_all));
        xx_all(ind) = [];
        yy_all(ind) = [];
        zz_all(ind) = [];
        clear ind


        %interpolate the gap between the topo end and the bathy start
        for ii=1:length(Ybathy(:,1)) %for each alongshore location on the topo grid where both topo and bathy will be present
            ind=find(yy_all==Ybathy(ii, 1)); %all the data at this alongshore coordinate

            topo_ind=find(zz_all(ind)>=0); %indices of the topo data at this alongshore coordinate
            if ~isempty(topo_ind) %if there is topographic data for interpolation
                bathy_ind=find(zz_all(ind)<0); %indices of the bathy data at this alongshore coordinate
                %the x-coordinates with missing data that need to be added
                xx_add=max(xx_all(ind(topo_ind)))+0.1: 0.1: min(xx_all(ind(bathy_ind)))-0.1;
                %the cubic interpolation between these points
                zz_add=interp1(xx_all(ind), zz_all(ind), xx_add, 'pchip');

                %check the slope of the added region to see if xbeach wetslope has
                %been exceeded. If it has, then as soon as the simulation starts
                %it will avalanche.
                slp=abs((zz_add(end-1)-zz_add(2))/(xx_add(end-1)-xx_add(2)));
                if slp>0.15 %the 0.15 value is the best vlue from Josh's thesis
                    disp(['The slope joining topo to bathy at ii= ' num2str(ii) ' is ' num2str(slp) ' and is larger than the xbeach calibrated wetslp of 0.15'])
                end
                clear slp

                %plot to see how it is
                %plot(xx_all(ind), zz_all(ind), '-', 'Color', 'b')
                %hold on
                %plot(xx_add, zz_add, '-', 'Color', 'r')
                %pause
                %hold off

                %add this interpolated data back into the mix
                xx_all = [xx_all xx_add];
                yy_all = [yy_all Ybathy(ii, 1)*ones(size(xx_add))];
                zz_all = [zz_all zz_add];
                clear bathy_ind xx_add zz_add
            end
            clear ind topo_ind
        end

        %now grid the data into a surface
        %Use 1m x 5m grid
        xx = -200:1:1000;
        yy=-200:5:4000;
        [pre_surf.x, pre_surf.y] = meshgrid(xx,yy);
        %grid into a surface using natural neighbour
        pre_surf.z = griddata(xx_all, yy_all ,zz_all, pre_surf.x, pre_surf.y, 'natural');
        %remove landward boundary interpolations that exceed the surveyed data
        pre_surf.z=remove_landward_interps(pre_surf.x, pre_surf.y, pre_surf.z, surveydata_spz, surveydata_xyz, survey_type, filepath);
        %there can sometimes be landward boundary locations where weird
        %things can happen during the interpolation so identify them and
        %remove them
        pre_surf.z=cleanup_interpolation(pre_surf.x, pre_surf.y, pre_surf.z);
        %fill in the remaining with the surface data from 2016 which extends
        %much further to the backbeach as the 2016 is a combination of the
        %UAV and LiDAR datasets. The reason that this data is added after
        %the interpolation onto the finer pre_surf grid is because the
        %backbeach data has a very high point density so rather then
        %decimating the data onto a coarse grid and then interpolating
        %onto the finer grid using 'griddata' and lose information, it is
        %better to just interpolate straight onto the finer grid and
        %maintain all the features in the data
        pre_surf=fill_backbeach(pre_surf);
        
        %first storm the pre-storm surface data as is
        %add meta data to the variables
        pfdata.metadata.event=[storms2prep{mm} ' Narrabeen']; %storm
        pfdata.metadata.morphology_type='Pre-storm average bathymetry';
        pfdata.metadata.bathy_date=('N/A');
        pfdata.metadata.toposurvey_date=stormevents.narrabeen(stormdata_idx).prestorm_topo;
        pfdata.metadata.dune_data='2016 June Backbeach';
        pfdata.metadata.coordinates='spz';
        %the xbeach grid data in xyz
        pfdata.data=pre_surf;
        %save the surface
        saveloc=['..\Processed\' storms2prep{mm} '\' nn{1} '\'];
        variable_save_name='Prestorm_average_pfdata.mat';
        overwrite=save_variable(saveloc, variable_save_name, pfdata, overwrite);
        clear pfdata variable_save_name saveloc
        
        
        
        %interpolate onto the XBeach grid and store that as well
        gridfile=load(xbgrid);
        fns1=fieldnames(gridfile);
        gridfile=gridfile.(fns1{1});
        gridfile.z=NaN(size(gridfile.x));
        %convert to spz to allow interpolation of grid
        tmp=xyz2spz(gridfile, 'NARRA');
        %flip so that landward north at (1,1) and store
        xb_grid.x=fliplr(tmp.p);
        xb_grid.y=fliplr(tmp.s);
        clear fns1 tmp

        %interpolate the created morphology surface onto the xbeach grid
        %query points
        query.x=xb_grid.x(:);
        query.y=xb_grid.y(:);
        %data points
        datain.x=pre_surf.x(:);
        datain.y=pre_surf.y(:);
        datain.z=pre_surf.z(:);
        intp=delaunay_interpolation(datain, query, 10, 0); %10m radius
        xb_grid.z=reshape(intp.z, size(xb_grid.x));
        clear query intp datain

        %check to see if there are any NaN values. There should not be as the grid
        %should remain exactly the same as with the control run
        [alongshore, ~]=size(xb_grid.x);
        for ii=1:alongshore
            if any(isnan(xb_grid.z(ii,:)))
                error(['Alongshore row ' num2str(ii) ' contains an NaN'])
            end
        end
        clear alongshore

        %flip the matrix back to the original format that can be used by xbeach.
        %there is a slight difference between the re-converted grid and the
        %original grid when spz is used so just make the grid the same. The z
        %doesn't change so it is kept as is
        xb_grid.x=gridfile.x;
        xb_grid.y=gridfile.y;
        xb_grid.z = fliplr(xb_grid.z);

        %the xbeach grid data in xyz
        pfdata.metadata.event=[storms2prep{mm} ' Narrabeen']; %storm
        pfdata.metadata.morphology_type='Pre-storm average bathymetry';
        pfdata.metadata.bathy_date=('N/A');
        pfdata.metadata.toposurvey_date=stormevents.narrabeen(stormdata_idx).prestorm_topo;
        pfdata.metadata.dune_data='2016 June Backbeach';
        pfdata.metadata.coordinates='xyz';
        %the xbeach grid data
        pfdata.data=xb_grid;

        %save the surface
        saveloc=['..\Processed\' storms2prep{mm} '\' nn{1} '\'];
        variable_save_name='Prestorm_average_xbgrid.mat';
        overwrite=save_variable(saveloc, variable_save_name, pfdata, overwrite);                 

        clear  Ztopo Zbathy created_bathy Xbathy Ybathy Xdeepbathy Ydeepbathy...
            Zdeepbathy saveloc xx_all yy_all zz_all ii jj xx yy temp tmp pfdata...
            variable_save_name  surveydata_spz surveydata_xyz pre_surf ind...
            survey_type xb_grid gridfile filepath
        
    end %loop for prestorm and poststorm
    
    clear stormdata_idx foldername
end
   




%% local functions

function Ztopo=remove_landward_interps(Xtopo, Ytopo, Ztopo, surveydata_spz, surveydata_xyz, survey_type, filepath)
    
    %creates a polygon on the landward boundary of the survey data and
    %removes any data within the polygon. This is because these
    %interpolations are usually errenous. This data is then filled back in
    %using the backbeach survey data from a LiDAR survey etc, making it
    %more reliable than the dodgy interpolations
    
    %first separate the survey data into transects and get the landward
    %points
    figure('units', 'normalized', 'outerposition', [0 0 1 1])
    scatter(Xtopo(:), Ytopo(:))
    hold on
    scatter(Xtopo(~isnan(Ztopo(:))), Ytopo(~isnan(Ztopo(:))))
    scatter(surveydata_spz.p, surveydata_spz.s)
    xlim([-100 100])
    ylim([200 3800])
    title('Select LANDWARD limits of survey data')
    
    ind_start=1;
    if strcmpi(survey_type, 'lidar')
        %if it is the LiDAR data then a seperate methodology is used to
        %define the limits
        tmp=find(diff(surveydata_xyz.y)~=0);
        for ii=1:length(tmp)
            %note: the last point is left out because it is usually hugging the
            %most landward point so no need
            tmp1.p=surveydata_spz.p(ind_start:tmp(ii));
            tmp1.s=surveydata_spz.s(ind_start:tmp(ii));
            [poly.x(ii, 1), idx]=min(tmp1.p);
            poly.y(ii, 1)=tmp1.s(idx);
            ind_start=tmp(ii)+1;
            clear idx tmp1
        end
    else
        %first check if a limits file has already been created and load it
        %if it has
        if exist([filepath 'landward_surveydata_limits_poly.mat'], 'file')
            load([filepath 'landward_surveydata_limits_poly.mat'])
        else
            %manually select the seaward limits
            [poly.x, poly.y]=ginputc;
        end
    end
    %close the polygon off a minimum of the surveyed data
    %point 1
    val=round(min(poly.x)-100,0);
    poly.x(end+1, 1)=val;
    poly.y(end+1, 1)=poly.y(end, 1);
    %point 2
    poly.x(end+1, 1)=val;
    poly.y(end+1, 1)=poly.y(1, 1);
    plot(poly.x, poly.y, 'g')
    
    if ~exist([filepath 'landward_surveydata_limits_poly.mat'], 'file')
        save([filepath 'landward_surveydata_limits_poly.mat'], 'poly')
    end

    %remove the Ztopo points which are inside the polygon or on the polygon
    %boundary
    [in, on]=inpolygon(Xtopo(:), Ytopo(:), poly.x, poly.y);
    tmp=Ztopo(:);
    tmp(in)=NaN;
    tmp(on)=NaN;
    
    Ztopo=reshape(tmp, size(Xtopo));
    close all

end


function Ztopo=remove_seaward_interps(Xtopo, Ytopo, Ztopo, surveydata_spz, surveydata_xyz, survey_type, filepath)
    
    %creates a polygon on the landward boundary of the survey data and
    %removes any data within the polygon. This is because these
    %interpolations are usually errenous. This data is then filled back in
    %using the backbeach survey data from a LiDAR survey etc, making it
    %more reliable than the dodgy interpolations
    
    %first separate the survey data into transects and get the landward
    %points
    
    figure('units', 'normalized', 'outerposition', [0 0 1 1])
    scatter(Xtopo(:), Ytopo(:))
    hold on
    scatter(Xtopo(~isnan(Ztopo(:))), Ytopo(~isnan(Ztopo(:))))
    scatter(surveydata_spz.p, surveydata_spz.s)
    xlim([-100 100])
    ylim([200 3800])
    title('Select SEAWARD limits of survey data')
    
    ind_start=1;
    if strcmpi(survey_type, 'lidar')
        %if it is the LiDAR data then a seperate methodology is used to
        %define the limits
        tmp=find(diff(surveydata_xyz.y)~=0);
        for ii=1:length(tmp)
            %note: the last point is left out because it is usually hugging the
            %most landward point so no need
            tmp1.p=surveydata_spz.p(ind_start:tmp(ii));
            tmp1.s=surveydata_spz.s(ind_start:tmp(ii));
            [poly.x(ii, 1), idx]=max(tmp1.p);
            poly.y(ii, 1)=tmp1.s(idx);
            ind_start=tmp(ii)+1;
            clear idx tmp1
        end
    else
        %first check if a limits file has already been created and load it
        %if it has
        if exist([filepath 'seaward_surveydata_limits_poly.mat'], 'file')
            load([filepath 'seaward_surveydata_limits_poly.mat'])
        else
            %manually select the seaward limits
            [poly.x, poly.y]=ginputc;
        end
        
    end
    %close the polygon off a minimum of the surveyed data
    %point 1
    val=round(max(poly.x)+100,0);
    poly.x(end+1, 1)=val;
    poly.y(end+1, 1)=poly.y(end, 1);
    %point 2
    poly.x(end+1, 1)=val;
    poly.y(end+1, 1)=poly.y(1, 1);
    plot(poly.x, poly.y, 'g')
    
    if ~exist([filepath 'seaward_surveydata_limits_poly.mat'], 'file')
        save([filepath 'seaward_surveydata_limits_poly.mat'], 'poly')
    end

    %remove the Ztopo points which are inside the polygon or on the polygon
    %boundary
    [in, on]=inpolygon(Xtopo(:), Ytopo(:), poly.x, poly.y);
    tmp=Ztopo(:);
    tmp(in)=NaN;
    tmp(on)=NaN;
    
    Ztopo=reshape(tmp, size(Xtopo));
    close all

end


function out=fill_backbeach(pre_surf)

    gap2use=5; %indices to leave as a gap for smoother interpolation
    
    %fill with the June 2016 post-storm data. The reason that this survey
    %is used because it is the survey data where the most exposed beach was
    %captured. So By using this we can ensure that any backfilling will be
    %filled with with non-erodible layers like the rock, and not sand
    %if another backbeach surface is to be used
    %then just replace this with that data
    June2016_surf=load('C:\Nash\UNSW\Postgrad\Research\Questions\Q5_1\xb_calibration\2DH\Model_Input_Data\morphology\Processed\Average_bathy\narrabeen 2016 June\poststorm\AverageMorphology_GriddedSurface.mat');
    fns1=fieldnames(June2016_surf);
    June2016_surf=June2016_surf.(fns1{1}).data;
    clear fns1

    for ii=1:length(pre_surf.y(:, 1)) %for each of the alongshore transects in the grid
        if ~all(June2016_surf.y(ii, :)==pre_surf.y(ii, :)) || ~all(June2016_surf.x(ii, :)==pre_surf.x(ii, :))
            error('The coordinate systems do not match for June 2016 back beach and current storm')
        end

        %backbeach added in only for locations with y>200 as this is only
        %where the data becomes reliable
        if pre_surf.y(ii, 1)<205
            continue
        end

        topo_start=find(~isnan(pre_surf.z(ii, :)), 1, 'first'); %first point with data
        topo_end=find(pre_surf.z(ii, :)>0, 1, 'last');

        %if there is no backbeach data in the June 2016 data then skip
        if ~any(~isnan(June2016_surf.z(ii, 1:topo_start-1)))
            continue
        end
        
        %if there is a gap between the first few points and the rest of the
        %profile at this point of the processing then remove the first few
        %points as it is most likely an error associated with an intepolation
        if any(isnan(pre_surf.z(ii, topo_start:topo_end)))
            tmp=topo_start:topo_end;
            idx=find(isnan(pre_surf.z(ii, topo_start:topo_end)), 1, 'last');
            idx=tmp(idx)+1;
            if idx-topo_start<=2 || pre_surf.z(ii, idx)<4
                %just gap fill it in as it is most likely just
                %mising data
                %sub=section of the profile with data
                x_sub=pre_surf.x(ii, topo_start:topo_end);
                z_sub=pre_surf.z(ii, topo_start:topo_end);

                %identify nan and non-nan data for interpolation
                nonnan_idx=find(~isnan(z_sub));
                x_add=x_sub(isnan(z_sub));
                %interpolate
                z_add=interp1(x_sub(nonnan_idx), z_sub(nonnan_idx), x_add, 'pchip');
                %add it back into sub-section
                z_sub(isnan(z_sub))=z_add;
                %add the sub section back into the original
                pre_surf.z(ii, topo_start:topo_end)=z_sub;
                clear x_sub z_sub nonnan_idx x_add z_add
            end
            topo_start=idx;
            pre_surf.z(ii, 1:topo_start-1)=NaN;
            clear idx tmp
        end

        %if there is data then back fill it in leaving a gap
        backfillend_ind=topo_start-gap2use;
        %check that the point being used in the backfill dataset is at or
        %above the topo start point
        if June2016_surf.z(ii, backfillend_ind)<pre_surf.z(ii, topo_start)-0.5  && pre_surf.y(ii, 1)>350
            %move the backfillend_ind to a value that is reasonable
            %plot(pre_surf.x(ii, :), pre_surf.z(ii, :), 'k')
            %hold on
            %plot(June2016_surf.x(ii, 1:backfillend_ind), June2016_surf.z(ii, 1:backfillend_ind), '--r')
            
           % a special case for the section around PF6 because some issues
            % happen because of the tree that is there sometimes in lidar
            % data
            if (pre_surf.y(ii, 1)>=2325 && pre_surf.y(ii, 1)<=2350) &&...
                    (pre_surf.x(ii, topo_start)-June2016_surf.x(ii, backfillend_ind))<10
                %leave as is 
            else
                %option 1 of using a closer z-valie
                opt1=find(June2016_surf.z(ii, :)>pre_surf.z(ii, topo_start)+0.2, 1, 'last');
                if backfillend_ind-opt1>35
                    backfillend_ind=backfillend_ind-10; %option 2 of using a distance
                else
                    backfillend_ind=opt1;
                end
                clear opt1
            end
        end
        pre_surf.z(ii, 1:backfillend_ind)=June2016_surf.z(ii, 1:backfillend_ind);

        %fill in the gap
        xadd=pre_surf.x(ii, backfillend_ind+1:topo_start-1);
        nonnans=find(~isnan(pre_surf.z(ii, :)));
        pre_surf.z(ii, backfillend_ind+1:topo_start-1)=interp1(pre_surf.x(ii, nonnans), pre_surf.z(ii, nonnans), xadd, 'pchip');

%         plot(pre_surf.x(ii, :), pre_surf.z(ii, :), 'k')
%         hold on
%         plot(June2016_surf.x(ii, 1:backfillend_ind), June2016_surf.z(ii, 1:backfillend_ind), '--r')
%         plot(xadd, pre_surf.z(ii, backfillend_ind+1:topo_start-1), 'g')
%         title(num2str(pre_surf.y(ii, 1)))
%         xlim([-200 100])
%         ylim([-2 15])
%         hold off
%         pause

        clear topo_start backfillend_ind xadd nonnans
    end
    
    out=pre_surf;
end


function Ztopo=cleanup_interpolation(Xtopo, Ytopo, Ztopo)
    %this function identifies landward boundary locations where there is a
    %sudden change in the gradient of the interpolation and removes that
    %section of the topo. This makes the next steps involving adding the
    %back layers much smoother
    
    x=Xtopo(1, :); %remains unchanged
    for ii=1:length(Ytopo(:, 1))
        %double check that x remains unchanged in the grid provided
        if ~all(Xtopo(ii, :)==x)
            error('The x-coordinate system changes in grid. Should not happen')
        end
        
        z=Ztopo(ii, :);
        if all(isnan(z))
            continue
        end
        
        %fill in any missing data
        start_ind=find(~isnan(z), 1, 'first');
        last_ind=find(~isnan(z), 1, 'last');
        if any(isnan(z(start_ind:last_ind)))
            %sub=section of the profile with data
            x_sub=x(start_ind:last_ind);
            z_sub=z(start_ind:last_ind);
            
            %identify nan and non-nan data for interpolation
            nonnan_idx=find(~isnan(z_sub));
            x_add=x_sub(isnan(z_sub));
            %interpolate
            z_add=interp1(x_sub(nonnan_idx), z_sub(nonnan_idx), x_add, 'pchip');
            %add it back into sub-section
            z_sub(isnan(z_sub))=z_add;
            %add the sub section back into the original
            z(start_ind:last_ind)=z_sub;
            
            clear z_sub z_add x_add nonnan_idx
        end
        
        [~, ind]=max(z);
        %if there is no data landward of this max then no issues
        if all(isnan(z(1:ind-1)))
            continue
        end
        
        %if there is data and it dips down then it is likely an
        %interpolation error so remove that section
        z(1:ind-1)=NaN;
         
        %if there is a plateau at the beginning then it is most likely an
        %error as well
        %first identify the plateau
        if z(ind)<0 %the case for the northern and southern bounadaries
            continue
        end
        tmp=diff(z);
        if abs(tmp(find(~isnan(tmp), 1, 'first')))<0.07
            idx=find(abs(tmp)<0.07);
            %the first continous section at the start of the profile
            sec=idx(1:find(diff(idx)~=1, 1, 'first'));
            if ~isempty(sec) && sec(1)~=ind
                continue %most likely a wrong place
            elseif isempty(sec) && idx(1)~=ind
                continue %another wrong place
            end
            z(sec)=NaN;
        end
        
        Ztopo(ii, :)=z;
        clear tmp idx sec ind start_ind tmp last_ind
        
    end
    
end
        
    
function overwrite=save_variable(saveloc, variablename, pfdata, overwrite)

    if ~exist(saveloc, 'dir')
        mkdir(saveloc)
    end
    
    if exist([saveloc variablename], 'file') && ~overwrite
        user_input=input('WARNING: Files exists, do you want to overwrite it? 1 for yes, any key for no: ');
        if user_input~=1
            error('Terminated by user')
        else
            overwrite=1;
        end
    end
    save([saveloc variablename], 'pfdata')
    
end


function pfdata= check_and_correct_shoreline(pfdata, storm)
    
    %some strorms already have known issues
    missing_locs=[];
    switch storm
        case '2020_02_09 storm'
            missing_locs=[3080;3085;3090;3095;3100;3105;3110;3115;3120;...
                3125;3130;3135;3140;3145;3150;3155;3160;3165;3170;3175;3180;...
                3185;3190;3195;3200;3205;3210;3215;3220;3225;3230;3235;3240;...
                3245;3250;3255;3260;3265;3270;3275;3280];
        case '2020_07_15 storm'
            missing_locs=[2105;2110;2115;2120;2125;2130;2135;2140;2145;...
                2150;2155;2160;2165;2170;2175;2180;2185;2225;2230;2235;...
                2240;2245;2250;2255;2260;2265;2270;2275;2280;2285;2290;2295;2300;2305];
    end

    %first check that there are no missing locs other than these identified
    for ii=1:length(pfdata.data.y(:, 1))
        if all(isnan(pfdata.data.z(ii, :))) | pfdata.data.y(ii, 1)<260
            continue
        end

        if ~any(pfdata.data.z(ii, :)<=0.7) && ~ismember(pfdata.data.y(ii, 1), missing_locs)
            error(['Post-storm y=' num2str(pfdata.data.y(ii, 1)) ' does not have the 0.7m contour'])
        end

    %     plot(pfdata.data.x(ii, :), pfdata.data.z(ii, :), 'k')
    %     xlim([-200 200])
    %     ylim([-1 12])
    %     title(num2str(pfdata.data.y(ii, 1)))
    %     pause

    end

    for ii=1:length(missing_locs)
        %get the row of the missing location
        missing_row(ii, 1)=find(pfdata.data.y(:, 1)==missing_locs(ii));

        %last location where there is data
        st_val=find(~isnan(pfdata.data.z(missing_row(ii, 1), :)), 1, 'last');
        if isempty(st_val) %the whole row is empty then go back and front and look for the nearest data
            found_front_loc=0;
            found_back_loc=0;
            increment_val=1; %value to increment row by
            while ~found_front_loc || ~found_back_loc
                if ~found_back_loc %find previous row withd data
                    %find the first index that isn't empty
                    tmp=find(~isnan(pfdata.data.z(missing_row(ii, 1)-increment_val, :)), 1, 'first');
                    if ~isempty(tmp)
                        val(1, 1)=tmp-1;
                        found_back_loc=1;
                    end
                    clear tmp
                end
                if ~found_front_loc %find front row withd data
                    %find the first index that isn't empty
                    tmp=find(~isnan(pfdata.data.z(missing_row(ii, 1)+increment_val, :)), 1, 'first');
                    if ~isempty(tmp)
                        val(2, 1)=tmp-1;
                        found_front_loc=1;
                    end
                    clear tmp
                end
                increment_val=increment_val+1;
            end
            last_ind(ii, 1)=max(val);
            clear found_front_loc found_back_loc increment_val val
        else
            last_ind(ii, 1)=st_val;
        end
        clear st_val

        %double check that this is less than 0.7m
        if pfdata.data.z(missing_row(ii, 1), last_ind(ii, 1))<=0.7
            error('This should be >0.7')
        end

    end


    for ii=1:length(missing_locs)
        %fill in the data
        pfdata=fill_missing_row(pfdata, missing_row(ii, 1), last_ind(ii, 1)+1);
    end

end

function pfdata=fill_missing_row(pfdata, missing_row, last_ind)

    if ~isnan(pfdata.data.z(missing_row, last_ind)) && pfdata.data.z(missing_row, last_ind)>0.7
        pfdata=fill_missing_row(pfdata, missing_row, last_ind+1);
        
    elseif isnan(pfdata.data.z(missing_row, last_ind))

        %get the existing data points
        first_data_row=find(~isnan(pfdata.data.z(:, last_ind)), 1, 'first'); %first data point
        last_data_row=find(~isnan(pfdata.data.z(:, last_ind)), 1, 'last'); %last data point
        nonnans=find(~isnan(pfdata.data.z(:, last_ind))); %all data points

        %get the missing section of interest
        nan_rows=find(isnan(pfdata.data.z(:, last_ind)));
        nan_rows=nan_rows(nan_rows>first_data_row & nan_rows<last_data_row &...
            nan_rows>=missing_row-100 & nan_rows<=missing_row+100);

        %carry out the interpolation
        y=pfdata.data.y(nan_rows, last_ind);
        z=interp1(pfdata.data.y(nonnans, last_ind), pfdata.data.z(nonnans, last_ind), y, 'pchip');
        pfdata.data.z(nan_rows, last_ind)=z;

        if pfdata.data.z(missing_row, last_ind)>0.7
            pfdata=fill_missing_row(pfdata, missing_row, last_ind+1);
        end
    end
    

end
