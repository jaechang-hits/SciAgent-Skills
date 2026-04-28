---
name: matlab-scientific-computing
description: "MATLAB/GNU Octave numerical computing: matrices, linear algebra, ODEs, signal processing, optimization, statistics, scientific visualization. MATLAB-syntax examples run on both. For Python use numpy/scipy; for statistical modeling use statsmodels."
license: "GPL-3.0 (GNU Octave); MATLAB requires commercial license"
---

# MATLAB/Octave — Scientific Computing

## Overview

MATLAB is a numerical computing environment optimized for matrix operations and scientific computing. GNU Octave is a free, open-source alternative with high compatibility. All code examples use MATLAB syntax that runs on both platforms.

## When to Use

- Performing matrix operations and linear algebra (eigenvalues, SVD, least squares)
- Solving ordinary and partial differential equations numerically
- Signal processing (FFT, filtering, spectral analysis)
- Creating 2D/3D scientific visualizations and publication figures
- Numerical optimization and root finding
- Statistical analysis and curve fitting
- Batch processing of experimental data files
- For **Python-based numerical computing**, use numpy/scipy instead
- For **statistical modeling with inference**, use statsmodels instead

## Prerequisites

```bash
# GNU Octave (free, open-source)
# macOS
brew install octave
# Ubuntu/Debian
sudo apt install octave

# Running scripts
octave script.m                           # Octave
matlab -nodisplay -nosplash -r "run('script.m'); exit;"  # MATLAB
```

**Note**: MATLAB requires a commercial license from MathWorks. GNU Octave is free and runs most MATLAB scripts without modification. Key Octave differences: supports `#` comments, `++`/`+=` operators; some MATLAB toolbox functions unavailable.

## Quick Start

```matlab
% Load data, fit, and plot
x = linspace(0, 2*pi, 100);
y = sin(x) + 0.1 * randn(size(x));
p = polyfit(x, y, 5);
y_fit = polyval(p, x);

figure;
plot(x, y, 'bo', x, y_fit, 'r-', 'LineWidth', 2);
xlabel('x'); ylabel('y');
legend('Data', 'Polynomial fit');
title('Curve Fitting Example');
saveas(gcf, 'fit_result.png');
```

## Core API

### 1. Matrix Operations

MATLAB operates fundamentally on matrices and arrays.

```matlab
% Create matrices
A = [1 2 3; 4 5 6; 7 8 9];    % 3x3 matrix
v = linspace(0, 1, 100);       % 100 evenly spaced points
I = eye(3);                     % Identity matrix
R = rand(3, 3);                 % Uniform random
N = randn(3, 3);                % Normal random

% Operations
B = A';                  % Transpose
C = A * B;               % Matrix multiplication
D = A .* B;              % Element-wise multiplication
x = A \ [1; 2; 3];      % Solve Ax = b (preferred over inv(A)*b)
fprintf('Solution: [%.2f, %.2f, %.2f]\n', x);
```

```matlab
% Indexing and manipulation
A = magic(5);
sub = A(1:3, 2:4);      % Submatrix (rows 1-3, cols 2-4)
row = A(2, :);           % Entire row 2
col = A(:, 3);           % Entire column 3
A(A < 5) = 0;           % Logical indexing

% Concatenation
C = [A; ones(1, 5)];    % Vertical (add row)
D = [A, zeros(5, 1)];   % Horizontal (add column)
fprintf('Size: %d x %d\n', size(C));
```

### 2. Linear Algebra

```matlab
A = [4 1 2; 1 3 1; 2 1 5];

% Eigendecomposition
[V, D] = eig(A);           % V: eigenvectors, D: diagonal eigenvalues
fprintf('Eigenvalues: %.2f, %.2f, %.2f\n', diag(D));

% Singular value decomposition
[U, S, V] = svd(A);
fprintf('Singular values: %.2f, %.2f, %.2f\n', diag(S));

% Matrix decompositions
[L, U, P] = lu(A);         % LU with pivoting
[Q, R] = qr(A);            % QR decomposition
R_chol = chol(A);           % Cholesky (symmetric positive definite)

% Condition number and rank
fprintf('Condition number: %.2f\n', cond(A));
fprintf('Rank: %d\n', rank(A));
```

### 3. Plotting and Visualization

```matlab
% 2D line plots
x = 0:0.1:2*pi;
figure;
plot(x, sin(x), 'b-', 'LineWidth', 2); hold on;
plot(x, cos(x), 'r--', 'LineWidth', 2);
xlabel('x'); ylabel('y');
title('Trigonometric Functions');
legend('sin(x)', 'cos(x)');
grid on;
saveas(gcf, 'trig.png');
```

