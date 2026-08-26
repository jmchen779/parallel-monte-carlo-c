#include "../include/montecarlo_integrations.h"
#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#include <math.h>
#include <string.h>
#include <gsl/gsl_rng.h>
#include <time.h>
#include <float.h>


// a program for monte carlo integration. The program takes the command line arguments
// N (number of random samples), the lower end of integration range, the upper end of integration range,
// an optional seed paramter and an optionl max of the function parameter
int main(int argc, char *argv[]){
    double t0 = omp_get_wtime();
    unsigned long int seed = 0;
    //read in the arguments
    int argi = 0;
    int N = atoi(argv[++argi]);     printf("N = %d\n", N);
    int k = atoi(argv[++argi]);     printf("Number of Threads: %d\n", k);
    double x_start = atof(argv[++argi]);     printf("Lower bound = %.6lf\n", x_start);
    double x_end = atof(argv[++argi]);     printf("Upper bound = %.6lf\n", x_end);
    if (argi < argc -1){
        //read in an unsigned long int
        unsigned long int var_seed = strtoul((argv[++argi]), NULL, 10);
        seed = (unsigned long int)var_seed;
    }
    else {
        srand48((long int)time(NULL));
        long int temp_seed = lrand48();
        seed = (unsigned long int)temp_seed;
    }
    printf("Seed=%lu\n", seed);
    double max_value;
    int max_supplied; 
    if (argi < argc -1){
        max_value = atof(argv[++argi]);
        max_supplied =1;
    }
    else {
        max_supplied = 0;
    }
    double min_value;
    int min_supplied; 
    if (argi < argc -1){
        min_value = atof(argv[++argi]);
        min_supplied =1;
    }
    else {
        min_supplied = 0;
    }
    //if min and max are not supplied, discretize the function and find the max and min
    if ((min_supplied == 0) || (max_supplied == 0) ){
        compute_min_max(&min_value, &max_value, x_start, x_end, k);
    }
    printf("Max = %.6lf and Min = %.6lf\n", max_value, min_value);
    
    //additional integration logic
    if ((min_value > 0) && (max_value > 0)){
        min_value = 0;
    }
    if ((min_value < 0) && (max_value < 0)){
        max_value = 0;
    }
    //compute percentage of points thta land under curve
    double integral = integrate(x_start, x_end, min_value, max_value, N, k, seed);
    //rescale to integration region
    integral = integral*((x_end - x_start) * (max_value - min_value));
    printf("The integral value is: %.6lf\n", integral);
    double t_end = omp_get_wtime();
    printf("Time to Complete: %.6lf\n", t_end - t0);
    return 0;
}
