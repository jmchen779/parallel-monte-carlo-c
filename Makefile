integrate: main.o monte_carlo.o
	gcc-15 -fopenmp -O2 -o integrate main.o monte_carlo.o -lm $(shell gsl-config --libs)

main.o: src/main.c
	gcc-15 -fopenmp -O2 $(shell gsl-config --cflags) -c src/main.c

monte_carlo.o: src/monte_carlo.c
	gcc-15 -fopenmp -O2 $(shell gsl-config --cflags) -c src/monte_carlo.c

clean:
	-rm -f integrate *.o

run: integrate
	./integrate 160000000 0 1