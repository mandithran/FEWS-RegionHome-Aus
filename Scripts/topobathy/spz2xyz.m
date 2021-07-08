function out = spz2xyz(spz_data,site);

%function out = spz2xyz(spz_data)
%
%Function to transform alongshore - cross-shore coordinates (s,p,z) on an
%embayed beach back to original coordinates (x,y,z) using the log spiral, given by the equation  
%r = r0*exp(A*theta). A = cot(alpha).
%
%spz_data is a structure containing:
%
%spz_data.s
%spz_data.p
%spz_data.z
%
%Refer to paper
%
%Harley, M.D. and Turner,I.L. (2008) A simple data transformation technique
%for pre-processing survey data at embayed beaches, Coast. Eng.,
%doi:10.1016/j.coastaleng.2007.07.001
%
%Created by Mitch Harley
%8th August, 2005
%Last Modified 7th April, 2009


%----------------------------------------------------------------
%LOAD LOGSPIRAL-FIT PARAMETERS

eval(['load ' site ';'])
eval(['site = ' site ';'])


%Define origin and A of log spiral
origin = site.origin;
alph = site.alpha; 
A = cot(alph*pi/180);
r0_origin = site.r0_origin;

%-----------------------------------------------------------------

%PRE-PROCESS DATA

%p data
if alph<0 %Deal with problem when alpha is negative
    spz_data.p = -spz_data.p;
end

if site.subtract_res ==1 %Add switch for user to subtract residuals or not - MDH 19/5/2010
[MIN,L] = min(site.boundary.s);
I = find(spz_data.s<=MIN);
spz_data.p(I) = spz_data.p(I) + site.boundary.p(L);
[MAX,L] = max(site.boundary.s);
I = find(spz_data.s>=MAX);
spz_data.p(I) = spz_data.p(I) + site.boundary.p(L);
I = find(spz_data.s>MIN&spz_data.s<MAX);
spz_data.p(I) = spz_data.p(I) + interp1(site.boundary.s,site.boundary.p,spz_data.s(I));%Subtract logspiral errors from p data
end

%s data
if site.reverse_s ==0
    spz_data.s = spz_data.s + site.startpoint;%Make minimum s == 0
elseif site.reverse_s ==1
    spz_data.s = site.startpoint-spz_data.s;
end

%-----------------------------------------------------------------

%DO BACK-TRANSFORMATION

%Calculate constants Beta and lamda

beta = ones(size(spz_data.s))*(pi/2 - acot(A));
lamda = r0_origin*sec(acot(A)); %From Equation 8

%Find angles theta_s given s
start_point = 0;
theta_s = log(spz_data.s/lamda + exp(A*start_point))/A;%From Equation 10

%Find distances from origin on spiral given theta_s
r_s = r0_origin*exp(A*theta_s); %From Equation 1

%Find distances from origin for points given s
r = sqrt(spz_data.p.^2+r_s.^2 - 2*r_s.*spz_data.p.*cos(beta)); %From Equation 11

%Find angles from origin

theta = asin(spz_data.p./r.*sin(beta))+theta_s;%From Equation 12

%Convert (r,theta) back to xyz coordinates
%x = origin(1)-r.*sin(theta); %From Equation 13
%y = origin(2)-r.*cos(theta); %From Equation 14
x = origin(1)+r.*cos(theta); %From Equation 13
y = origin(2)+r.*sin(theta); %From Equation 14

%-----------------------------------------------------------------

%POST-PROCESS DATA

% %Deal with any rotation
% if site.rotation.angle~=0
%     or = site.rotation.origin;
%     points_rotated = [reshape(x,size(x,1)*size(x,2),1) reshape(y,size(y,1)*size(y,2),1)]; %Deal with data in grid format - MDH 20/5/2010
%     points_rotated = points_rotated - repmat(or,length(points_rotated),1);
%     points_unrotated = points_rotated*[cos(-site.rotation.angle) -sin(-site.rotation.angle);sin(-site.rotation.angle) cos(-site.rotation.angle)];
%     points_new = points_unrotated + repmat(or,length(points_unrotated),1);
%     x = reshape(points_new(:,1),size(x,1),size(x,2)); %Convert back to original grid form
%     y = reshape(points_new(:,2),size(y,1),size(y,2));
% end
% 
% 
% %Deal with any horizontal or vertical flips
% if site.fliphor == 1
%     x = -x;
% end
% if site.flipver == 1
%     y = -y;
% end

%Address any negative alphas
%if site.alpha < 0
%    y = -y;
%end
%-----------------------------------------------------------------


out.x = x;
out.y = y;
out.z = spz_data.z;