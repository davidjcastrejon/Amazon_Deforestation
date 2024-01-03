#include <iostream>
#include <iterator>
#include <vector>
#include <fstream>
#include <unistd.h>
using namespace std;

void evi(unsigned short* rgb,short value) {
	if(value == -3000) {
		rgb[0] = 0;
		rgb[1] = 0;
		rgb[2] = 0;
		return;
	}
	value = ((value+2000)*239)>>13;
	if(value > 255) {
		rgb[0] = 0;
		rgb[1] = 255;
		rgb[2] = 0;
		return;
	}
	rgb[0] = 255-value;
	rgb[1] = value;
	rgb[2] = 0;
}

int main() {	
	short value;
	unsigned short greyscale[3];
	while(fread(&value, sizeof value, 1, stdin) == 1) {
		evi_to_greyscale(greyscale, value);
		fwrite(&greyscale, sizeof greyscale[0], 3, stdout);
	}
	return 0;
}

