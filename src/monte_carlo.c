#include "../include/montecarlo_integrations.h"
#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#include <math.h>
#include <string.h>
#include <gsl/gsl_rng.h>
#include <float.h>



//the integrand
double integrand(double x){
    //update this line with function fo your choice
    return CUSTOM_FORMULA(x);
}

//function that computes min and max of our previously defined function. Takes pointers to variables holding min/max
void compute_min_max(double* min, double* max, double x_start, double x_end, int k){
    //step is dx, steps is number of times we evauluate function on interval [a, b]
        double max_value = *(max);
        double min_value = *(min);
        max_value = -DBL_MAX;
        min_value = DBL_MAX;
        double dx = 1e-3;
        int steps = (int)((x_end - x_start) / dx);
        printf("Steps: %d\n", steps);
        int i;
        #pragma omp parallel num_threads(k) shared(dx, steps) private(i) reduction(max:max_value) reduction(min:min_value)
        {
        #pragma omp for schedule(static, 2)
        for (i=0; i < steps+1; i++){
            double x_val = x_start + (double)i*dx;
            if (i == steps){
                x_val = x_end;
            }
            double val = integrand(x_val);
            if ( val > max_value){
                max_value = val;
            }
            if (val < min_value){
                min_value = val;
            }
        }
        }

        *(max) = max_value;
        *(min) = min_value;
}
//function to integrate function. Returns the fraction of darts which landed beneath the function 
//subtracts negative from positive counts 
double integrate(double x_start, double x_end, double ymin, double ymax, int N, int k, int seed){
    int count_pos, count_neg, i;
    count_pos =0;
    count_neg = 0;
    double range = x_end - x_start;
    #pragma omp parallel num_threads(k) shared(x_start, x_end, N, range) private(i) reduction(+:count_pos, count_neg)
    {
    //initilize the generator
    gsl_rng *generator;
    generator = gsl_rng_alloc(gsl_rng_mt19937);
    gsl_rng_set(generator, seed + omp_get_thread_num());
    #pragma omp for schedule(static, 2)
    for (i = 0; i < N; i++){
        double rand_x = (range)*(gsl_rng_uniform(generator)) + x_start; 
        double rand_y = (ymax - ymin)*(gsl_rng_uniform(generator) ) + ymin; 
        double y_value = integrand(rand_x);
        //check if random value is positive and between 0 and y value
        if ((rand_y < y_value) && (rand_y > 0)){
            count_pos++;
        }
        //check if random value is negative and between 0 and y value
        if ((rand_y > y_value) && (rand_y < 0)){
            count_neg++;
        }
    }
    gsl_rng_free(generator);
}
    printf("Positive count: %d\n", count_pos);
    printf("Negative count: %d\n", count_neg);
    double val = (double)(count_pos - count_neg) / N;
    printf("Fractional integral: %.6lf\n", val);
    return val;
}