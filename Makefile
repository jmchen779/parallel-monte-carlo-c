FORMULA ?= 3*(x)*(x)

integrate: main.o monte_carlo.o 
	gcc-15 -fopenmp -O2 -o integrate main.o monte_carlo.o -lm $(shell gsl-config --libs) -D'CUSTOM_FORMULA(x)=($(FORMULA))'

main.o: src/main.c
	gcc-15 -fopenmp -O2 $(shell gsl-config --cflags) -D'CUSTOM_FORMULA(x)=($(FORMULA))' -c src/main.c

monte_carlo.o: src/monte_carlo.c
	gcc-15 -fopenmp -O2 $(shell gsl-config --cflags) -D'CUSTOM_FORMULA(x)=($(FORMULA))' -c src/monte_carlo.c

clean:
	-rm -f integrate *.o

run: integrate
	./integrate 160000000 8 0 1