```matlab
% 3D surface plot
[X, Y] = meshgrid(-2:0.1:2, -2:0.1:2);
Z = X.^2 + Y.^2;
figure;
surf(X, Y, Z);
colorbar; xlabel('X'); ylabel('Y'); zlabel('Z');
title('Paraboloid');
print('-dpdf', 'surface.pdf');
```

```matlab
% Multi-panel figure
figure;
subplot(2, 2, 1); plot(x, sin(x)); title('sin');
subplot(2, 2, 2); plot(x, cos(x)); title('cos');
subplot(2, 2, 3); bar([1 3 2 5 4]); title('Bar');
subplot(2, 2, 4); histogram(randn(1000, 1), 30); title('Histogram');
saveas(gcf, 'panels.png');
```

### 4. Data Import/Export

```matlab
% CSV / tabular data
T = readtable('data.csv');
M = readmatrix('data.csv');
fprintf('Table: %d rows x %d cols\n', height(T), width(T));

% Write data
writetable(T, 'output.csv');
writematrix(M, 'output.csv');

% MAT files (MATLAB native binary)
A = rand(100, 100);
save('data.mat', 'A');          % Save variable
S = load('data.mat', 'A');     % Load specific variable

% Images
img = imread('image.png');
fprintf('Image size: %d x %d x %d\n', size(img));
imwrite(img, 'output.jpg');
```

### 5. Statistics and Data Analysis

```matlab
data = randn(1000, 1) * 5 + 50;

% Descriptive statistics
fprintf('Mean: %.2f, Std: %.2f, Median: %.2f\n', mean(data), std(data), median(data));
fprintf('Min: %.2f, Max: %.2f\n', min(data), max(data));

% Correlation and covariance
X = randn(100, 3);
R = corrcoef(X);
fprintf('Correlation matrix:\n');
disp(R);

% Linear regression (polyfit)
x = (1:50)';
y = 2.5 * x + 10 + randn(50, 1) * 5;
p = polyfit(x, y, 1);
fprintf('Slope: %.2f, Intercept: %.2f\n', p(1), p(2));

% Moving statistics
y_smooth = movmean(y, 5);
```

### 6. Differential Equations

```matlab
% First-order ODE: dy/dt = -2y, y(0) = 1
f = @(t, y) -2 * y;
[t, y] = ode45(f, [0 5], 1);
figure; plot(t, y, 'b-', 'LineWidth', 2);
xlabel('Time'); ylabel('y(t)');
title('Exponential Decay');
fprintf('Final value: %.4f (expected: %.4f)\n', y(end), exp(-10));
```

```matlab
% Second-order ODE: y'' + 0.5y' + 4y = 0 (damped oscillator)
% Convert to system: y1' = y2, y2' = -0.5*y2 - 4*y1
f = @(t, y) [y(2); -0.5*y(2) - 4*y(1)];
[t, y] = ode45(f, [0 20], [1; 0]);
figure; plot(t, y(:,1), 'b-', 'LineWidth', 2);
xlabel('Time'); ylabel('Displacement');
title('Damped Oscillator');
```

### 7. Signal Processing

```matlab
% Generate signal with two frequencies
fs = 1000;                       % Sampling frequency
t = 0:1/fs:1-1/fs;
signal = sin(2*pi*50*t) + 0.5*sin(2*pi*120*t) + randn(size(t))*0.2;

% FFT
Y = fft(signal);
f = (0:length(Y)-1) * fs / length(Y);
figure;
plot(f(1:length(f)/2), abs(Y(1:length(Y)/2)));
xlabel('Frequency (Hz)'); ylabel('|FFT|');
title('Frequency Spectrum');
```

```matlab
% FIR low-pass filter (keep < 80 Hz)
b = fir1(50, 80/(fs/2));          % 50th order, cutoff 80 Hz
filtered = filter(b, 1, signal);
figure;
plot(t, signal, 'b', t, filtered, 'r', 'LineWidth', 1.5);
legend('Original', 'Filtered');
title('Low-pass Filtering');
```

### 8. Functions and Programming

