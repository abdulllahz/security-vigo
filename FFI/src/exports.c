#include <stdio.h>

// Exponential time function to calculate the exponentiation of a number
int exponential_time(int base,int exponent) {
    if (exponent == 0) {
        return 1; // Base case: any number raised to the power of 0 is 1
    } else {
        // Recursive case: multiply the base by itself recursively
        return base * exponential_time(base, exponent - 1);
    }
}

int sum(int a,int b){
	return a+b;
}