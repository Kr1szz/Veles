CXX ?= g++
CXXFLAGS ?= -O3 -fPIC -Wall -Wextra -std=c++20
LDFLAGS ?= -shared

TARGET = libaegis.so
SRCS = aegis_engine.cpp
OBJS = $(SRCS:.cpp=.o)

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) $(LDFLAGS) -o $@ $^

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS) $(TARGET)

.PHONY: all clean
