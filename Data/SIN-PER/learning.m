clc; close all;
A = magic(4);
A(2,2);
A(3,:);
A(:,end);

% filename = 'AppropriateFileName.csv'
% T = readtable(filename);
% G = findgroups(T{:,1});     %first column
% Tc = splitapply( @(varargin) varargin, T, G);

plot(A)
print