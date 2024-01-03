#include <iostream>

extern "C" {

void sub_arrays(const int16_t* array1, const int16_t* array2, float* array3, int rows, int cols) {
    for (int i = 0; i < rows; ++i) {
        for (int j = 0; j < cols; ++j) {
            int index = i * cols + j;
            // double val = array2[index] - array1[index];
            
            // Convert int16_t to float32 before subtraction
            float val1 = static_cast<float>(array1[index]);
            float val2 = static_cast<float>(array2[index]);

            // Perform subtraction in float32
            float val = val2 - val1;

            // Replace only if the value is less than what was currently at array3[index]
            if (val < array3[index] && array2[index] != -3000) {
                array3[index] = val;
            }
        }
    }
}

}