```matlab
% Anonymous functions
f = @(x) x.^2 + 2*x + 1;
fprintf('f(5) = %d\n', f(5));   % 36

% Function files (save as myfunc.m)
% function [rmse, r2] = myfunc(y_true, y_pred)
%     residuals = y_true - y_pred;
%     rmse = sqrt(mean(residuals.^2));
%     ss_res = sum(residuals.^2);
%     ss_tot = sum((y_true - mean(y_true)).^2);
%     r2 = 1 - ss_res / ss_tot;
% end

% Struct for organized data
experiment.name = 'Trial 1';
experiment.data = rand(10, 3);
experiment.params = struct('temp', 37, 'pH', 7.4);
fprintf('Experiment: %s, %d samples\n', experiment.name, size(experiment.data, 1));
```

## Key Concepts

### Vectorization

MATLAB is optimized for vectorized operations. Avoid explicit loops when possible:

```matlab
% Slow (loop)
n = 1e6;
y = zeros(1, n);
tic;
for i = 1:n
    y(i) = sin(i/1000);
end
t_loop = toc;

% Fast (vectorized)
tic;
y = sin((1:n)/1000);
t_vec = toc;
fprintf('Loop: %.3fs, Vectorized: %.3fs, Speedup: %.1fx\n', t_loop, t_vec, t_loop/t_vec);
```

### Element-wise vs Matrix Operations

| Operator | Matrix | Element-wise |
|----------|--------|-------------|
| Multiply | `A * B` | `A .* B` |
| Divide | `A / B` (right div) | `A ./ B` |
| Power | `A ^ n` (matrix power) | `A .^ n` |

### ODE Solver Selection

| Solver | Order | When to Use |
|--------|-------|-------------|
| `ode45` | 4-5 | Default. Most non-stiff problems |
| `ode23` | 2-3 | Rough solutions, faster per step |
| `ode113` | variable | High-accuracy, expensive evaluations |
| `ode15s` | variable | Stiff problems (chemical kinetics, circuits) |
| `ode23s` | 2 | Stiff, moderate accuracy |

## Common Workflows

### Workflow: Data Analysis Pipeline

```matlab
% 1. Load data
data = readtable('experiment.csv');

% 2. Clean
data = rmmissing(data);
fprintf('After cleaning: %d rows\n', height(data));

% 3. Group analysis
groups = unique(data.Category);
results = table();
for i = 1:length(groups)
    mask = strcmp(data.Category, groups{i});
    subset = data(mask, :);
    row = table(groups(i), mean(subset.Value), std(subset.Value), ...
        'VariableNames', {'Category', 'Mean', 'Std'});
    results = [results; row];
end
disp(results);

% 4. Visualize and save
figure;
bar(categorical(results.Category), results.Mean);
hold on;
errorbar(1:height(results), results.Mean, results.Std, '.k');
ylabel('Mean Value'); title('Results by Category');
saveas(gcf, 'results.png');
writetable(results, 'summary.csv');
```

### Workflow: Numerical Simulation (Heat Equation)

```matlab
% 1D heat equation: du/dt = alpha * d2u/dx2
L = 1; N = 100; T_end = 0.5; alpha = 0.01;
dx = L / (N - 1);
dt = 0.4 * dx^2 / alpha;  % CFL condition
x = linspace(0, L, N);
nsteps = floor(T_end / dt);

% Initial condition: Gaussian pulse
u = exp(-50 * (x - 0.5).^2);

% Time stepping (explicit finite difference)
figure;
for step = 1:nsteps
    u_new = u;
    for i = 2:N-1
        u_new(i) = u(i) + alpha * dt / dx^2 * (u(i+1) - 2*u(i) + u(i-1));
    end
    u = u_new;
    if mod(step, floor(nsteps/5)) == 0
        plot(x, u, 'LineWidth', 1.5); hold on;
    end
end
xlabel('Position'); ylabel('Temperature');
title('Heat Equation Evolution');
legend(arrayfun(@(n) sprintf('t=%.2f', n*dt*floor(nsteps/5)), 1:5, 'UniformOutput', false));
saveas(gcf, 'heat_equation.png');
```

### Workflow: Batch File Processing

1. List files with `dir('data/*.csv')`
2. Loop through files, load each with `readtable()`
3. Apply analysis function to each file
4. Collect results into a summary table with `vertcat()`
5. Export summary with `writetable()`

## Key Parameters

| Parameter | Function | Default | Range | Effect |
|-----------|----------|---------|-------|--------|
| Order | `polyfit` | — | 1–20 | Polynomial degree for fitting |
| `tspan` | `ode45` | — | [t0, tf] | Integration time interval |
| `'LineWidth'` | `plot` | 0.5 | 0.1–5 | Line thickness in plots |
| `bins` | `histogram` | auto | 1–1000 | Number of histogram bins |
| Filter order | `fir1` | — | 10–200 | FIR filter order (higher = sharper) |
| `'RelTol'` | `ode45` | 1e-3 | 1e-12–1e-1 | Relative error tolerance |
| `'AbsTol'` | `ode45` | 1e-6 | 1e-15–1e-1 | Absolute error tolerance |

