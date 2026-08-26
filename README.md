# parallel-monte-carlo-c

```
Monte Carlo Integration Version 1.0
```

# Introduction
Monte Carlo Integration is a numerical integration scheme that uses random number generation to estimate the area under a curve. It does this by randomly picking a point in a predetermined region, determining if that point lies above or below the curve, and computing the fraction of points above/below the curve. Monte Carlo integration's error scales with 1 / sqrt(N), where N is the number of randomly generated points. This is worse scaling than other integration schemes, however Monte Carlo integration is one of the only ways to numerically integrate in multiple dimensions. Additionally, this implementation has been parallelized with OpenMP, allowing for significantly faster performance.

# Installation and Running the Code
To install the code, you do
```
git clone https://github.com/jmchen779/parallel-monte-carlo-c
make clean 
make
```

Currently the code only compiles on gcc. You may need to install gsl if you haven't done so already.

The default integrand is 3x^2. You may feel the need to integrate a custom function, in which case you can pass a custom function in by
```
make clean
make FORMULA="Your function here"
```
Any function using standard operations or in the math library is supported. For example, to integrate pi^sin(x)
from 0 to 1
```
make clean
make FORMULA="pow(M_PI, sin(x))"
make run
```
Using ```make run``` will run the program on default settings, which is 160000000 points, 8 threads, and an integration range of 0 to 1.

You can also run the code on custom settings using
```
./integrate N k lower_bound upper_bound seed max min
```
```N``` is the number of points used to estimate the area, ```k``` is the number of OpenMp threads used in the calculation, ```lower_bound``` and ```upper_bound``` are the lower and upper bounds of integration, respectively. ```seed``` is an optional parameter that allows you to specify a custom seed for the random number generator. The seed should be a positive integer. If no seed is supplied, a random seed will be generated. ```max``` and ```min``` are optional parameters that allow you to specify the maximum and mininum of your function. If these are provided, the program will save time by not computing the max and min. 

For example, to run a program with 10000 samples on 4 threads with an integration range of -10 10, a seed of 123456789, and the integrand maximum and minimum are 3 and -3 you would do
```
./integrate 10000 4 -10 10 123456789 3 -3
```

# Performance and Scaling Benchmarks
Coming soon