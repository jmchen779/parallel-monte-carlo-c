#ifndef MONTECARLO_INTEGRATIONS_H
#define  MONTECARLO_INTEGRATIONS_H

//custom formula for our script, we can change this or change it when we compile
#ifndef CUSTOM_FORMULA
#define CUSTOM_FORMULA(x)((x)*(x))
#endif

double integrand(double x);
void compute_min_max(double* min_value, double* max_value,  double x_start, double x_end, int k);
double integrate(double x_start, double x_end, double ymin, double ymax, int N, int k, int seed);

#endif