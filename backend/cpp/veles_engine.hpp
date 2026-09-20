#ifndef VELES_ENGINE_HPP
#define VELES_ENGINE_HPP

#include <cstddef>
#include <cstdint>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Veles Shield C++ High-Performance Anomaly & Entropy Engine
 * 
 * Provides sub-microsecond calculation of:
 * 1. Shannon Entropy for string token randomness (synthetic identity detection)
 * 2. Character class distribution (vowel/consonant/digit/special ratio)
 * 3. Exponentially Weighted Moving Average (EWMA) anomaly deviation
 * 4. Verhoeff checksum algorithm for Aadhaar identity validation
 */

// Calculate Shannon entropy of a null-terminated UTF-8 / ASCII string.
// Output range: 0.0 (uniform characters) to ~8.0 (high randomness/entropy).
double veles_calculate_shannon_entropy(const char* text, size_t length);

// Calculate synthetic identity risk score (0.0 to 1.0) based on:
// - Shannon entropy anomaly
// - Consecutive consonant/digit clusters (keyboard smash)
// - Repetition ratios
double veles_calculate_name_anomaly(const char* name, size_t length);

// Calculate EWMA anomaly score given current transaction amount, historical mean, and variance
// Output: Z-score or normalized anomaly index (0.0 to 1.0)
double veles_calculate_ewma_deviation(double current_val, double ewma_mean, double ewma_var, double alpha);

// Validate Indian Aadhaar 12-digit number using the Verhoeff algorithm
// Returns 1 if valid, 0 if invalid
int veles_validate_verhoeff(const char* num_str);

// High-speed n-gram character transition irregularity
double veles_calculate_bigram_perplexity(const char* text, size_t length);

#ifdef __cplusplus
}
#endif

#endif // VELES_ENGINE_HPP
