#include <iostream>
#include <stdint.h>
#include <fstream>  // For file operations
#include <cstring>  // For string handling
#include <algorithm> // For std::fill

extern "C" {

void ml_data_generator(int day,
                       int16_t* prev,
                       int16_t* cur,
                       double* max_drop,
                       int16_t* prodes_data,
                       int16_t* gfc_data,
                       double* prodes_geotransform,
                       double* appears_geotransform,
                       int prodes_height,
                       int prodes_width,
                       int cur_height,
                       int cur_width,
                       const char* prodes_output_path,
                       const char* gfc_output_path,
                       int eco_top_right_x,
                       int eco_bottom_left_y,
                       int eco_top_left_x,
                       int eco_top_left_y
                       ) {

        // Thank goodness for C++ :)

        std::cout << "Before program!" << std::endl;
        std::cout << "day: " << day << std::endl;
        std::cout << "prodes_height: " << prodes_height << std::endl;
        std::cout << "prodes_width: " << prodes_width << std::endl;
        std::cout << "cur_height: " << cur_height << std::endl;
        std::cout << "cur_width: " << cur_width << std::endl;
        std::cout << "eco_top_right_x:" << eco_top_right_x << std::endl;
        std::cout << "eco_bottom_left_y:" << eco_bottom_left_y << std::endl;

        // Open CSV files for append
        std::ofstream prodes_output_file(prodes_output_path, std::ios::app);
        std::ofstream gfc_output_file(gfc_output_path, std::ios::app);

        // Check if files are opened successfully
        if (!prodes_output_file.is_open() || !gfc_output_file.is_open()) {
                std::cerr << "Error opening CSV files for append." << std::endl;
                return;
        }

        // Generate ML data
        int* prodes_deforestation = new int[cur_height * cur_width];
        int* gfc_deforestation = new int[cur_height * cur_width];

        // Initialize the deforestation to all zeros
        std::fill(prodes_deforestation, prodes_deforestation + cur_height * cur_width, 0);
        std::fill(gfc_deforestation, gfc_deforestation + cur_height * cur_width, 0);

        std::cout << day << std::endl;

        for (int i = 0; i < prodes_height; ++i) {
                for (int j = 0; j < prodes_width; ++j) {
                        long long index = static_cast<long long>(i * prodes_width) + j;

                        // Need to convert i,j to lat,lon
                        double lon = prodes_geotransform[0] + (i * prodes_geotransform[1]);
                        double lat = prodes_geotransform[3] + (j * prodes_geotransform[5]);

                        std::cout << "lat: " << lat << std::endl;
                        std::cout<< "lon: " << lon << std::endl;

                        // int x_pixel = (static_cast<int>((lon - appears_geotransform[0])/appears_geotransform[1])) - eco_top_left_x;
                        // int y_pixel = (static_cast<int>((lat - appears_geotransform[3])/appears_geotransform[5])) - eco_top_left_y;
                        int x_pixel = (static_cast<int>((lon - appears_geotransform[0])/appears_geotransform[1])) - eco_top_left_x;
                        int y_pixel = (static_cast<int>((lat - appears_geotransform[3])/appears_geotransform[5])) - eco_top_left_y;

                        std::cout << "x_pixel:" << x_pixel << std::endl;
                        //std::cout << "cur_max_width:" << cur_max_width << std::endl;
                        std::cout << "y_pixel:" << y_pixel << std::endl;

                        
                        //std::cout << "cur_max_height:" << cur_max_height << std::endl;
                        //std::cout << "prodes_data[index]:" << prodes_data[index] << std::endl;



                        if (x_pixel >= 0 && x_pixel < eco_top_right_x && y_pixel >= 0 && y_pixel < eco_bottom_left_y && (prodes_data[index] == 1 || prodes_data[index] == 0)){
                                int cur_index = x_pixel * cur_width + y_pixel;

                                if (prodes_data[index] == 1) {
                                        prodes_deforestation[cur_index] = 1;
                                }

                                if (gfc_data[index] == 1) {
                                        gfc_deforestation[cur_index] = 1;
                                }

                                double difference = static_cast<double>(cur[cur_index] - prev[cur_index]);
                                
                                // std::cout << "We in here!" << std::endl;

                                if (max_drop[cur_index] > difference) {
                                        max_drop[cur_index] = difference;
                                        std::cout << "Difference: " << difference << ", max_drop[cur_index]: " << max_drop[cur_index] << ", cur_index: " << cur_index << std::endl;
                                }
                                // std::cout << "We in here!" << std::endl;
                                if (day == 353) {
                                        // std::cout << "Its day 353!" << std::endl;
                                        // write to prodes_output_file (difference, prodes_deforestation[cur_index])
                                        prodes_output_file << max_drop[cur_index] << "," << prodes_deforestation[cur_index] << "\n";
                                        // std::cout<< max_drop[cur_index] << "," << prodes_deforestation[cur_index] << std::endl;
                                        // write to gfc_output_file (difference, gfc_deforestation[cur_index])
                                        gfc_output_file << max_drop[cur_index] << "," << gfc_deforestation[cur_index] << "\n";
                                        // std::cout<< max_drop[cur_index] << "," << gfc_deforestation[cur_index] << std::endl;
                                }                               
                        }
                        
                }
                
        }

        // Closing CSV files
        prodes_output_file.close();
        gfc_output_file.close();

        delete[] prodes_deforestation;
        delete[] gfc_deforestation;

}

}