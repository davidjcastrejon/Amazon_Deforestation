# Optimization level. Change this -O2 to -Og or -O0 or whatever,
OPTIMIZE = -O3

CC = g++
CFLAGS = $(OPTIMIZE) -g3 -Wall -Wextra -fopenmp
SANITIZERS = -fsanitize=address -fsanitize=undefined

default: process

process: process_images.cpp
	$(CC) $(CFLAGS) $(SANITIZERS) $^ -o $@
