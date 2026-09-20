#include "veles_engine.hpp"
#include <cmath>
#include <cctype>
#include <cstring>
#include <algorithm>
#include <array>

// Verhoeff algorithm multiplication and permutation tables
static const uint8_t verhoeff_d[10][10] = {
    {0, 1, 2, 3, 4, 5, 6, 7, 8, 9},
    {1, 2, 3, 4, 0, 6, 7, 8, 9, 5},
    {2, 3, 4, 0, 1, 7, 8, 9, 5, 6},
    {3, 4, 0, 1, 2, 8, 9, 5, 6, 7},
    {4, 0, 1, 2, 3, 9, 5, 6, 7, 8},
    {5, 9, 8, 7, 6, 0, 4, 3, 2, 1},
    {6, 5, 9, 8, 7, 1, 0, 4, 3, 2},
    {7, 6, 5, 9, 8, 2, 1, 0, 4, 3},
    {8, 7, 6, 5, 9, 3, 2, 1, 0, 4},
    {9, 8, 7, 6, 5, 4, 3, 2, 1, 0}
};

static const uint8_t verhoeff_p[8][10] = {
    {0, 1, 2, 3, 4, 5, 6, 7, 8, 9},
    {1, 5, 7, 6, 2, 8, 3, 0, 9, 4},
    {5, 8, 0, 3, 7, 9, 6, 1, 4, 2},
    {8, 9, 1, 6, 0, 4, 3, 5, 2, 7},
    {9, 4, 5, 3, 1, 2, 6, 8, 7, 0},
    {4, 2, 8, 6, 5, 7, 3, 9, 0, 1},
    {2, 7, 9, 3, 8, 0, 6, 4, 1, 5},
    {7, 0, 4, 6, 9, 1, 3, 2, 5, 8}
};

extern "C" {

double veles_calculate_shannon_entropy(const char* text, size_t length) {
    if (!text || length == 0) {
        return 0.0;
    }

    std::array<size_t, 256> freq{};
    size_t count = 0;

    for (size_t i = 0; i < length; ++i) {
        unsigned char c = static_cast<unsigned char>(text[i]);
        if (c > 32) {
            freq[c]++;
            count++;
        }
    }

    if (count <= 1) {
        return 0.0;
    }

    double entropy = 0.0;
    double inv_count = 1.0 / static_cast<double>(count);

    for (size_t f : freq) {
        if (f > 0) {
            double p = static_cast<double>(f) * inv_count;
            entropy -= p * std::log2(p);
        }
    }

    return entropy;
}

double veles_calculate_name_anomaly(const char* name, size_t length) {
    if (!name || length == 0) {
        return 1.0;
    }

    size_t alpha_count = 0;
    size_t vowel_count = 0;
    size_t consonant_count = 0;
    size_t digit_count = 0;
    size_t max_consecutive_consonants = 0;
    size_t current_consecutive_consonants = 0;
    size_t max_char_repeat = 1;
    size_t current_char_repeat = 1;
    char prev_char = 0;

    for (size_t i = 0; i < length; ++i) {
        char ch = name[i];
        if (ch == ' ' || ch == '-' || ch == '\'') {
            current_consecutive_consonants = 0;
            current_char_repeat = 1;
            prev_char = ch;
            continue;
        }

        if (std::isdigit(static_cast<unsigned char>(ch))) {
            digit_count++;
            current_consecutive_consonants = 0;
        } else if (std::isalpha(static_cast<unsigned char>(ch))) {
            alpha_count++;
            char lower = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
            if (lower == 'a' || lower == 'e' || lower == 'i' || lower == 'o' || lower == 'u') {
                vowel_count++;
                current_consecutive_consonants = 0;
            } else {
                consonant_count++;
                current_consecutive_consonants++;
                if (current_consecutive_consonants > max_consecutive_consonants) {
                    max_consecutive_consonants = current_consecutive_consonants;
                }
            }
        }

        if (ch == prev_char) {
            current_char_repeat++;
            if (current_char_repeat > max_char_repeat) {
                max_char_repeat = current_char_repeat;
            }
        } else {
            current_char_repeat = 1;
        }
        prev_char = ch;
    }

    (void)consonant_count;
    double risk = 0.0;

    if (digit_count > 0) {
        risk += 0.45;
    }

    if (max_consecutive_consonants >= 5) {
        risk += 0.40;
    } else if (max_consecutive_consonants == 4) {
        risk += 0.15;
    }

    if (max_char_repeat >= 4) {
        risk += 0.35;
    } else if (max_char_repeat == 3) {
        risk += 0.10;
    }

    if (alpha_count >= 4) {
        double vowel_ratio = static_cast<double>(vowel_count) / static_cast<double>(alpha_count);
        if (vowel_ratio < 0.10) {
            risk += 0.30;
        } else if (vowel_ratio > 0.85) {
            risk += 0.25;
        }
    }

    double entropy = veles_calculate_shannon_entropy(name, length);
    if (length > 6 && entropy > 4.2) {
        risk += 0.20;
    } else if (length > 4 && entropy < 1.2) {
        risk += 0.30;
    }

    if (risk > 1.0) risk = 1.0;
    return risk;
}

double veles_calculate_ewma_deviation(double current_val, double ewma_mean, double ewma_var, double alpha) {
    (void)alpha;
    if (ewma_mean <= 0.0) {
        return 0.0;
    }

    double variance = ewma_var;
    if (variance < 1.0) {
        double default_sd = ewma_mean * 0.15;
        variance = default_sd * default_sd;
    }

    double std_dev = std::sqrt(variance);
    if (std_dev < 0.001) std_dev = 0.001;

    double diff = current_val - ewma_mean;
    double z_score = diff / std_dev;

    if (z_score <= 1.0) {
        return 0.0;
    }

    double risk = 1.0 / (1.0 + std::exp(-(z_score - 3.0)));
    return (risk > 1.0) ? 1.0 : (risk < 0.0 ? 0.0 : risk);
}

int veles_validate_verhoeff(const char* num_str) {
    if (!num_str) return 0;
    size_t len = std::strlen(num_str);
    if (len != 12) return 0;

    int c = 0;
    for (size_t i = 0; i < len; ++i) {
        char ch = num_str[len - 1 - i];
        if (!std::isdigit(static_cast<unsigned char>(ch))) {
            return 0;
        }
        int digit = ch - '0';
        c = verhoeff_d[c][verhoeff_p[i % 8][digit]];
    }

    return (c == 0) ? 1 : 0;
}

double veles_calculate_bigram_perplexity(const char* text, size_t length) {
    if (!text || length < 2) return 0.0;

    size_t rare_transitions = 0;
    size_t total_transitions = 0;

    for (size_t i = 0; i < length - 1; ++i) {
        unsigned char c1 = std::tolower(static_cast<unsigned char>(text[i]));
        unsigned char c2 = std::tolower(static_cast<unsigned char>(text[i + 1]));

        if (std::isalpha(c1) && std::isalpha(c2)) {
            total_transitions++;
            if ((c1 == 'q' && c2 != 'u') ||
                (c1 == 'x' && c2 == 'j') ||
                (c1 == 'z' && c2 == 'q') ||
                (c1 == 'j' && c2 == 'x') ||
                (c1 == 'v' && c2 == 'k') ||
                (c1 == 'k' && c2 == 'x')) {
                rare_transitions++;
            }
        }
    }

    if (total_transitions == 0) return 0.0;
    return static_cast<double>(rare_transitions) / static_cast<double>(total_transitions);
}

}
