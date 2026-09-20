CXX ?= g++
CXXFLAGS ?= -O3 -fPIC -Wall -Wextra -std=c++20
LDFLAGS ?= -shared

TARGET = libveles.so
SRCS = veles_engine.cpp
OBJS = $(SRCS:.cpp=.o)

all: $(TARGET) libaegis.so

$(TARGET): $(OBJS)
	$(CXX) $(LDFLAGS) -o $@ $^

libaegis.so: $(TARGET)
	ln -sf $(TARGET) $@

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS) $(TARGET) libaegis.so aegis_engine.o

.PHONY: all clean
