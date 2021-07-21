function out = xyz2spz(xyz_data,site)

%Function to transform (x,y,z) coordinates on an embayed beach to alongshore - cross-shore
%coordinates (s,p,z) using the log spiral, given by the equation  
%r = r0*exp(A*theta). A = cot(alpha).
%
%xyz_data is a structure containing:
%
%xyz_data.x
%xyz_data.y
%xyz_data.z
%
%Refer to paper
%
%Harley, M.D. and Turner,I.L. (2007) A simple data transformation technique
%for pre-processing survey data at embayed beaches, Coast. Eng.,
%doi:10.1016/j.coastaleng.2007.07.001, in press.
%
%Created by Mitch Harley
%8th August, 2005
%Last Modified 7th April, 2009

% V1.1 - Joshua Simmons 05/2017
%added support for grid inputs
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

%DO TRANSFORMATION

%JAS 04/05/2017 - First lets deal with any 2d input
reshapebool = 0;
sz = size(xyz_data.x);
if ~(sz(1) == 1) && ~(sz(2) == 1)
    reshapebool = 1;
    xyz_data.x = xyz_data.x(:);
    xyz_data.y = xyz_data.y(:);
end

%MDH 07/07/2016 First, sort data so that unwrap function works properly 
[sorted_x, id_sort] = sort(xyz_data.x); %Sorth data by northings (most suited to north-south oriented beaches)
sorted_y = xyz_data.y(id_sort);

%Convert xyz coordinates to polar coordinates
r = sqrt((sorted_x - origin(1)).^2+(sorted_y - origin(2)).^2);
theta = unwrap(atan2((sorted_y-origin(2)),(sorted_x-origin(1))) );
I = find(theta<0);
if ~isempty(I)
    percentage = length(I)/length(theta)*100;
    disp(['Warning: ' num2str(percentage,'%0.0f') '% of data points have a negative theta. Could result in anomalous solution'])
end

if exist('WAMBE','var')==1
    theta(theta<0) = theta(theta<0)+2*pi; %MDH 2015/09/03 Fix problem with Wanda data that wants to find solution of smaller logspiral
end

if exist('HARG','var')||exist('HARG','var')
    theta(theta>0) = theta(theta>0)-2*pi; %MDH 2015/09/03 Fix problem with Wanda data that wants to find solution of smaller logspiral
end


%Find constants delta and kappa
delta = pi/2+acot(A)-theta; %From Equation 5
kappa = r./(r0_origin*sin(pi/2-acot(A))); %From Equation 6

%Find theta_s by solving implicitly using fzero function
for i = 1:length(theta);
    %Use muller function in case any complex solutions
    theta_s(i,1) = muller(@(x) (x-(1/A)*log(kappa(i)*sin(delta(i)+x))),[theta(i)-pi/8 theta(i) theta(i)+pi/8]);%From Equation 6
end

%Find r_s
r_s = r0_origin*exp(A*theta_s);%From Equation 1

%Find s
lamda = r0_origin*sec(acot(A));%From Equation 8
start_point =  0; %Can be changed to make a more suitable start point
s = lamda*(exp(A*theta_s)-exp(A*start_point));%From Equation 8

%Find p
p = r.*sin(theta-theta_s)./sin(pi/2-acot(A)); %From Equation 9

%Convert any complex numbers to real numbers
p = real(p);
s = real(s);

%-----------------------------------------------------------------
%POST-PROCESS DATA
%s data

if site.reverse_s ==0
    s = s - site.startpoint;%Make minimum s == 0
elseif site.reverse_s ==1
    s = -(s - site.startpoint);
end

%p data
if site.subtract_res ==1 %Add switch for user to subtract residuals or not - MDH 19/5/2010
[MIN,L] = min(site.boundary.s);
I = find(s<=MIN);
p(I) = p(I) - site.boundary.p(L);
[MAX,L] = max(site.boundary.s);
I = find(s>=MAX);
p(I) = p(I) - site.boundary.p(L);
I = find(s>MIN&s<MAX);
p(I) = p(I) - interp1(site.boundary.s,site.boundary.p,s(I));%Subtract logspiral errors from p data
end


if site.alpha<0
   p = -p;
end

%Sort data back
[dummy, id_rev] = sort(id_sort); 
unsorted_s = s(id_rev);
unsorted_p = p(id_rev);

%-----------------------------------------------------------------
%JAS 04/05/2017 - Now just convert it back into shape after all the hard
%work is done!
if reshapebool
    unsorted_s = reshape(unsorted_s,sz);
    unsorted_p = reshape(unsorted_p,sz);
end

out.s = unsorted_s;
out.p = unsorted_p;
out.z = xyz_data.z;