## Best Practices

1. **Always vectorize over loops**: MATLAB's JIT is good but vectorized code is 10-100x faster for large arrays. Use `bsxfun`, logical indexing, and array operations.

2. **Preallocate arrays**: Growing arrays in loops causes repeated memory allocation.
   ```matlab
   % Bad: y = []; for i=1:n, y = [y, f(i)]; end
   % Good:
   y = zeros(1, n);
   for i = 1:n, y(i) = f(i); end
   ```

3. **Use `\` instead of `inv()` for linear systems**: `A\b` is numerically more stable and faster than `inv(A)*b`.

4. **Anti-pattern — using `==` for floating-point comparison**: Use `abs(a - b) < tol` instead of `a == b` due to floating-point precision.

5. **Save figures in vector format for publications**: Use `print('-dpdf', 'fig.pdf')` or `print('-dsvg', 'fig.svg')` instead of PNG for scalable figures.

6. **Anti-pattern — mixing 0-indexed and 1-indexed logic**: MATLAB arrays start at 1. When porting from Python/C, adjust all indices.

7. **Use `fprintf` over `disp` for formatted output**: `fprintf` gives control over number formatting; `disp` only shows raw values.

## Common Recipes

### Recipe: Curve Fitting with Confidence Intervals

```matlab
x = (1:20)';
y = 3 * exp(-0.2 * x) + 0.5 * randn(size(x));

% Nonlinear fit using lsqcurvefit (Optimization Toolbox)
% Or use polyfit for polynomial:
p = polyfit(x, y, 3);
y_fit = polyval(p, x);
residuals = y - y_fit;
rmse = sqrt(mean(residuals.^2));
fprintf('RMSE: %.4f\n', rmse);

figure;
plot(x, y, 'ko', x, y_fit, 'r-', 'LineWidth', 2);
xlabel('x'); ylabel('y');
title(sprintf('Polynomial Fit (RMSE = %.3f)', rmse));
saveas(gcf, 'curvefit.png');
```

### Recipe: Image Processing Basics

```matlab
img = imread('sample.png');
gray = rgb2gray(img);

% Edge detection
edges = edge(gray, 'Canny');

% Display
figure;
subplot(1, 3, 1); imshow(img); title('Original');
subplot(1, 3, 2); imshow(gray); title('Grayscale');
subplot(1, 3, 3); imshow(edges); title('Edges');
saveas(gcf, 'image_processing.png');
```

### Recipe: Python Integration

```matlab
% Call Python from MATLAB (requires Python on PATH)
result = py.numpy.array([1, 2, 3, 4, 5]);
py_mean = py.numpy.mean(result);
fprintf('Python numpy mean: %.1f\n', double(py_mean));

% Call MATLAB from Python (requires matlab.engine)
% import matlab.engine
% eng = matlab.engine.start_matlab()
% result = eng.sqrt(42.0)
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `Undefined function or variable` | Function not on path or misspelled | Check `which funcname`; add path with `addpath()` |
| Dimension mismatch in `*` | Matrix sizes incompatible | Use `.*` for element-wise; check `size()` of both operands |
| ODE solver very slow | Stiff problem with non-stiff solver | Switch to `ode15s` or `ode23s` for stiff systems |
| `Singular matrix` warning | Matrix is rank-deficient | Check `cond(A)`; use `pinv()` (pseudo-inverse) or regularize |
| Octave `pkg` error | Package not installed | Run `pkg install -forge package_name; pkg load package_name` |
| Figure not saving | No `figure` handle active | Create figure explicitly with `figure;` before plotting |
| `Out of memory` | Large array allocation | Use sparse matrices (`sparse()`), process in chunks, or increase swap |

## Related Skills

- **statsmodels-statistical-modeling** — Python alternative for statistical modeling with inference tables
- **matplotlib-scientific-plotting** — Python plotting; use when working in Python ecosystem
- **scikit-learn-machine-learning** — Python ML; for classification/clustering tasks better suited to Python

## References

- [GNU Octave documentation](https://docs.octave.org/latest/) — official manual and function reference
- [MATLAB documentation](https://www.mathworks.com/help/matlab/) — MathWorks official reference
- [MATLAB–Octave compatibility](https://wiki.octave.org/FAQ#Differences_between_Octave_and_Matlab) — key syntax and feature differences
